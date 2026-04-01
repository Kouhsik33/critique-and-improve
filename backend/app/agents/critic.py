"""
Critic Agent - Evaluates ideas for flaws and weaknesses.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.schemas.state_schema import AgentOutput, AgentAction


class Critic(BaseAgent):
    """
    Critic agent analyzes ideas for weaknesses, inconsistencies, and flaws.
    Provides constructive criticism to improve ideas.
    """
    
    def __init__(self, custom_model_mapping: Optional[Dict[str, str]] = None):
        super().__init__("critic", custom_model_mapping=custom_model_mapping)
    
    def _create_system_prompt(self) -> str:
        return """You are a critical evaluator and technical expert. Your role is to identify 
weaknesses, potential problems, and areas for improvement in ideas.

Core principles:
- Look for logical flaws and inconsistencies
- Consider practical constraints and challenges
- Identify missing components or oversights
- Provide specific, actionable critique
- Be constructive but rigorous

When critiquing ideas, consider:
1. Technical feasibility
2. Resource requirements
3. Market viability
4. Implementation challenges
5. Unintended consequences
6. Missing components

Format your response as structured JSON."""
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        **kwargs,
    ) -> AgentOutput:
        """
        Critique ideas and identify weaknesses.
        
        Input:
        {
            'ideas': list of idea strings,
            'context': optional context about the problem,
        }
        """
        ideas = input_data.get("ideas", [])
        context = input_data.get("context", "")
        
        # Build user message
        ideas_text = "\n".join(f"- {idea}" for idea in ideas)
        
        user_message = f"""Critique the following ideas:

{ideas_text}"""
        
        if context:
            user_message += f"\n\nContext: {context}"
        
        user_message += """\n\nProvide your critique as JSON:
{
    "critiques": [
        {
            "idea_index": 0,
            "issues": [
                {
                    "category": "feasibility|clarity|logic|resources|viability|other",
                    "severity": "low|medium|high",
                    "description": "Specific issue",
                    "impact": "How this affects the idea"
                }
            ]
        }
    ],
    "overall_assessment": "General observations about the idea set",
    "reasoning": "Your analytical process"
}"""
        
        system_prompt = self._create_system_prompt()
        
        response = await self._call_llm(system_prompt, user_message, json_mode=True)
        
        # Extract JSON
        parsed = self._extract_json(response)
        
        if parsed:
            critiques = parsed.get("critiques", [])
            reasoning = parsed.get("reasoning", "")
            content = f"Identified {len(critiques)} areas for improvement"
        else:
            content = response
            reasoning = ""
        
        # Estimate tokens
        token_count = len(response.split()) // 4 + sum(len(idea.split()) for idea in ideas) // 4
        
        return AgentOutput(
            agent="critic",
            action=AgentAction.ATTACK,
            content=content,
            reasoning=reasoning,
            timestamp=datetime.utcnow(),
            token_count=token_count,
            confidence=0.6,
        )
