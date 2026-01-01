"""Test configuration management."""

import pytest
import os
from backend.config import Settings


def test_default_settings():
    """Test default settings values."""
    # Clear environment variables for testing
    original_env = os.environ.copy()
    
    # Remove relevant env vars
    for key in ['OPENROUTER_API_KEY', 'COUNCIL_MODELS', 'CHAIRMAN_MODEL']:
        if key in os.environ:
            del os.environ[key]
    
    try:
        # This should raise an error because API key is required
        with pytest.raises(ValueError, match='Invalid OpenRouter API key format'):
            Settings()
    finally:
        # Restore environment
        os.environ.clear()
        os.environ.update(original_env)


def test_api_key_validation():
    """Test API key validation."""
    original_env = os.environ.copy()
    
    try:
        # Test invalid API key
        os.environ['OPENROUTER_API_KEY'] = 'invalid-key'
        with pytest.raises(ValueError, match='Invalid OpenRouter API key format'):
            Settings()
        
        # Test valid API key
        os.environ['OPENROUTER_API_KEY'] = 'sk-or-v1-valid-key-here'
        settings = Settings()
        assert settings.openrouter_api_key == 'sk-or-v1-valid-key-here'
        
    finally:
        os.environ.clear()
        os.environ.update(original_env)


def test_positive_validators():
    """Test positive value validators."""
    original_env = os.environ.copy()
    
    try:
        os.environ['OPENROUTER_API_KEY'] = 'sk-or-v1-valid-key-here'
        
        # Test invalid rate limit
        os.environ['RATE_LIMIT_REQUESTS'] = '0'
        with pytest.raises(ValueError, match='Value must be positive'):
            Settings()
        
        # Test valid rate limit
        os.environ['RATE_LIMIT_REQUESTS'] = '10'
        settings = Settings()
        assert settings.rate_limit_requests == 10
        
    finally:
        os.environ.clear()
        os.environ.update(original_env)
