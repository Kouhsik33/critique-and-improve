"""
Execution Service - Manages workflow execution with streaming and metrics.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, AsyncIterator
from datetime import datetime

from app.graph.workflow import WorkflowOrchestrator
from app.schemas.state_schema import WorkflowState, RunRequest
from app.streaming.redis_streaming import RedisStreamManager
from app.metrics.metrics_engine import MetricsEngine
from app.db.postgres import DatabaseManager
from app.memory.vector_store import MemoryStore


class ExecutionService:
    """Service for executing workflows with full streaming and metrics"""
    
    def __init__(self):
        self.redis = RedisStreamManager()
        self.orchestrator = None
        self.metrics_engine = None
        self.memory = MemoryStore()
        DatabaseManager.init()
    
    async def execute(
        self,
        request: RunRequest,
        stream_callback: Optional[callable] = None,
        request_id: Optional[str] = None,
    ) -> WorkflowState:
        """
        Execute a complete workflow with streaming.
        
        Args:
            request: RunRequest with prompt and parameters
            stream_callback: Optional callback for streaming events
            request_id: Optional request ID (will be generated if not provided)
            
        Returns:
            Final workflow state
        """
        # Initialize tracking
        if not request_id:
            request_id = f"exec_{uuid.uuid4().hex[:12]}"
        self.metrics_engine = MetricsEngine(request_id)
        
        # Log workflow start
        DatabaseManager.log_workflow(
            request_id=request_id,
            initial_prompt=request.prompt,
            metadata={
                "max_iterations": request.max_iterations,
                "temperature": request.temperature,
            },
        )
        
        # Create orchestrator
        self.orchestrator = WorkflowOrchestrator(request.model_mapping)
        
        # Publish start event
        await self.redis.connect()
        await self.redis.publish_agent_action(
            request_id=request_id,
            agent="system",
            action="generate",
            data={"status": "workflow_started", "prompt": request.prompt},
            iteration=0,
        )
        
        try:
            # Run workflow
            state = await self._run_workflow_with_streaming(
                request_id,
                request,
                stream_callback,
            )
            
            # Finalize metrics
            self.metrics_engine.finalize_metrics(state.iteration, state.total_tokens)
            
            # Update database
            DatabaseManager.update_workflow_status(
                request_id=request_id,
                status="completed",
                final_output=state.final_output,
                total_iterations=state.iteration,
                total_tokens=state.total_tokens,
            )
            
            # Publish completion
            metrics_summary = self.metrics_engine.get_summary()
            await self.redis.publish_workflow_complete(
                request_id=request_id,
                final_output=state.final_output,
                total_iterations=state.iteration,
                metrics=metrics_summary,
            )
            
            return state
            
        except Exception as e:
            print(f"Workflow error: {e}")
            DatabaseManager.update_workflow_status(
                request_id=request_id,
                status="failed",
            )
            raise
        finally:
            await self.redis.disconnect()
    
    async def _run_workflow_with_streaming(
        self,
        request_id: str,
        request: RunRequest,
        stream_callback: Optional[callable] = None,
    ) -> WorkflowState:
        """Run workflow with streaming updates"""
        
        # Initialize state
        state = WorkflowState(
            ideas=[request.prompt],
            current_idea=request.prompt,
            iteration=0,
            max_iterations=request.max_iterations,
            request_id=request_id,
            model_mapping=request.model_mapping or {},
        )
        
        # Execute workflow through orchestrator, streaming updates
        input_state = state.model_dump()
        # Defensive: handle accidental nesting or non-dict inputs
        if isinstance(input_state, dict) and "state" in input_state and isinstance(input_state["state"], WorkflowState):
            input_state = input_state["state"].model_dump()
        async for output in self.orchestrator.graph.astream(input_state):
            for node_name, node_output in output.items():
                if node_name == "__end__":
                    continue
                
                # node_output is a dictionary representing WorkflowState
                if not isinstance(node_output, dict):
                    continue
                    
                # Update our reference to state just to end properly
                current_state = WorkflowState(**node_output)
                state = current_state
                
                # Map node to agent and action
                action_map = {
                    "creator": "generate",
                    "critic": "attack",
                    "radical": "disrupt",
                    "synthesizer": "merge",
                    "judge": "judge"
                }
                
                if node_name in action_map:
                    action = action_map[node_name]
                    
                    # Extract last output based on node
                    agent_output = None
                    last_idea = current_state.current_idea
                    data = {}
                    
                    if node_name == "creator":
                        agent_output = current_state.creator_output
                        data = {
                            "ideas": agent_output.content if agent_output else "Generated",
                            "output": agent_output.content if agent_output else "",
                        }
                    elif node_name == "critic":
                        if current_state.critic_output:
                            agent_output = current_state.critic_output[-1] 
                        data = {
                            "issues_found": len(current_state.critiques),
                            "output": agent_output.content if agent_output else "",
                        }
                    elif node_name == "radical":
                        agent_output = current_state.radical_output
                        data = {
                            "paradigm_shifts": 1, # simplified
                            "output": agent_output.content if agent_output else "",
                        }
                    elif node_name == "synthesizer":
                        agent_output = current_state.synthesizer_output
                        data = {
                            "merge_result": last_idea,
                            "output": agent_output.content if agent_output else "",
                        }
                    elif node_name == "judge":
                        agent_output = current_state.judge_output
                        fitness_score = current_state.scores.get("judge", 0.0)
                        if current_state.feedback:
                            fitness_score = current_state.feedback.overall_score
                            
                        data = {
                            "fitness_score": fitness_score,
                            "should_iterate": current_state.feedback.should_iterate if current_state.feedback else False,
                            "output": agent_output.content if agent_output else "",
                        }
                        
                        # Record metrics for the iteration when judge finishes
                        self.metrics_engine.record_idea_metrics(
                            iteration=current_state.iteration - 1,  # judge increments iteration
                            idea=current_state.current_idea,
                            critiques=current_state.critiques,
                        )
                        
                        if stream_callback:
                            await stream_callback({
                                "iteration": current_state.iteration,
                                "fitness": fitness_score,
                                "status": "iterating" if (current_state.feedback and current_state.feedback.should_iterate) else "completed",
                            })
                    
                    # Record agent metrics if we have output
                    if agent_output:
                        self.metrics_engine.record_agent_output(
                            iteration=current_state.iteration if node_name != "judge" else current_state.iteration - 1,
                            agent=node_name,
                            output=agent_output.content,
                            token_count=agent_output.token_count,
                            feedback_score=0.5,  # generic default
                            action=action
                        )
                    
                    # Publish agent action via redis
                    await self._publish_agent_step(
                        request_id,
                        node_name,
                        action,
                        data,
                        current_state.iteration if node_name != "judge" else current_state.iteration - 1,
                    )
        
        state.final_output = state.current_idea
        
        return state
    
    async def _publish_agent_step(
        self,
        request_id: str,
        agent: str,
        action: str,
        data: Dict[str, Any],
        iteration: int,
    ):
        """Publish a single agent step"""
        await self.redis.publish_agent_action(
            request_id=request_id,
            agent=agent,
            action=action,
            data=data,
            iteration=iteration,
        )
    
    async def get_metrics(self, request_id: str) -> Dict[str, Any]:
        """Retrieve metrics for a completed workflow"""
        return DatabaseManager.get_metrics(request_id)
