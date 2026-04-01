"""
LangGraph workflow orchestration.
Defines the multi-agent collaborative workflow with feedback loops.
"""

from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from app.agents.creator import Creator
from app.agents.critic import Critic
from app.agents.radical import Radical
from app.agents.synthesizer import Synthesizer
from app.agents.judge import Judge
from app.schemas.state_schema import WorkflowState, IterationFeedback
from app.memory.vector_store import MemoryStore
from app.metrics.metrics_engine import MetricsEngine


class WorkflowOrchestrator:
    """Orchestrates the multi-agent workflow"""
    
    def __init__(self, custom_model_mapping: Optional[Dict[str, str]] = None):
        self.custom_model_mapping = custom_model_mapping
        
        # Initialize agents
        self.creator = Creator(custom_model_mapping)
        self.critic = Critic(custom_model_mapping)
        self.radical = Radical(custom_model_mapping)
        self.synthesizer = Synthesizer(custom_model_mapping)
        self.judge = Judge(custom_model_mapping)
        
        # Initialize memory
        self.memory = MemoryStore()
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("creator", self._creator_node)
        workflow.add_node("critic", self._critic_node)
        workflow.add_node("radical", self._radical_node)
        workflow.add_node("synthesizer", self._synthesizer_node)
        workflow.add_node("judge", self._judge_node)
        workflow.add_node("iterate_decision", self._iterate_decision_node)
        
        # Add edges
        workflow.add_edge("creator", "critic")
        workflow.add_edge("critic", "radical")
        workflow.add_edge("radical", "synthesizer")
        workflow.add_edge("synthesizer", "judge")
        workflow.add_edge("judge", "iterate_decision")
        
        # Conditional edge from iterate_decision
        workflow.add_conditional_edges(
            "iterate_decision",
            self._should_iterate,
            {
                "iterate": "creator",
                "done": END,
            },
        )
        
        # Set entry point
        workflow.set_entry_point("creator")
        
        return workflow.compile()
    
    async def _creator_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Creator node"""
        feedback = state.feedback.improvement_suggestions if state.feedback else []
        
        output = await self.creator.execute({
            "prompt": state.current_idea or state.ideas[0] if state.ideas else "",
            "previous_feedback": feedback,
            "iteration": state.iteration,
        })
        
        state.creator_output = output
        state.ideas.append(output.content)
        state.current_idea = output.content
        state.total_tokens += output.token_count
        
        return {"state": state}
    
    async def _critic_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Critic node"""
        output = await self.critic.execute({
            "ideas": [state.current_idea],
            "context": "",
        })
        
        state.critic_output = [output]
        state.critiques.append(output.content)
        state.total_tokens += output.token_count
        
        return {"state": state}
    
    async def _radical_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Radical node"""
        critiques = state.critiques[-1:] if state.critiques else []
        
        output = await self.radical.execute({
            "ideas": [state.current_idea],
            "critiques": critiques,
            "context": "",
        })
        
        state.radical_output = output
        state.radical_ideas.append(output.content)
        state.total_tokens += output.token_count
        
        return {"state": state}
    
    async def _synthesizer_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Synthesizer node"""
        critiques = state.critiques[-1:] if state.critiques else []
        radical = state.radical_ideas[-1:] if state.radical_ideas else []
        
        output = await self.synthesizer.execute({
            "original_idea": state.current_idea,
            "critiques": critiques,
            "radical_suggestions": radical,
            "context": "",
        })
        
        state.synthesizer_output = output
        state.refined_output = output.content
        state.current_idea = output.content
        state.total_tokens += output.token_count
        
        return {"state": state}
    
    async def _judge_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Judge node"""
        output = await self.judge.execute({
            "idea": state.current_idea,
            "context": "",
            "iteration": state.iteration,
            "max_iterations": state.max_iterations,
        })
        
        state.judge_output = output
        state.total_tokens += output.token_count
        state.iteration += 1
        
        # Parse feedback from reasoning
        import json
        try:
            feedback_dict = json.loads(output.reasoning)
            state.feedback = IterationFeedback(**feedback_dict)
        except:
            state.feedback = IterationFeedback()
        
        state.scores["judge"] = 0.85  # Judge confidence
        
        return {"state": state}
    
    def _iterate_decision_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Decision node for iteration"""
        return {"state": state}
    
    def _should_iterate(self, state: WorkflowState) -> str:
        """Determine if workflow should iterate"""
        if not state.feedback:
            return "done"
        
        should_iterate = (
            state.feedback.should_iterate
            and state.iteration < state.max_iterations
        )
        
        return "iterate" if should_iterate else "done"
    
    async def run(
        self,
        prompt: str,
        max_iterations: int = 5,
        model_mapping: Optional[Dict[str, str]] = None,
    ) -> WorkflowState:
        """Run the complete workflow"""
        
        # Initialize state
        state = WorkflowState(
            ideas=[prompt],
            current_idea=prompt,
            iteration=0,
            max_iterations=max_iterations,
            request_id="flow_" + str(hash(prompt))[:8],
            model_mapping=model_mapping or {},
        )
        
        # Initialize metrics
        metrics = MetricsEngine(state.request_id)
        
        # Run workflow
        try:
            result = await self.graph.ainvoke({"state": state})
            final_state = result.get("state", state)
        except Exception as e:
            print(f"Workflow error: {e}")
            final_state = state
        
        # Finalize
        final_state.final_output = final_state.current_idea
        metrics.finalize_metrics(final_state.iteration, final_state.total_tokens)
        
        return final_state
