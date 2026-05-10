

import base64
import json
import logging
from typing import Optional, Dict, Any, List

import httpx

from github_mcp.config import settings
from github_mcp.github.exceptions import (
    GitHubError,
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubNotFoundError,
    GitHubValidationError,
    GitHubConflictError,
    GitHubConnectionError,
)
from github_mcp.github.rate_limiter import RateLimiter
from github_mcp.github.models import (
    GitHubUser,
    GitHubRepository,
    GitHubContent,
    GitHubCommit,
    GitHubIssue,
    GitHubPullRequest,
)
from github_mcp.utils.retry import async_retry

logger = logging.getLogger(__name__)


class GitHubClient:
    """Async GitHub API client with comprehensive error handling."""
    
    def __init__(self):
        """Initialize GitHub client with configuration."""
        self.base_url = settings.github_api_base_url
        self.token = settings.github_token
        self.timeout = settings.github_request_timeout
        self.rate_limiter = RateLimiter()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
    
    async def initialize(self) -> None:
        """Initialize HTTP client and validate authentication."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": f"GitHub-MCP-Server/{settings.mcp_server_version}",
            },
            follow_redirects=True,
        )
        
        # Validate token by getting current user
        try:
            await self.get_current_user()
            logger.info("GitHub authentication successful")
        except Exception as e:
            logger.error(f"GitHub authentication failed: {e}")
            raise GitHubAuthenticationError(f"Failed to authenticate with GitHub: {e}")
    
    async def close(self) -> None:
        """Close HTTP client session."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure client is initialized."""
        if not self._client:
            raise GitHubError("Client not initialized. Call initialize() first.")
        return self._client
    
    async def _handle_response(self, response: httpx.Response, endpoint: str) -> Dict[str, Any]:
        """Parse response and handle errors."""
        # Update rate limiter with headers
        self.rate_limiter.update_from_headers(dict(response.headers))
        
        # Check for HTTP errors
        if response.status_code == 401:
            raise GitHubAuthenticationError("Invalid or expired GitHub token")
        elif response.status_code == 403:
            # Check if rate limited
            if 'X-RateLimit-Remaining' in response.headers and int(response.headers['X-RateLimit-Remaining']) == 0:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                raise GitHubRateLimitError(
                    "GitHub API rate limit exceeded. Please wait.",
                    reset_time=reset_time
                )
            else:
                error_msg = f"Access forbidden: {response.text}"
                raise GitHubError(error_msg, status_code=403)
        elif response.status_code == 404:
            raise GitHubNotFoundError(f"Resource not found: {endpoint}")
        elif response.status_code == 422:
            error_data = response.json() if response.text else {}
            raise GitHubValidationError(
                f"Validation failed: {error_data.get('message', response.text)}",
                status_code=422,
                response_data=error_data
            )
        elif response.status_code == 409:
            raise GitHubConflictError(f"Conflict: {response.text}", status_code=409)
        elif response.status_code >= 500:
            raise GitHubError(
                f"GitHub server error: {response.status_code}",
                status_code=response.status_code
            )
        
        # Parse JSON response
        try:
            return response.json() if response.text else {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from {endpoint}: {e}")
            raise GitHubError(f"Invalid JSON response from GitHub: {e}")
    
    @async_retry(max_retries=3)
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to GitHub API with retry logic."""
        client = self._ensure_client()
        
        # Log request (without sensitive data)
        logger.debug(f"Request: {method} {endpoint} - params={params}")
        
        try:
            response = await client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params
            )
            
            return await self._handle_response(response, endpoint)
            
        except httpx.TimeoutException as e:
            logger.error(f"Timeout on {method} {endpoint}: {e}")
            raise GitHubConnectionError(f"Request timeout after {self.timeout}s: {e}")
        except httpx.NetworkError as e:
            logger.error(f"Network error on {method} {endpoint}: {e}")
            raise GitHubConnectionError(f"Network error: {e}")
        except (GitHubError, GitHubAuthenticationError, GitHubRateLimitError) as e:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error on {method} {endpoint}: {e}", exc_info=True)
            raise GitHubError(f"Unexpected error: {e}")
    
    # ===== User Methods =====
    
    async def get_current_user(self) -> GitHubUser:
        """Get authenticated user information."""
        data = await self._request("GET", "/user")
        return GitHubUser(**data)
    
    # ===== Repository Methods =====
    
    async def list_repositories(
        self,
        visibility: str = "all",
        per_page: int = 30,
        page: int = 1
    ) -> List[GitHubRepository]:
        """List repositories for authenticated user."""
        params = {
            "visibility": visibility,
            "per_page": min(per_page, 100),
            "page": page,
            "sort": "updated",
            "direction": "desc"
        }
        
        data = await self._request("GET", "/user/repos", params=params)
        return [GitHubRepository(**repo) for repo in data]
    
    async def get_repository(self, owner: str, repo: str) -> GitHubRepository:
        """Get repository by owner and name."""
        data = await self._request("GET", f"/repos/{owner}/{repo}")
        return GitHubRepository(**data)
    
    async def search_repositories(
        self,
        query: str,
        per_page: int = 30,
        page: int = 1
    ) -> List[GitHubRepository]:
        """Search repositories by query."""
        params = {
            "q": query,
            "per_page": min(per_page, 100),
            "page": page,
            "sort": "stars",
            "order": "desc"
        }
        
        data = await self._request("GET", "/search/repositories", params=params)
        return [GitHubRepository(**item) for item in data.get("items", [])]
    
    # ===== Content Methods =====
    
    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None
    ) -> GitHubContent:
        """Get file content from repository."""
        params = {}
        if ref:
            params["ref"] = ref
        
        data = await self._request("GET", f"/repos/{owner}/{repo}/contents/{path}", params=params)
        return GitHubContent(**data)
    
    async def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: Optional[str] = None,
        sha: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update a file in repository."""
        # Prepare request data - only include non-None values
        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode()
        }
        
        # Only add branch if provided
        if branch:
            data["branch"] = branch
        
        # Only add sha if provided (for updates)
        if sha:
            data["sha"] = sha
        
        logger.debug(f"Creating/updating file {path} in {owner}/{repo} (branch: {branch or 'default'})")
        
        return await self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", data=data)
    
    # ===== Methods for later phases =====
    
    async def list_commits(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        per_page: int = 30,
        page: int = 1
    ) -> List[GitHubCommit]:
        """List commits in repository."""
        params = {
            "per_page": min(per_page, 100),
            "page": page,
        }
        if branch:
            params["sha"] = branch
        
        data = await self._request("GET", f"/repos/{owner}/{repo}/commits", params=params)
        return [GitHubCommit(**commit) for commit in data]
    
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None
    ) -> GitHubIssue:
        """Create an issue."""
        data = {
            "title": title,
        }
        if body:
            data["body"] = body
        if assignees:
            data["assignees"] = assignees
        if labels:
            data["labels"] = labels
        
        response = await self._request("POST", f"/repos/{owner}/{repo}/issues", data=data)
        return GitHubIssue(**response)
    
    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
        page: int = 1
    ) -> List[GitHubPullRequest]:
        """List pull requests."""
        params = {
            "state": state,
            "per_page": min(per_page, 100),
            "page": page,
            "sort": "updated",
            "direction": "desc"
        }
        
        data = await self._request("GET", f"/repos/{owner}/{repo}/pulls", params=params)
        return [GitHubPullRequest(**pr) for pr in data]
