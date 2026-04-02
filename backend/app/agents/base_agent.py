"""
Base agent class defining common interface for all agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.base_language import BaseLanguageModel

from app.config.llm_config import LLMFactory
from app.schemas.state_schema import AgentOutput, AgentAction


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(
        self,
        name: str,
        llm: Optional[BaseLanguageModel] = None,
        custom_model_mapping: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.custom_model_mapping = custom_model_mapping
        self.llm = llm or LLMFactory.get_agent_llm(name, custom_model_mapping)
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        **kwargs,
    ) -> AgentOutput:
        """Execute the agent's task"""
        raise NotImplementedError
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the agent"""
        raise NotImplementedError
    
    async def _call_llm(
        self,
        system_prompt: str,
        user_message: str,
        json_mode: bool = False,
    ) -> str:
        """Call LLM with structured prompting"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
        
        response = await self.llm.ainvoke(messages)
        content = response.content
        
        # Try to parse JSON if requested
        if json_mode:
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                json.loads(content)  # Validate
            except (json.JSONDecodeError, IndexError):
                pass  # Return as-is if not valid JSON
        
        return content
    
    def _extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from response"""
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            return json.loads(response)
        except (json.JSONDecodeError, IndexError):
            return None
