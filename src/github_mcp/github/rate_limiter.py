"""Rate limit tracking for GitHub API."""

import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Track and manage GitHub API rate limits."""
    
    def __init__(self):
        self.limit: Optional[int] = None
        self.remaining: Optional[int] = None
        self.reset_time: Optional[int] = None
        self.used: Optional[int] = None
    
    def update_from_headers(self, headers: dict) -> None:
        """Update rate limit information from response headers."""
        if 'X-RateLimit-Limit' in headers:
            self.limit = int(headers['X-RateLimit-Limit'])
        if 'X-RateLimit-Remaining' in headers:
            self.remaining = int(headers['X-RateLimit-Remaining'])
        if 'X-RateLimit-Reset' in headers:
            self.reset_time = int(headers['X-RateLimit-Reset'])
        if 'X-RateLimit-Used' in headers:
            self.used = int(headers['X-RateLimit-Used'])
        
        # Log warning if rate limit is low
        if self.remaining is not None and self.remaining < 100:
            logger.warning(
                f"Low rate limit remaining: {self.remaining}/{self.limit}. "
                f"Resets at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.reset_time))}"
            )
    
    def get_wait_time(self) -> Optional[float]:
        """Get seconds to wait until rate limit resets."""
        if self.remaining is not None and self.remaining <= 0 and self.reset_time:
            wait_time = max(0, self.reset_time - int(time.time()))
            return wait_time
        return None
    
    def __repr__(self) -> str:
        return f"RateLimiter(limit={self.limit}, remaining={self.remaining}, reset={self.reset_time})"