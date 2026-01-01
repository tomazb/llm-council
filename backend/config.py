"""Configuration for the LLM Council."""

import os
import logging
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # OpenRouter API configuration
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    openrouter_api_url: str = Field(
        default="https://openrouter.ai/api/v1/chat/completions",
        env="OPENROUTER_API_URL"
    )
    
    # Council models configuration
    council_models: List[str] = Field(
        default=[
            "openai/gpt-4o",
            "google/gemini-pro",
            "anthropic/claude-3-sonnet",
            "x-ai/grok-beta",
        ],
        env="COUNCIL_MODELS"
    )
    
    chairman_model: str = Field(
        default="google/gemini-pro",
        env="CHAIRMAN_MODEL"
    )
    
    # Storage configuration
    data_dir: str = Field(default="data/conversations", env="DATA_DIR")
    
    # API configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8001, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Rate limiting
    rate_limit_requests: int = Field(default=10, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # Request timeouts
    default_timeout: float = Field(default=120.0, env="DEFAULT_TIMEOUT")
    title_generation_timeout: float = Field(default=30.0, env="TITLE_GENERATION_TIMEOUT")
    
    # CORS configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    
    @field_validator('openrouter_api_key')
    @classmethod
    def validate_api_key(cls, v):
        if not v or not v.startswith('sk-or-'):
            raise ValueError('Invalid OpenRouter API key format')
        return v
    
    @field_validator('data_dir')
    @classmethod
    def validate_data_dir(cls, v):
        if not v:
            raise ValueError('Data directory cannot be empty')
        return v
    
    @field_validator('council_models')
    @classmethod
    def validate_council_models(cls, v):
        if not v:
            raise ValueError('At least one council model must be specified')
        return v
    
    @field_validator('rate_limit_requests', 'rate_limit_window')
    @classmethod
    def validate_positive_int(cls, v):
        if v <= 0:
            raise ValueError('Value must be positive')
        return v
    
    @field_validator('default_timeout', 'title_generation_timeout')
    @classmethod
    def validate_positive_float(cls, v):
        if v <= 0:
            raise ValueError('Timeout must be positive')
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Create global settings instance
try:
    settings = Settings()
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise

# Export individual settings for backward compatibility
OPENROUTER_API_KEY = settings.openrouter_api_key
OPENROUTER_API_URL = settings.openrouter_api_url
COUNCIL_MODELS = settings.council_models
CHAIRMAN_MODEL = settings.chairman_model
DATA_DIR = settings.data_dir
