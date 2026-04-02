"""
State Manager for handling workflow state persistence and retrieval.
"""

from typing import Dict, Any, Optional
import json
from datetime import datetime

from app.streaming.redis_streaming import RedisStreamManager
from app.db.postgres import DatabaseManager
from app.schemas.state_schema import WorkflowState


class StateManager:
    """Manages workflow state persistence and retrieval"""
    
    def __init__(self):
        self.redis = RedisStreamManager()
        self.db = DatabaseManager
    
    async def save_state(self, request_id: str, state: WorkflowState):
        """Save workflow state to Redis (for in-progress) and PostgreSQL (for persistence)"""
        await self.redis.connect()
        
        # Serialize state
        state_dict = {
            "request_id": state.request_id,
            "iteration": state.iteration,
            "max_iterations": state.max_iterations,
            "ideas": state.ideas,
            "current_idea": state.current_idea,
            "critiques": state.critiques,
            "radical_ideas": state.radical_ideas,
            "refined_output": state.refined_output,
            "final_output": state.final_output,
            "total_tokens": state.total_tokens,
            "scores": state.scores,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Store in Redis for fast access
        await self.redis.store_state(request_id, state_dict)
    
    async def load_state(self, request_id: str) -> Optional[WorkflowState]:
        """Load workflow state from Redis"""
        await self.redis.connect()
        state_dict = await self.redis.get_state(request_id)
        
        if not state_dict:
            return None
        
        # Reconstruct WorkflowState
        return WorkflowState(**state_dict)
    
    async def save_metrics(self, request_id: str, metrics: Dict[str, Any]):
        """Save metrics to Redis and PostgreSQL"""
        await self.redis.connect()
        await self.redis.store_metrics(request_id, metrics)
    
    async def load_metrics(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Load metrics from Redis"""
        await self.redis.connect()
        return await self.redis.get_metrics(request_id)
    
    def get_workflow_history(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get complete workflow execution history from database"""
        session = self.db.get_session()
        try:
            from app.db.postgres import WorkflowLog
            workflow = session.query(WorkflowLog).filter_by(request_id=request_id).first()
            
            if not workflow:
                return None
            
            return {
                "request_id": workflow.request_id,
                "initial_prompt": workflow.initial_prompt,
                "final_output": workflow.final_output,
                "status": workflow.status,
                "total_iterations": workflow.total_iterations,
                "total_tokens": workflow.total_tokens,
                "created_at": workflow.created_at.isoformat(),
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                "data": workflow.data,
            }
        finally:
            session.close()
    
    def cleanup_old_workflows(self, days: int = 7):
        """Remove old workflows from database (older than specified days)"""
        from datetime import timedelta
        from app.db.postgres import WorkflowLog
        
        session = self.db.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            old_workflows = session.query(WorkflowLog).filter(
                WorkflowLog.created_at < cutoff_date
            ).delete()
            session.commit()
            return old_workflows
        finally:
            session.close()
