"""Retry utilities with exponential backoff."""

import asyncio
import random
import logging
from functools import wraps
from typing import TypeVar, Callable, Awaitable, Optional, List, Any

T = TypeVar('T')

logger = logging.getLogger(__name__)


def async_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_multiplier: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[List[Any]] = None
):
    """Decorator for async functions with exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_multiplier: Multiplier for each retry
        jitter: Add random jitter to delay
        retry_on_exceptions: List of exception types to retry on
    """
    if retry_on_exceptions is None:
        # Default retry on network errors and server errors
        import httpx
        retry_on_exceptions = [
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
        ]
    
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry this exception
                    should_retry = any(
                        isinstance(e, exc_type) for exc_type in retry_on_exceptions
                    )
                    
                    if not should_retry or attempt == max_retries:
                        raise
                    
                    # Calculate delay with jitter
                    current_delay = delay
                    if jitter:
                        current_delay = delay * (1 + random.uniform(-0.25, 0.25))
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {current_delay:.2f}s: {e}"
                    )
                    
                    await asyncio.sleep(current_delay)
                    
                    # Update delay for next attempt
                    delay = min(delay * backoff_multiplier, max_delay)
            
            # Should never reach here
            raise last_exception
        
        return wrapper
    
    return decorator