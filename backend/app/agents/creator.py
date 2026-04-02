"""
Creator Agent - Generates novel ideas and solutions.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from app.agents.base_agent import BaseAgent
from app.schemas.state_schema import AgentOutput, AgentAction


class Creator(BaseAgent):
    """
    Creator agent generates original ideas and solutions.
    Focuses on creativity, novelty, and possibility.
    """
    
    def __init__(self, custom_model_mapping: Optional[Dict[str, str]] = None):
        super().__init__("creator", custom_model_mapping=custom_model_mapping)
    
    def _create_system_prompt(self) -> str:
        return """You are a creative entrepreneur and ideation expert. Your role is to generate novel, 
original ideas that expand possibilities. 

Core principles:
- Think outside conventional boundaries
- Generate multiple diverse angles on the problem
- Embrace unconventional approaches
- Focus on feasibility second, novelty first
- Be bold and imaginative

When generating ideas:
1. Start with the core problem/opportunity
2. Generate 2-3 distinct solution directions
3. For each direction, explain the key innovation
4. Note why this approach is novel

Format your response as structured JSON."""
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        **kwargs,
    ) -> AgentOutput:
        """
        Generate novel ideas based on input prompt.
        
        Input:
        {
            'prompt': str,
            'previous_feedback': optional list of feedback from judge,
            'iteration': int,
        }
        """
        prompt = input_data.get("prompt", "")
        previous_feedback = input_data.get("previous_feedback", [])
        iteration = input_data.get("iteration", 0)
        
        # Build user message
        user_message = f"""Generate novel ideas for: {prompt}"""
        
        if previous_feedback and iteration > 0:
            user_message += "\n\nPrevious feedback to address:\n"
            for feedback in previous_feedback:
                user_message += f"- {feedback}\n"
            user_message += "\nCreate improved ideas that address these suggestions."
        
        user_message += """\n\nProvide your response as JSON:
{
    "ideas": [
        {
            "title": "Brief title",
            "description": "Detailed description",
            "novelty_justification": "Why this is novel",
            "key_innovation": "Core innovative element"
        }
    ],
    "reasoning": "Your overall creative thinking process",
    "diversity": "How these ideas approach the problem differently"
}"""
        
        system_prompt = self._create_system_prompt()
        
        response = await self._call_llm(system_prompt, user_message, json_mode=True)
        
        # Extract JSON
        parsed = self._extract_json(response)
        
        if parsed:
            ideas = [idea.get("description", "") for idea in parsed.get("ideas", [])]
            reasoning = parsed.get("reasoning", "")
            content = " | ".join(ideas) if ideas else response
        else:
            content = response
            reasoning = ""
        
        # Estimate tokens (rough approximation)
        token_count = len(response.split()) // 4 + len(prompt.split()) // 4
        
        return AgentOutput(
            agent="creator",
            action=AgentAction.GENERATE,
            content=content,
            reasoning=reasoning,
            timestamp=datetime.utcnow(),
            token_count=token_count,
            confidence=0.7,
        )
