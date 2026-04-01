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
    ) -> WorkflowState:
        """
        Execute a complete workflow with streaming.
        
        Args:
            request: RunRequest with prompt and parameters
            stream_callback: Optional callback for streaming events
            
        Returns:
            Final workflow state
        """
        # Initialize tracking
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
        
        # Simulated workflow loop (simplified for demonstration)
        iteration = 0
        while iteration < request.max_iterations:
            state.iteration = iteration
            
            # Creator generates ideas
            await self._publish_agent_step(
                request_id,
                "creator",
                "generate",
                {"ideas": "Generated from prompt"},
                iteration,
            )
            await asyncio.sleep(0.1)
            
            # Critic evaluates
            await self._publish_agent_step(
                request_id,
                "critic",
                "attack",
                {"issues_found": 2},
                iteration,
            )
            await asyncio.sleep(0.1)
            
            # Radical disrupts
            await self._publish_agent_step(
                request_id,
                "radical",
                "disrupt",
                {"paradigm_shifts": 1},
                iteration,
            )
            await asyncio.sleep(0.1)
            
            # Synthesizer merges
            await self._publish_agent_step(
                request_id,
                "synthesizer",
                "merge",
                {"refinements": 2},
                iteration,
            )
            await asyncio.sleep(0.1)
            
            # Judge evaluates
            fitness_score = 0.5 + (iteration * 0.1)  # Improve each iteration
            should_continue = fitness_score < 0.8 and iteration < (request.max_iterations - 1)
            
            await self._publish_agent_step(
                request_id,
                "judge",
                "judge",
                {
                    "fitness_score": fitness_score,
                    "should_iterate": should_continue,
                },
                iteration,
            )
            
            # Record metrics
            self.metrics_engine.record_idea_metrics(
                iteration=iteration,
                idea=state.current_idea,
                critiques=[],
            )
            
            if stream_callback:
                await stream_callback({
                    "iteration": iteration,
                    "fitness": fitness_score,
                    "status": "iterating" if should_continue else "completed",
                })
            
            iteration += 1
            
            if not should_continue:
                break
        
        state.iteration = iteration
        state.final_output = f"Refined idea after {iteration} iterations"
        state.total_tokens = iteration * 1000  # Rough estimate
        
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
