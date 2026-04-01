"""
Synthesizer Agent - Integrates feedback and refines ideas.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.schemas.state_schema import AgentOutput, AgentAction


class Synthesizer(BaseAgent):
    """
    Synthesizer agent integrates critiques, radical ideas, and improvements
    into a refined, cohesive solution.
    """
    
    def __init__(self, custom_model_mapping: Optional[Dict[str, str]] = None):
        super().__init__("synthesizer", custom_model_mapping=custom_model_mapping)
    
    def _create_system_prompt(self) -> str:
        return """You are a master synthesizer and integrator. Your role is to combine 
diverse perspectives into a coherent, improved solution.

Core principles:
- Balance creativity with practicality
- Integrate legitimate critiques
- Incorporate valuable radical ideas
- Create a robust, well-reasoned solution
- Make trade-offs explicit
- Maintain coherence in the refined idea

When synthesizing:
1. Acknowledge key critiques and address them
2. Identify valuable radical suggestions
3. Create an integrated solution
4. Explain the reasoning and trade-offs
5. Highlight improvements over original

Format your response as structured JSON."""
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        **kwargs,
    ) -> AgentOutput:
        """
        Synthesize feedback and create refined idea.
        
        Input:
        {
            'original_idea': str,
            'critiques': list of critique dicts with issues,
            'radical_suggestions': list of radical ideas,
            'context': problem context,
        }
        """
        original_idea = input_data.get("original_idea", "")
        critiques = input_data.get("critiques", [])
        radical_suggestions = input_data.get("radical_suggestions", [])
        context = input_data.get("context", "")
        
        # Build user message
        user_message = f"""Original idea: {original_idea}"""
        
        if critiques:
            user_message += "\n\nKey critiques:\n"
            if isinstance(critiques[0], dict):
                for c in critiques:
                    user_message += f"- {c.get('category', 'issue')}: {c.get('description', '')}\n"
            else:
                for c in critiques:
                    user_message += f"- {c}\n"
        
        if radical_suggestions:
            user_message += "\n\nRadical suggestions:\n"
            for s in radical_suggestions:
                user_message += f"- {s}\n"
        
        if context:
            user_message += f"\n\nContext: {context}"
        
        user_message += """\n\nSynthesize a refined idea that:
1. Addresses legitimate critiques
2. Incorporates valuable radical elements
3. Maintains feasibility and coherence
4. Improves over the original

Provide your response as JSON:
{
    "refined_idea": "Detailed description of improved idea",
    "addressed_issues": [
        {
            "issue": "Original criticism",
            "resolution": "How it's addressed"
        }
    ],
    "incorporated_radical_elements": [
        "Radical element 1 and how it's integrated",
        "Radical element 2 and how it's integrated"
    ],
    "key_improvements": [
        "Improvement 1",
        "Improvement 2",
        "Improvement 3"
    ],
    "trade_offs": [
        {
            "trade_off": "What was traded",
            "rationale": "Why this trade-off"
        }
    ],
    "overall_score": 0.7,
    "reasoning": "Synthesis process and rationale"
}"""
        
        system_prompt = self._create_system_prompt()
        
        response = await self._call_llm(system_prompt, user_message, json_mode=True)
        
        # Extract JSON
        parsed = self._extract_json(response)
        
        if parsed:
            refined_idea = parsed.get("refined_idea", "")
            improvements = parsed.get("key_improvements", [])
            reasoning = parsed.get("reasoning", "")
            content = refined_idea if refined_idea else response
        else:
            content = response
            reasoning = ""
        
        # Estimate tokens
        token_count = len(response.split()) // 4 + len(original_idea.split()) // 4
        
        return AgentOutput(
            agent="synthesizer",
            action=AgentAction.MERGE,
            content=content,
            reasoning=reasoning,
            timestamp=datetime.utcnow(),
            token_count=token_count,
            confidence=0.7,
        )
