"""OpenRouter API client for making LLM requests."""

import httpx
import logging
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL

logger = logging.getLogger(__name__)


class OpenRouterError(Exception):
    """Custom exception for OpenRouter API errors."""
    pass


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    if not OPENROUTER_API_KEY:
        logger.error("OpenRouter API key not configured")
        raise OpenRouterError("API key not configured")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details')
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error querying model {model}: {e.response.status_code} - {e.response.text}")
        return None
    except httpx.TimeoutException:
        logger.error(f"Timeout querying model {model} after {timeout}s")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error querying model {model}: {e}")
        return None
    except (KeyError, IndexError) as e:
        logger.error(f"Invalid response format from model {model}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    # Create tasks for all models
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # Map models to their responses, handle exceptions
    result = {}
    for model, response in zip(models, responses):
        if isinstance(response, Exception):
            logger.error(f"Exception in parallel query for {model}: {response}")
            result[model] = None
        else:
            result[model] = response

    return result
