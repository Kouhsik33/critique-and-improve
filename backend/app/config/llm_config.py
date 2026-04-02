"""
LLM Configuration module.
Allows swappable LLM models per agent without code changes.
Supports: OpenAI, Anthropic, Google, Ollama, Hugging Face
"""

import os
from typing import Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field, AliasChoices
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.base_language import BaseLanguageModel
import requests


class LLMSettings(BaseSettings):
    """LLM configuration from environment"""
    model_config = ConfigDict(extra="ignore", env_file=".env", case_sensitive=False)
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_base_url: str = "https://api.openai.com/v1"
    openai_fallback_model: Optional[str] = Field(
        default=None, validation_alias="OPENAI_FALLBACK_MODEL"
    )
    
    # Anthropic
    anthropic_api_key: Optional[str] = None
    
    # Google
    google_api_key: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY")
    )
    
    # Ollama (local)
    ollama_base_url: str = "http://localhost:11434/v1"
    
    # Hugging Face - Global fallback
    hf_token: Optional[str] = None
    
    # Per-Agent Hugging Face Configuration
    creator_hf_model: Optional[str] = None
    creator_hf_token: Optional[str] = None
    
    critic_hf_model: Optional[str] = None
    critic_hf_token: Optional[str] = None
    
    radical_hf_model: Optional[str] = None
    radical_hf_token: Optional[str] = None
    
    synthesizer_hf_model: Optional[str] = None
    synthesizer_hf_token: Optional[str] = None
    
    judge_hf_model: Optional[str] = None
    judge_hf_token: Optional[str] = None
    
    # Default model preferences (using free models)
    creator_model: str = "ollama-llama2"
    critic_model: str = "hf-qwen"
    radical_model: str = "ollama-mistral"
    synthesizer_model: str = "hf-qwen"
    judge_model: str = "gemini-2.5-flash"
    
    # Temperature settings
    creator_temperature: float = 0.8
    critic_temperature: float = 0.5
    radical_temperature: float = 0.9
    synthesizer_temperature: float = 0.6
    judge_temperature: float = 0.3
    
    # Model max tokens
    max_tokens: int = 2000


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
    def get_llm(cls, model_name: str, temperature: float = 0.7, agent_name: str = None) -> BaseLanguageModel:
        """
        Get or create an LLM instance.
        Supports: Ollama, Hugging Face, Google Gemini, OpenAI, Anthropic
        
        Args:
            model_name: Model identifier (e.g., "ollama-llama2", "hf-qwen", "gemini-pro", "gpt-4")
            temperature: Model temperature
            agent_name: Agent name for per-agent HF configuration (creator, critic, radical, etc.)
            
        Returns:
            BaseLanguageModel instance
        """
        cache_key = f"{model_name}_{temperature}_{agent_name or ''}"
        
        if cache_key in cls._llm_cache:
            return cls._llm_cache[cache_key]
        
        settings = cls.get_settings()
        llm = None
        
        # Ollama (local models)
        if model_name.startswith("ollama-"):
            actual_model = model_name.replace("ollama-", "")
            llm = ChatOpenAI(
                model_name=actual_model,
                temperature=temperature,
                api_key="ollama",
                base_url=settings.ollama_base_url,
                max_tokens=settings.max_tokens,
            )
        
        # Hugging Face Qwen
        elif model_name.startswith("hf-"):
            from langchain_community.llms import HuggingFaceHub
            
            # Get per-agent HF config if available
            hf_model = None
            hf_token = None
            
            if agent_name:
                # Try to get agent-specific config
                agent_model_attr = f"{agent_name}_hf_model"
                agent_token_attr = f"{agent_name}_hf_token"
                hf_model = getattr(settings, agent_model_attr, None)
                hf_token = getattr(settings, agent_token_attr, None)
            
            # Fall back to global config if not set per-agent
            if not hf_model:
                hf_model = "Qwen/Qwen1.5-7B-Chat"  # default
            if not hf_token:
                hf_token = settings.hf_token  # use global token as fallback
            
            llm = HuggingFaceHub(
                repo_id=hf_model,
                huggingfacehub_api_token=hf_token,
                model_kwargs={"temperature": temperature, "max_new_tokens": settings.max_tokens}
            )
        
        # Google Gemini
        elif model_name.startswith("gemini"):
            google_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                google_api_key=google_key,
                convert_system_message_to_human=True,
            )
        
        # OpenAI models
        elif model_name.startswith("gpt") or model_name.startswith("text-davinci"):
            if not settings.openai_api_key:
                if settings.openai_fallback_model:
                    return cls.get_llm(settings.openai_fallback_model, temperature, agent_name)
                raise ValueError("OpenAI API key missing and no OPENAI_FALLBACK_MODEL configured")
            llm = ChatOpenAI(
                model_name=model_name,
                temperature=temperature,
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                max_tokens=settings.max_tokens,
            )
        
        # Anthropic models
        elif model_name.startswith("claude"):
            llm = ChatAnthropic(
                model=model_name,
                temperature=temperature,
                api_key=settings.anthropic_api_key,
                max_tokens=settings.max_tokens,
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
        
        return cls.get_llm(model_name, temperature, agent_name)
    
    @classmethod
    def update_model_mapping(cls, agent_name: str, model_name: str):
        """Dynamically update model for an agent"""
        settings = cls.get_settings()
        model_attr = f"{agent_name}_model"
        setattr(settings, model_attr, model_name)
        cls._llm_cache.clear()  # Clear cache to pick up new model
