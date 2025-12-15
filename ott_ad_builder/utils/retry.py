"""
Retry Utilities for API Reliability

Implements exponential backoff retry logic for all AI providers:
- Anthropic Claude (429 rate limit, 529 overloaded, 500 internal)
- OpenAI GPT-5.2 (429 rate limit, 500/502/503 server errors)
- Fal.ai Flux (X-Fal-Retryable header, 503/504 transient errors)

Best practices implemented:
1. Exponential backoff with jitter
2. Maximum retry limits (default: 3)
3. Retryable vs non-retryable error classification
4. Detailed logging for debugging
"""

import time
import random
from functools import wraps
from typing import Callable, Type, Tuple, Optional


# Retryable HTTP status codes by provider
RETRY_STATUS_CODES = {
    "anthropic": [429, 500, 529],  # rate_limit, api_error, overloaded
    "openai": [429, 500, 502, 503],  # rate_limit, server errors
    "fal": [503, 504],  # transient connection issues (queue handles others)
}


def exponential_backoff(
    retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    retryable_status_codes: Optional[list] = None,
    provider: str = "generic"
):
    """
    Decorator for exponential backoff retry with jitter.
    
    Args:
        retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exponential_base: Base for exponential calculation (default 2x)
        jitter: Add random jitter to prevent thundering herd
        retryable_exceptions: Tuple of exception types to retry on
        retryable_status_codes: HTTP status codes that trigger retry
        provider: Provider name for logging ('anthropic', 'openai', 'fal')
    
    Usage:
        @exponential_backoff(retries=3, provider="anthropic")
        def call_claude_api():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is a retryable error
                    is_retryable = False
                    status_code = None
                    
                    # Extract status code from exception if present
                    if hasattr(e, 'status_code'):
                        status_code = e.status_code
                    elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                        status_code = e.response.status_code
                    elif hasattr(e, 'status'):
                        status_code = e.status
                    
                    # Check retryable status codes
                    codes_to_check = retryable_status_codes or RETRY_STATUS_CODES.get(provider, [])
                    if status_code and status_code in codes_to_check:
                        is_retryable = True
                    
                    # Check exception type
                    if isinstance(e, retryable_exceptions):
                        # Check for specific error messages indicating transient issues
                        error_msg = str(e).lower()
                        transient_keywords = [
                            'rate limit', 'overloaded', 'temporarily', 'timeout',
                            'connection', 'network', 'retry', '529', '503', '504'
                        ]
                        if any(kw in error_msg for kw in transient_keywords):
                            is_retryable = True
                    
                    # If not retryable, raise immediately
                    if not is_retryable:
                        print(f"[RETRY] {provider.upper()} - Non-retryable error: {e}")
                        raise
                    
                    # If this was the last attempt, raise
                    if attempt >= retries:
                        print(f"[RETRY] {provider.upper()} - Max retries ({retries}) exceeded. Giving up.")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter (±25% of delay)
                    if jitter:
                        jitter_amount = delay * 0.25 * random.uniform(-1, 1)
                        delay = max(0.1, delay + jitter_amount)
                    
                    print(f"[RETRY] {provider.upper()} - Attempt {attempt + 1}/{retries} failed: {e}")
                    print(f"[RETRY] {provider.upper()} - Retrying in {delay:.2f}s...")
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def retry_on_rate_limit(func: Callable, provider: str = "generic"):
    """
    Simple decorator specifically for rate limit handling.
    Waits 60 seconds on rate limit (429) errors.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check for rate limit
                status_code = getattr(e, 'status_code', None) or getattr(getattr(e, 'response', None), 'status_code', None)
                
                if status_code == 429:
                    if attempt >= max_retries:
                        print(f"[RATE LIMIT] {provider.upper()} - Max retries exceeded.")
                        raise
                    
                    # Look for Retry-After header
                    retry_after = 60  # Default
                    if hasattr(e, 'response') and hasattr(e.response, 'headers'):
                        retry_after = int(e.response.headers.get('Retry-After', 60))
                    
                    print(f"[RATE LIMIT] {provider.upper()} - Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                else:
                    raise
        
    return wrapper


class APIHealthCheck:
    """
    Health check utility to verify API availability before batch operations.
    """
    
    @staticmethod
    def check_anthropic(client) -> dict:
        """Test Anthropic API with minimal request."""
        try:
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=10,
                messages=[{"role": "user", "content": "Say OK"}]
            )
            return {"status": "healthy", "response": response.content[0].text}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    def check_openai(client) -> dict:
        """Test OpenAI API with minimal request."""
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=10,
                messages=[{"role": "user", "content": "Say OK"}]
            )
            return {"status": "healthy", "response": response.choices[0].message.content}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    def check_fal(model_id: str = "fal-ai/flux-pro/v1.1") -> dict:
        """Test Fal.ai API with minimal request."""
        import fal_client
        try:
            # Use a very simple test prompt
            handler = fal_client.submit(
                model_id,
                arguments={
                    "prompt": "solid black square",
                    "image_size": "square",
                    "num_images": 1
                }
            )
            # Just check if we can submit - don't wait for result
            return {"status": "healthy", "request_id": handler.request_id}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
