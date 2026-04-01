"""
Judge Agent - Evaluates and decides whether to accept or iterate.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.schemas.state_schema import AgentOutput, AgentAction, IterationFeedback, IterationIssue


class Judge(BaseAgent):
    """
    Judge agent determines if the current iteration quality is acceptable,
    or if improvements are needed, and provides specific feedback for iteration.
    """
    
    def __init__(self, custom_model_mapping: Optional[Dict[str, str]] = None):
        super().__init__("judge", custom_model_mapping=custom_model_mapping)
    
    def _create_system_prompt(self) -> str:
        return """You are a wise and decisive judge. Your role is to evaluate the quality 
of ideas and determine if they meet acceptance criteria or need iteration.

Core principles:
- Evaluate based on novelty, feasibility, clarity, and impact
- Make clear accept/reject decisions
- Provide specific, actionable feedback for iteration
- Balance idealism with pragmatism
- Consider both technical and market viability

When judging:
1. Assess quality across multiple dimensions
2. Compare against acceptance criteria
3. Make clear recommendation (accept/iterate)
4. If iterating, provide concrete improvement directions
5. Highlight strengths and weaknesses

Acceptance criteria:
- Novelty score >= 0.6
- Feasibility score >= 0.5
- Clarity score >= 0.6
- Impact score >= 0.5
- Overall fitness >= 0.55

Format your response as structured JSON."""
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        **kwargs,
    ) -> AgentOutput:
        """
        Judge the quality of the synthesized idea.
        
        Input:
        {
            'idea': str,
            'context': str,
            'iteration': int,
            'max_iterations': int,
        }
        """
        idea = input_data.get("idea", "")
        context = input_data.get("context", "")
        iteration = input_data.get("iteration", 0)
        max_iterations = input_data.get("max_iterations", 5)
        
        # Build user message
        user_message = f"""Idea to evaluate:
{idea}"""
        
        if context:
            user_message += f"\n\nProblem context: {context}"
        
        user_message += f"\n\nIteration: {iteration + 1}/{max_iterations}"
        
        user_message += """\n\nProvide your judgment as JSON:
{
    "novelty_score": 0.7,
    "feasibility_score": 0.6,
    "clarity_score": 0.7,
    "impact_score": 0.7,
    "overall_fitness": 0.675,
    "recommendation": "accept|iterate",
    "accept_reasoning": "Why this is good enough" or null,
    "issues": [
        {
            "category": "feasibility|clarity|logic|resources|viability|other",
            "severity": "low|medium|high",
            "description": "Specific issue",
            "impact": "How this affects acceptance"
        }
    ],
    "improvement_suggestions": [
        "Specific suggestion 1",
        "Specific suggestion 2"
    ],
    "radical_directions": [
        "Direction to explore",
        "Direction to explore"
    ],
    "partial_refinements": [
        "Refinement that could help",
        "Refinement that could help"
    ]
}"""
        
        system_prompt = self._create_system_prompt()
        
        response = await self._call_llm(system_prompt, user_message, json_mode=True)
        
        # Extract JSON
        parsed = self._extract_json(response)
        
        if parsed:
            recommendation = parsed.get("recommendation", "iterate").lower()
            overall_fitness = parsed.get("overall_fitness", 0.5)
            
            # Build feedback object
            issues = []
            for issue_data in parsed.get("issues", []):
                issues.append(IterationIssue(
                    category=issue_data.get("category", "general"),
                    severity=self._severity_to_float(issue_data.get("severity", "low")),
                    description=issue_data.get("description", ""),
                    impact=issue_data.get("impact", ""),
                ))
            
            feedback = IterationFeedback(
                issues=issues,
                improvement_suggestions=parsed.get("improvement_suggestions", []),
                radical_directions=parsed.get("radical_directions", []),
                partial_refinements=parsed.get("partial_refinements", []),
                overall_score=overall_fitness,
                should_iterate=recommendation == "iterate",
            )
            
            content = f"Fitness Score: {overall_fitness:.2f} - {'ACCEPT' if recommendation == 'accept' else 'ITERATE'}"
        else:
            feedback = IterationFeedback(
                overall_score=0.5,
                should_iterate=True,
            )
            content = response
        
        # Estimate tokens
        token_count = len(response.split()) // 4 + len(idea.split()) // 4
        
        return AgentOutput(
            agent="judge",
            action=AgentAction.JUDGE,
            content=content,
            reasoning=str(feedback.dict()),
            timestamp=datetime.utcnow(),
            token_count=token_count,
            confidence=0.85,
        )
    
    @staticmethod
    def _severity_to_float(severity: str) -> float:
        """Convert severity string to float"""
        severity_map = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.9,
        }
        return severity_map.get(severity.lower(), 0.5)
