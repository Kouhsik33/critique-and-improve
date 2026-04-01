"""
PostgreSQL database integration.
Stores metrics, logs, and workflow state.
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from pydantic import BaseSettings

Base = declarative_base()


# Models
class WorkflowLog(Base):
    """Logs for workflow executions"""
    __tablename__ = "workflow_logs"
    
    id = Column(String, primary_key=True)
    request_id = Column(String, index=True)
    iteration = Column(Integer)
    initial_prompt = Column(Text)
    final_output = Column(Text)
    status = Column(String)  # "running", "completed", "failed"
    total_iterations = Column(Integer)
    total_tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, default={})


class AgentMetric(Base):
    """Per-agent metrics"""
    __tablename__ = "agent_metrics"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, index=True)
    agent = Column(String, index=True)
    iteration = Column(Integer)
    action = Column(String)
    token_count = Column(Integer, default=0)
    quality_score = Column(Float, default=0.0)
    diversity_score = Column(Float, nullable=True)
    confidence = Column(Float, default=0.5)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    output = Column(Text, nullable=True)
    metadata = Column(JSON, default={})


class IdeaMetric(Base):
    """Per-idea metrics"""
    __tablename__ = "idea_metrics"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, index=True)
    iteration = Column(Integer)
    idea = Column(Text)
    novelty = Column(Float, default=0.0)
    feasibility = Column(Float, default=0.0)
    clarity = Column(Float, default=0.0)
    impact = Column(Float, default=0.0)
    fitness_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSON, default={})


class SystemMetric(Base):
    """System-level metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, index=True)
    iteration_count = Column(Integer, default=0)
    convergence_speed = Column(Float, nullable=True)
    total_token_usage = Column(Integer, default=0)
    conflict_intensity = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSON, default={})


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", 5432))
    db_name: str = os.getenv("DB_NAME", "ai_agents")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "postgres")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", 10))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", 20))
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class DatabaseManager:
    """Manager for PostgreSQL connections and operations"""
    
    _engine = None
    _SessionLocal = None
    _settings = None
    
    @classmethod
    def init(cls, settings: Optional[DatabaseSettings] = None):
        """Initialize database connection"""
        if settings:
            cls._settings = settings
        else:
            cls._settings = DatabaseSettings()
        
        url = (
            f"postgresql://"
            f"{cls._settings.db_user}:{cls._settings.db_password}"
            f"@{cls._settings.db_host}:{cls._settings.db_port}"
            f"/{cls._settings.db_name}"
        )
        
        cls._engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=cls._settings.db_pool_size,
            max_overflow=cls._settings.db_max_overflow,
            echo=False,
        )
        
        cls._SessionLocal = sessionmaker(bind=cls._engine)
        cls.create_tables()
    
    @classmethod
    def create_tables(cls):
        """Create all tables"""
        Base.metadata.create_all(cls._engine)
    
    @classmethod
    def get_session(cls) -> Session:
        """Get a database session"""
        if cls._SessionLocal is None:
            cls.init()
        return cls._SessionLocal()
    
    @classmethod
    def log_workflow(
        cls,
        request_id: str,
        initial_prompt: str,
        metadata: Dict[str, Any] = None
    ) -> WorkflowLog:
        """Log a new workflow execution"""
        session = cls.get_session()
        try:
            log = WorkflowLog(
                id=request_id,
                request_id=request_id,
                initial_prompt=initial_prompt,
                status="running",
                metadata=metadata or {},
            )
            session.add(log)
            session.commit()
            return log
        finally:
            session.close()
    
    @classmethod
    def update_workflow_status(
        cls,
        request_id: str,
        status: str,
        final_output: str = "",
        total_iterations: int = 0,
        total_tokens: int = 0,
    ):
        """Update workflow status"""
        session = cls.get_session()
        try:
            workflow = session.query(WorkflowLog).filter_by(request_id=request_id).first()
            if workflow:
                workflow.status = status
                workflow.final_output = final_output
                workflow.total_iterations = total_iterations
                workflow.total_tokens = total_tokens
                workflow.completed_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()
    
    @classmethod
    def log_agent_metric(
        cls,
        workflow_id: str,
        agent: str,
        iteration: int,
        action: str,
        token_count: int = 0,
        quality_score: float = 0.0,
        confidence: float = 0.5,
        output: str = "",
        metadata: Dict[str, Any] = None,
    ) -> AgentMetric:
        """Log agent metrics"""
        import uuid
        session = cls.get_session()
        try:
            metric = AgentMetric(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                agent=agent,
                iteration=iteration,
                action=action,
                token_count=token_count,
                quality_score=quality_score,
                confidence=confidence,
                output=output,
                metadata=metadata or {},
            )
            session.add(metric)
            session.commit()
            return metric
        finally:
            session.close()
    
    @classmethod
    def log_idea_metric(
        cls,
        workflow_id: str,
        iteration: int,
        idea: str,
        novelty: float = 0.0,
        feasibility: float = 0.0,
        clarity: float = 0.0,
        impact: float = 0.0,
        metadata: Dict[str, Any] = None,
    ) -> IdeaMetric:
        """Log idea metrics"""
        import uuid
        session = cls.get_session()
        try:
            fitness_score = (novelty + feasibility + clarity + impact) / 4
            metric = IdeaMetric(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                iteration=iteration,
                idea=idea,
                novelty=novelty,
                feasibility=feasibility,
                clarity=clarity,
                impact=impact,
                fitness_score=fitness_score,
                metadata=metadata or {},
            )
            session.add(metric)
            session.commit()
            return metric
        finally:
            session.close()
    
    @classmethod
    def log_system_metric(
        cls,
        workflow_id: str,
        iteration_count: int = 0,
        total_token_usage: int = 0,
        conflict_intensity: float = 0.0,
        metadata: Dict[str, Any] = None,
    ) -> SystemMetric:
        """Log system-level metrics"""
        import uuid
        session = cls.get_session()
        try:
            metric = SystemMetric(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                iteration_count=iteration_count,
                total_token_usage=total_token_usage,
                conflict_intensity=conflict_intensity,
                metadata=metadata or {},
            )
            session.add(metric)
            session.commit()
            return metric
        finally:
            session.close()
    
    @classmethod
    def get_metrics(cls, workflow_id: str) -> Dict[str, Any]:
        """Retrieve all metrics for a workflow"""
        session = cls.get_session()
        try:
            agent_metrics = session.query(AgentMetric).filter_by(workflow_id=workflow_id).all()
            idea_metrics = session.query(IdeaMetric).filter_by(workflow_id=workflow_id).all()
            system_metrics = session.query(SystemMetric).filter_by(workflow_id=workflow_id).all()
            
            return {
                "agent_metrics": [
                    {
                        "agent": m.agent,
                        "iteration": m.iteration,
                        "action": m.action,
                        "token_count": m.token_count,
                        "quality_score": m.quality_score,
                        "confidence": m.confidence,
                    }
                    for m in agent_metrics
                ],
                "idea_metrics": [
                    {
                        "iteration": m.iteration,
                        "novelty": m.novelty,
                        "feasibility": m.feasibility,
                        "clarity": m.clarity,
                        "impact": m.impact,
                        "fitness_score": m.fitness_score,
                    }
                    for m in idea_metrics
                ],
                "system_metrics": [
                    {
                        "iteration_count": m.iteration_count,
                        "total_token_usage": m.total_token_usage,
                        "conflict_intensity": m.conflict_intensity,
                    }
                    for m in system_metrics
                ],
            }
        finally:
            session.close()
