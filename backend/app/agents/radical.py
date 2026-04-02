"""
Radical Agent - Challenges assumptions and explores extreme alternatives.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.schemas.state_schema import AgentOutput, AgentAction


class Radical(BaseAgent):
    """
    Radical agent challenges fundamental assumptions and proposes 
    extreme or unconventional alternatives.
    """
    
    def __init__(self, custom_model_mapping: Optional[Dict[str, str]] = None):
        super().__init__("radical", custom_model_mapping=custom_model_mapping)
    
    def _create_system_prompt(self) -> str:
        return """You are a revolutionary thinker who challenges fundamental assumptions. 
Your role is to propose radical alternatives and disrupt conventional thinking.

Core principles:
- Question basic assumptions
- Propose extreme or unconventional approaches
- Explore "what if we inverted this?" scenarios
- Consider paradigm-shifting solutions
- Be provocative and thought-provoking

When disrupting ideas:
1. Identify core underlying assumptions
2. Invert or challenge each assumption
3. Propose 2-3 radical alternatives
4. Explain why conventional thinking holds people back
5. Highlight potential breakthroughs

Format your response as structured JSON."""
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        **kwargs,
    ) -> AgentOutput:
        """
        Challenge assumptions and propose radical alternatives.
        
        Input:
        {
            'ideas': list of current ideas,
            'critiques': list of identified weaknesses,
            'context': problem context,
        }
        """
        ideas = input_data.get("ideas", [])
        critiques = input_data.get("critiques", [])
        context = input_data.get("context", "")
        
        # Build user message
        ideas_text = "\n".join(f"- {idea}" for idea in ideas)
        critiques_text = "\n".join(f"- {c}" for c in critiques) if critiques else "None"
        
        user_message = f"""Current ideas:
{ideas_text}

Current critiques:
{critiques_text}"""
        
        if context:
            user_message += f"\n\nProblem context: {context}"
        
        user_message += """\n\nChallenge these ideas radically:
1. What foundational assumptions do these ideas make?
2. What if we inverted or eliminated these assumptions?
3. What radical alternatives would emerge?

Provide your response as JSON:
{
    "fundamental_assumptions": [
        {
            "assumption": "What is being assumed",
            "challenge": "Alternative assumption",
            "radical_idea": "Idea that emerges from the challenge"
        }
    ],
    "paradigm_shifts": [
        {
            "shift": "From X to Y",
            "implications": "What changes",
            "radical_direction": "New possibility"
        }
    ],
    "breakthrough_insights": [
        "Insight 1",
        "Insight 2"
    ],
    "reasoning": "Your disruptive thinking process"
}"""
        
        system_prompt = self._create_system_prompt()
        
        response = await self._call_llm(system_prompt, user_message, json_mode=True)
        
        # Extract JSON
        parsed = self._extract_json(response)
        
        if parsed:
            breakthrough_insights = parsed.get("breakthrough_insights", [])
            reasoning = parsed.get("reasoning", "")
            content = " | ".join(breakthrough_insights) if breakthrough_insights else response
        else:
            content = response
            reasoning = ""
        
        # Estimate tokens
        token_count = len(response.split()) // 4 + sum(len(idea.split()) for idea in ideas) // 4
        
        return AgentOutput(
            agent="radical",
            action=AgentAction.DISRUPT,
            content=content,
            reasoning=reasoning,
            timestamp=datetime.utcnow(),
            token_count=token_count,
            confidence=0.5,
        )
