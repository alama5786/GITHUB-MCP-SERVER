"""GitHub API client module."""

from github_mcp.github.client import GitHubClient
from github_mcp.github.exceptions import (
    GitHubError,
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubNotFoundError,
    GitHubValidationError,
    GitHubConflictError,
    GitHubConnectionError,
)
from github_mcp.github.models import (
    GitHubRepository,
    GitHubUser,
    GitHubContent,
    GitHubCommit,
    GitHubIssue,
    GitHubPullRequest,
)

__all__ = [
    "GitHubClient",
    "GitHubError",
    "GitHubAuthenticationError",
    "GitHubRateLimitError",
    "GitHubNotFoundError",
    "GitHubValidationError",
    "GitHubConflictError",
    "GitHubConnectionError",
    "GitHubRepository",
    "GitHubUser",
    "GitHubContent",
    "GitHubCommit",
    "GitHubIssue",
    "GitHubPullRequest",
]