"""Custom exceptions for GitHub API client."""

from typing import Optional


class GitHubError(Exception):
    """Base exception for GitHub API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[dict] = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class GitHubAuthenticationError(GitHubError):
    """Authentication failed - invalid or expired token."""
    pass


class GitHubRateLimitError(GitHubError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, reset_time: Optional[int] = None):
        self.reset_time = reset_time
        super().__init__(message, status_code=429)


class GitHubNotFoundError(GitHubError):
    """Resource not found."""
    pass


class GitHubValidationError(GitHubError):
    """Invalid request parameters (422)."""
    pass


class GitHubConflictError(GitHubError):
    """Resource conflict (e.g., file already exists)."""
    pass


class GitHubConnectionError(GitHubError):
    """Network connection error."""
    pass