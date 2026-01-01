"""OpenRouter API client for making LLM requests."""

import httpx
import logging
from typing import List, Dict, Any, Optional
from .config import settings

logger = logging.getLogger(__name__)


class OpenRouterError(Exception):
    """Custom exception for OpenRouter API errors."""
    pass


# Global HTTP client with connection pooling
_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create the global HTTP client with connection pooling."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.default_timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            http2=True
        )
        logger.info("Created HTTP client with connection pooling")
    return _client


async def close_http_client():
    """Close the global HTTP client."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("Closed HTTP client")


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds (overrides default)

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    if not settings.openrouter_api_key:
        logger.error("OpenRouter API key not configured")
        raise OpenRouterError("API key not configured")

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/tomazb/llm-council",
        "X-Title": "LLM Council",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    client = await get_http_client()
    
    # Override timeout if provided
    if timeout is not None:
        client = httpx.AsyncClient(timeout=timeout)

    try:
        response = await client.post(
            settings.openrouter_api_url,
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
        if e.response.status_code == 429:
            logger.warning("Rate limit exceeded for OpenRouter API")
        return None
    except httpx.TimeoutException:
        logger.error(f"Timeout querying model {model} after {timeout or settings.default_timeout}s")
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
    finally:
        # Close temporary client if timeout was overridden
        if timeout is not None:
            await client.aclose()


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel with connection pooling.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    logger.info(f"Querying {len(models)} models in parallel")
    
    # Create tasks for all models
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete with timeout
    try:
        responses = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"Error in parallel query: {e}")
        return {model: None for model in models}

    # Map models to their responses, handle exceptions
    result = {}
    successful_count = 0
    
    for model, response in zip(models, responses):
        if isinstance(response, Exception):
            logger.error(f"Exception in parallel query for {model}: {response}")
            result[model] = None
        else:
            result[model] = response
            if response is not None:
                successful_count += 1
    
    logger.info(f"Parallel query completed: {successful_count}/{len(models)} successful")
    return result


# Simple cache for title generation to avoid repeated API calls
_title_cache: Dict[str, str] = {}


async def generate_title_cached(query: str) -> str:
    """Generate title with simple caching to avoid repeated API calls."""
    # Simple cache key based on query hash
    import hashlib
    cache_key = hashlib.md5(query.encode()).hexdigest()[:16]
    
    if cache_key in _title_cache:
        logger.debug(f"Using cached title for query hash: {cache_key}")
        return _title_cache[cache_key]
    
    # Generate new title (this would call the actual title generation)
    # For now, return a simple title
    title = query[:50] + "..." if len(query) > 50 else query
    
    # Cache the result
    _title_cache[cache_key] = title
    
    # Limit cache size
    if len(_title_cache) > 100:
        # Remove oldest entries (simple LRU)
        oldest_key = next(iter(_title_cache))
        del _title_cache[oldest_key]
    
    return title
