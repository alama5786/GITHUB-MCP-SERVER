"""Issues and Pull Requests tools for GitHub repositories."""

import logging
from typing import Dict, Callable, Awaitable, Any, List, Optional

import mcp.types as types

from github_mcp.github import GitHubClient, GitHubIssue, GitHubPullRequest

logger = logging.getLogger(__name__)

# Store tool handlers and definitions
_tool_handlers: Dict[str, Callable[[dict], Awaitable[str]]] = {}
_tool_definitions: List[types.Tool] = []

# Global client reference
github_client_instance: Optional[GitHubClient] = None


async def get_client() -> GitHubClient:
    """Lazy initialization of GitHub client."""
    global github_client_instance
    if github_client_instance is None:
        github_client_instance = GitHubClient()
        await github_client_instance.initialize()
        logger.info("GitHub client initialized for issues/PRs")
    return github_client_instance


async def cleanup() -> None:
    """Clean up GitHub client resources."""
    global github_client_instance
    if github_client_instance:
        await github_client_instance.close()
        github_client_instance = None
        logger.info("GitHub client closed")


def format_issue(issue: GitHubIssue, detailed: bool = False) -> str:
    """Format an issue for display."""
    lines = [
        f"**#{issue.number}** - {issue.title}",
        f"State: {issue.state} | Created: {issue.created_at.strftime('%Y-%m-%d')}",
        f"Author: {issue.user.login}",
    ]
    
    if issue.labels:
        labels = [label.get('name', '') for label in issue.labels if isinstance(label, dict)]
        if labels:
            lines.append(f"Labels: {', '.join(labels)}")
    
    if issue.assignees:
        assignees = [assignee.login for assignee in issue.assignees]
        lines.append(f"Assignees: {', '.join(assignees)}")
    
    if detailed and issue.body:
        body_preview = issue.body[:200].replace('\n', ' ')
        lines.append(f"Description: {body_preview}...")
    
    lines.append(f"URL: {issue.html_url}")
    
    return "\n  ".join(lines)


def format_pull_request(pr: GitHubPullRequest, detailed: bool = False) -> str:
    """Format a pull request for display."""
    state_emoji = {
        'open': '🔄',
        'closed': '❌',
        'merged': '✅'
    }.get(pr.state, '📋')
    
    lines = [
        f"{state_emoji} **#{pr.number}** - {pr.title}",
        f"State: {pr.state} | Created: {pr.created_at.strftime('%Y-%m-%d')}",
        f"Author: {pr.user.login}",
    ]
    
    if pr.additions is not None:
        lines.append(f"Changes: +{pr.additions}/-{pr.deletions} in {pr.changed_files} files")
    
    if detailed and pr.body:
        body_preview = pr.body[:200].replace('\n', ' ')
        lines.append(f"Description: {body_preview}...")
    
    lines.append(f"URL: {pr.html_url}")
    
    return "\n  ".join(lines)


def register_tools(server) -> None:
    """Register issues and PR tools with the MCP server."""
    global _tool_handlers, _tool_definitions
    
    logger.info("Registering issues and PR tools...")
    
    # Tool 1: create_issue
    async def create_issue_handler(arguments: dict) -> str:
        """Handle create_issue tool calls."""
        owner = arguments.get("owner", "")
        repo = arguments.get("repo", "")
        title = arguments.get("title", "")
        body = arguments.get("body", None)
        assignees = arguments.get("assignees", None)
        labels = arguments.get("labels", None)
        
        # Validate required parameters
        if not owner:
            return "Error: 'owner' parameter is required"
        if not repo:
            return "Error: 'repo' parameter is required"
        if not title:
            return "Error: 'title' parameter is required"
        
        logger.info(f"Creating issue in {owner}/{repo}: '{title[:50]}'")
        
        try:
            client = await get_client()
            issue = await client.create_issue(
                owner=owner,
                repo=repo,
                title=title,
                body=body,
                assignees=assignees,
                labels=labels
            )
            
            # Format response
            result_lines = [
                f"✅ Issue created successfully!",
                f"",
                format_issue(issue, detailed=True),
                f"",
                f"💡 You can also reference this issue as #{issue.number}"
            ]
            
            return "\n".join(result_lines)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating issue: {e}", exc_info=True)
            return f"Error creating issue: {error_msg}"
    
    # Tool 2: list_pull_requests
    async def list_pull_requests_handler(arguments: dict) -> str:
        """Handle list_pull_requests tool calls."""
        owner = arguments.get("owner", "")
        repo = arguments.get("repo", "")
        state = arguments.get("state", "open")
        per_page = arguments.get("per_page", 10)
        
        # Validate required parameters
        if not owner:
            return "Error: 'owner' parameter is required"
        if not repo:
            return "Error: 'repo' parameter is required"
        
        # Validate state
        if state not in ["open", "closed", "all"]:
            return f"Error: Invalid state '{state}'. Must be 'open', 'closed', or 'all'"
        
        # Validate per_page
        if not isinstance(per_page, int) or per_page < 1 or per_page > 100:
            return f"Error: per_page must be between 1 and 100, got {per_page}"
        
        logger.info(f"Listing PRs in {owner}/{repo} with state='{state}'")
        
        try:
            client = await get_client()
            prs = await client.list_pull_requests(
                owner=owner,
                repo=repo,
                state=state,
                per_page=per_page
            )
            
            if not prs:
                return f"No {state} pull requests found in {owner}/{repo}"
            
            # Format response
            result_lines = [
                f"## Pull Requests in {owner}/{repo}",
                f"**State**: {state}",
                f"**Found**: {len(prs)} PRs\n"
            ]
            
            for i, pr in enumerate(prs, 1):
                result_lines.append(format_pull_request(pr, detailed=False))
                if i < len(prs):
                    result_lines.append("")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            logger.error(f"Error listing PRs: {e}", exc_info=True)
            return f"Error listing pull requests: {str(e)}"
    
    # Tool 3: create_pull_request
    async def create_pull_request_handler(arguments: dict) -> str:
        """Handle create_pull_request tool calls."""
        owner = arguments.get("owner", "")
        repo = arguments.get("repo", "")
        title = arguments.get("title", "")
        head = arguments.get("head", "")      # Source branch
        base = arguments.get("base", "main")  # Target branch
        body = arguments.get("body", None)
        draft = arguments.get("draft", False)
        
        # Validate required parameters
        if not owner:
            return "Error: 'owner' parameter is required"
        if not repo:
            return "Error: 'repo' parameter is required"
        if not title:
            return "Error: 'title' parameter is required"
        if not head:
            return "Error: 'head' parameter is required (source branch name)"
        
        logger.info(f"Creating PR in {owner}/{repo}: '{title[:50]}' from {head} to {base}")
        
        try:
            client = await get_client()
            
            # Need to use direct API call for PR creation
            data = {
                "title": title,
                "head": head,
                "base": base,
                "draft": draft
            }
            if body:
                data["body"] = body
            
            # POST /repos/{owner}/{repo}/pulls
            response = await client._request("POST", f"/repos/{owner}/{repo}/pulls", data=data)
            
            # Parse response
            pr = GitHubPullRequest(**response)
            
            # Format response
            result_lines = [
                f"✅ Pull Request created successfully!",
                f"",
                format_pull_request(pr, detailed=True),
                f"",
                f"📝 Next steps:",
                f"   • Review the PR at: {pr.html_url}",
                f"   • Add reviewers if needed",
                f"   • Run tests before merging",
                f"",
                f"💡 This PR will be automatically linked to this conversation."
            ]
            
            return "\n".join(result_lines)
            
        except Exception as e:
            error_msg = str(e)
            if "No commits between" in error_msg:
                return f"Error: No commits found in '{head}' branch. Make sure the branch exists and has commits."
            elif "Validation Failed" in error_msg:
                return f"Error: Invalid PR parameters. Check that the '{head}' branch exists and '{base}' is a valid branch."
            logger.error(f"Error creating PR: {e}", exc_info=True)
            return f"Error creating pull request: {error_msg}"
    
    # Create tool definitions
    create_issue_tool = types.Tool(
        name="create_issue",
        description="Create a new GitHub issue. Use this to report bugs, request features, track tasks, or document work items.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "GitHub username or organization that owns the repository"
                },
                "repo": {
                    "type": "string",
                    "description": "Name of the repository"
                },
                "title": {
                    "type": "string",
                    "description": "Issue title (brief summary)"
                },
                "body": {
                    "type": "string",
                    "description": "Issue description (supports Markdown)"
                },
                "assignees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "GitHub usernames to assign (optional)"
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Labels to add (e.g., ['bug', 'enhancement'])"
                }
            },
            "required": ["owner", "repo", "title"]
        }
    )
    
    list_prs_tool = types.Tool(
        name="list_pull_requests",
        description="List pull requests in a GitHub repository. Use this to see open PRs, track review status, or find PRs to review.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "GitHub username or organization"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name"
                },
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "description": "Filter by state (default: 'open')",
                    "default": "open"
                },
                "per_page": {
                    "type": "integer",
                    "description": "Number of results (1-100, default: 10)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["owner", "repo"]
        }
    )
    
    create_pr_tool = types.Tool(
        name="create_pull_request",
        description="Create a new pull request. Use this to propose changes from one branch to another, request code review, or merge features.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "GitHub username or organization"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name"
                },
                "title": {
                    "type": "string",
                    "description": "Pull request title"
                },
                "head": {
                    "type": "string",
                    "description": "Source branch containing changes"
                },
                "base": {
                    "type": "string",
                    "description": "Target branch to merge into (default: 'main')",
                    "default": "main"
                },
                "body": {
                    "type": "string",
                    "description": "PR description (supports Markdown)"
                },
                "draft": {
                    "type": "boolean",
                    "description": "Create as draft PR (not ready for review)",
                    "default": False
                }
            },
            "required": ["owner", "repo", "title", "head"]
        }
    )
    
    # Store handlers
    _tool_handlers["create_issue"] = create_issue_handler
    _tool_handlers["list_pull_requests"] = list_pull_requests_handler
    _tool_handlers["create_pull_request"] = create_pull_request_handler
    
    # Store definitions
    _tool_definitions = [create_issue_tool, list_prs_tool, create_pr_tool]
    
    logger.info(f"Registered {len(_tool_handlers)} issues/PR tools")


def get_tool_handlers() -> Dict[str, Callable[[dict], Awaitable[str]]]:
    """Return dictionary of tool name to handler function."""
    return _tool_handlers


def get_tool_definitions() -> List[types.Tool]:
    """Return list of tool definitions."""
    return _tool_definitions