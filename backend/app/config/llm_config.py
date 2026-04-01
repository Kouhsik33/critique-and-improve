"""
LLM Configuration module.
Allows swappable LLM models per agent without code changes.
"""

import os
from typing import Dict, Optional
from pydantic_settings import BaseSettings
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.base_language import BaseLanguageModel


class LLMSettings(BaseSettings):
    """LLM configuration from environment"""
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Anthropic
    anthropic_api_key: Optional[str] = None
    
    # Google
    google_api_key: Optional[str] = None
    
    # Default model preferences
    creator_model: str = "gpt-4-turbo"
    critic_model: str = "gpt-4-turbo"
    radical_model: str = "gpt-4"
    synthesizer_model: str = "gpt-3.5-turbo"
    judge_model: str = "gpt-4"
    
    # Temperature settings
    creator_temperature: float = 0.8
    critic_temperature: float = 0.5
    radical_temperature: float = 0.9
    synthesizer_temperature: float = 0.6
    judge_temperature: float = 0.3
    
    # Model max tokens
    max_tokens: int = 2000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class LLMFactory:
    """Factory for creating LLM instances"""
    
    _settings: LLMSettings = None
    _llm_cache: Dict[str, BaseLanguageModel] = {}
    
    @classmethod
    def init_settings(cls, settings: Optional[LLMSettings] = None):
        """Initialize settings"""
        if settings:
            cls._settings = settings
        else:
            cls._settings = LLMSettings()
    
    @classmethod
    def get_settings(cls) -> LLMSettings:
        """Get settings"""
        if cls._settings is None:
            cls.init_settings()
        return cls._settings
    
    @classmethod
    def get_llm(cls, model_name: str, temperature: float = 0.7) -> BaseLanguageModel:
        """
        Get or create an LLM instance.
        
        Args:
            model_name: Model identifier (e.g., "gpt-4-turbo", "claude-3", "gemini-pro")
            temperature: Model temperature
            
        Returns:
            BaseLanguageModel instance
        """
        cache_key = f"{model_name}_{temperature}"
        
        if cache_key in cls._llm_cache:
            return cls._llm_cache[cache_key]
        
        settings = cls.get_settings()
        llm = None
        
        if model_name.startswith("gpt") or model_name.startswith("text-davinci"):
            # OpenAI models
            llm = ChatOpenAI(
                model_name=model_name,
                temperature=temperature,
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                max_tokens=settings.max_tokens,
            )
        elif model_name.startswith("claude"):
            # Anthropic models
            llm = ChatAnthropic(
                model=model_name,
                temperature=temperature,
                api_key=settings.anthropic_api_key,
                max_tokens=settings.max_tokens,
            )
        elif model_name.startswith("gemini"):
            # Google Generative AI models
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                google_api_key=settings.google_api_key,
            )
        else:
            raise ValueError(f"Unsupported model: {model_name}")
        
        cls._llm_cache[cache_key] = llm
        return llm
    
    @classmethod
    def get_agent_llm(
        cls,
        agent_name: str,
        custom_model_mapping: Optional[Dict[str, str]] = None
    ) -> BaseLanguageModel:
        """
        Get LLM for a specific agent.
        
        Args:
            agent_name: Name of the agent (creator, critic, radical, synthesizer, judge)
            custom_model_mapping: Custom model mapping to override defaults
            
        Returns:
            BaseLanguageModel instance
        """
        settings = cls.get_settings()
        
        # Determine model name
        if custom_model_mapping and agent_name in custom_model_mapping:
            model_name = custom_model_mapping[agent_name]
        else:
            model_attr = f"{agent_name}_model"
            model_name = getattr(settings, model_attr, "gpt-3.5-turbo")
        
        # Determine temperature
        temp_attr = f"{agent_name}_temperature"
        temperature = getattr(settings, temp_attr, 0.7)
        
        return cls.get_llm(model_name, temperature)
    
    @classmethod
    def update_model_mapping(cls, agent_name: str, model_name: str):
        """Dynamically update model for an agent"""
        settings = cls.get_settings()
        model_attr = f"{agent_name}_model"
        setattr(settings, model_attr, model_name)
        cls._llm_cache.clear()  # Clear cache to pick up new model
