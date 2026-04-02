"""
State schema for the multi-agent workflow.
Defines the structure of data flowing through the system.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class AgentAction(str, Enum):
    """Actions agents can perform"""
    GENERATE = "generate"
    ATTACK = "attack"
    DISRUPT = "disrupt"
    MERGE = "merge"
    JUDGE = "judge"


class IterationIssue(BaseModel):
    """Represents a single issue found by critics"""
    category: str  # e.g., "feasibility", "clarity", "logic"
    severity: float  # 0-1 scale
    description: str
    impact: str


class IterationFeedback(BaseModel):
    """Structured feedback from the judge"""
    issues: List[IterationIssue] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    radical_directions: List[str] = Field(default_factory=list)
    partial_refinements: List[str] = Field(default_factory=list)
    overall_score: float = 0.0
    should_iterate: bool = True


class AgentOutput(BaseModel):
    """Output from a single agent"""
    agent: str
    action: AgentAction
    content: str
    reasoning: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    token_count: int = 0
    confidence: float = 0.5


class WorkflowState(BaseModel):
    """Complete state for a workflow iteration"""
    model_config = ConfigDict(protected_namespaces=())
    # Ideas and outputs
    ideas: List[str] = Field(default_factory=list)
    current_idea: str = ""
    
    # Agent outputs
    creator_output: Optional[AgentOutput] = None
    critic_output: Optional[List[AgentOutput]] = Field(default_factory=list)
    radical_output: Optional[AgentOutput] = None
    synthesizer_output: Optional[AgentOutput] = None
    judge_output: Optional[AgentOutput] = None
    
    # Critiques and feedback
    critiques: List[str] = Field(default_factory=list)
    radical_ideas: List[str] = Field(default_factory=list)
    refined_output: str = ""
    
    # Scoring and feedback
    scores: Dict[str, float] = Field(default_factory=dict)
    feedback: Optional[IterationFeedback] = None
    
    # Iteration tracking
    iteration: int = 0
    max_iterations: int = 5
    final_output: str = ""
    
    # Metadata
    request_id: str = ""
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_tokens: int = 0
    model_mapping: Dict[str, str] = Field(default_factory=dict)


class StreamEvent(BaseModel):
    """Event streamed to clients via Redis/WebSocket"""
    type: str  # "agent_action", "feedback", "iteration_complete", "workflow_complete"
    agent: str
    action: AgentAction
    data: Dict[str, Any]
    iteration: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = ""


class RunRequest(BaseModel):
    """API request to run the workflow"""
    model_config = ConfigDict(protected_namespaces=())
    prompt: str
    max_iterations: int = 5
    model_mapping: Optional[Dict[str, str]] = None
    temperature: float = 0.7
    include_reasoning: bool = True


class MetricSnapshot(BaseModel):
    """Snapshot of metrics at a point in time"""
    iteration: int
    agent: str
    token_count: int
    quality_score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    diversity_score: Optional[float] = None
    confidence: Optional[float] = None
