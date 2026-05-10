

import logging
import re
from typing import Dict, Callable, Awaitable, Any, List, Optional

import mcp.types as types

from github_mcp.github import GitHubClient

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
        logger.info("GitHub client initialized for git operations")
    return github_client_instance


async def cleanup() -> None:
    """Clean up GitHub client resources."""
    global github_client_instance
    if github_client_instance:
        await github_client_instance.close()
        github_client_instance = None
        logger.info("GitHub client closed")


def validate_branch_name(branch_name: str) -> bool:
    """Validate Git branch naming conventions."""
    if not branch_name or len(branch_name) > 255:
        return False
    
    if branch_name.startswith('-'):
        return False
    
    if '..' in branch_name:
        return False
    
    if '@{' in branch_name:
        return False
    
    forbidden_chars = r'[~^:?*\[\]\\]'
    if re.search(forbidden_chars, branch_name):
        return False
    
    if branch_name.endswith('/'):
        return False
    
    if '//' in branch_name:
        return False
    
    return True


def format_commit(commit: Any, short: bool = True) -> str:
    """Format a commit for display."""
    # Handle both dict and object
    if hasattr(commit, 'dict'):
        commit = commit.dict()
    
    sha = commit.get('sha', 'unknown')[:8] if short else commit.get('sha', 'unknown')
    
    # Extract commit details
    commit_data = commit.get('commit', {})
    message = commit_data.get('message', 'No message').split('\n')[0]
    
    author = commit_data.get('author', {})
    author_name = author.get('name', 'Unknown')
    date = author.get('date', '')[:10] if author.get('date') else 'Unknown'
    
    # Extract author info from nested structure if available
    if 'author' in commit and commit['author'] and isinstance(commit['author'], dict):
        author_name = commit['author'].get('login', author_name)
    
    if short:
        return f"  • `{sha}` - {message[:50]} - {author_name} ({date})"
    else:
        return f"Commit: {sha}\n  Message: {message}\n  Author: {author_name}\n  Date: {date}"


def format_file_change(file_info: Dict[str, Any]) -> str:
    """Format a file change for display."""
    filename = file_info.get('filename', 'unknown')
    status = file_info.get('status', 'modified')
    additions = file_info.get('additions', 0)
    deletions = file_info.get('deletions', 0)
    
    status_emoji = {
        'added': '➕',
        'removed': '➖',
        'modified': '📝',
        'renamed': '🔄',
        'copied': '📋'
    }.get(status, '•')
    
    return f"  {status_emoji} `{filename}` (+{additions}/-{deletions})"


def register_tools(server) -> None:
    """Register git operations tools with the MCP server."""
    global _tool_handlers, _tool_definitions
    
    logger.info("Registering git operations tools...")
    
    # Tool 1: list_commits
    async def list_commits_handler(arguments: dict) -> str:
        """Handle list_commits tool calls."""
        owner = arguments.get("owner", "")
        repo = arguments.get("repo", "")
        branch = arguments.get("branch", None)
        per_page = arguments.get("per_page", 10)
        
        if not owner or not repo:
            return "Error: 'owner' and 'repo' parameters are required"
        
        if not isinstance(per_page, int) or per_page < 1 or per_page > 100:
            return f"Error: per_page must be between 1 and 100, got {per_page}"
        
        logger.info(f"Listing commits for {owner}/{repo} (branch: {branch or 'default'})")
        
        try:
            client = await get_client()
            commits = await client.list_commits(owner, repo, branch=branch, per_page=per_page)
            
            if not commits:
                return f"No commits found in {owner}/{repo}" + (f" on branch '{branch}'" if branch else "")
            
            result_lines = [
                f"## Commit History for {owner}/{repo}",
                f"**Branch**: {branch or 'default'}",
                f"**Showing last {len(commits)} commits**\n"
            ]
            
            for commit in commits[:per_page]:
                result_lines.append(format_commit(commit, short=True))
            
            return "\n".join(result_lines)
            
        except Exception as e:
            logger.error(f"Error listing commits: {e}", exc_info=True)
            return f"Error listing commits: {str(e)}"
    
    # Tool 2: create_branch
    async def create_branch_handler(arguments: dict) -> str:
        """Handle create_branch tool calls."""
        owner = arguments.get("owner", "")
        repo = arguments.get("repo", "")
        branch_name = arguments.get("branch", "")
        source_branch = arguments.get("source_branch", "main")
        
        if not owner or not repo:
            return "Error: 'owner' and 'repo' parameters are required"
        
        if not branch_name:
            return "Error: 'branch' parameter is required"
        
        if not validate_branch_name(branch_name):
            return f"Error: Invalid branch name '{branch_name}'"
        
        logger.info(f"Creating branch '{branch_name}' in {owner}/{repo} from '{source_branch}'")
        
        try:
            client = await get_client()
            
            # Get the SHA of the source branch
            commits = await client.list_commits(owner, repo, branch=source_branch, per_page=1)
            if not commits:
                return f"Error: Source branch '{source_branch}' not found or has no commits"
            
            # Get SHA from first commit
            if hasattr(commits[0], 'sha'):
                source_sha = commits[0].sha
            else:
                source_sha = commits[0]['sha']
            
            # Create reference (branch)
            ref_path = f"refs/heads/{branch_name}"
            data = {
                "ref": ref_path,
                "sha": source_sha
            }
            
            result = await client._request("POST", f"/repos/{owner}/{repo}/git/refs", data=data)
            
            result_lines = [
                f"✅ Branch created successfully!",
                f"",
                f"**Repository**: {owner}/{repo}",
                f"**New Branch**: {branch_name}",
                f"**Source Branch**: {source_branch}",
                f"**Source Commit**: {source_sha[:8]}",
                f"**Branch Reference**: {result.get('ref', ref_path)}"
            ]
            
            return "\n".join(result_lines)
            
        except Exception as e:
            error_msg = str(e)
            if "Reference already exists" in error_msg:
                return f"Error: Branch '{branch_name}' already exists"
            return f"Error creating branch: {error_msg}"
    
    # Tool 3: compare_branches
    async def compare_branches_handler(arguments: dict) -> str:
        """Handle compare_branches tool calls."""
        owner = arguments.get("owner", "")
        repo = arguments.get("repo", "")
        base = arguments.get("base", "")
        head = arguments.get("head", "")
        
        if not owner or not repo:
            return "Error: 'owner' and 'repo' parameters are required"
        
        if not base or not head:
            return "Error: 'base' and 'head' parameters are required"
        
        logger.info(f"Comparing {base}...{head} in {owner}/{repo}")
        
        try:
            client = await get_client()
            
            endpoint = f"/repos/{owner}/{repo}/compare/{base}...{head}"
            comparison = await client._request("GET", endpoint)
            
            result_lines = [
                f"## Comparison: `{base}` → `{head}`",
                f"",
                f"### Summary",
                f"- **Ahead**: {comparison.get('ahead_by', 0)} commits",
                f"- **Behind**: {comparison.get('behind_by', 0)} commits",
                f"- **Total Commits**: {comparison.get('total_commits', 0)}",
                f"- **Changed Files**: {len(comparison.get('files', []))}",
                f""
            ]
            
            # Show commits
            commits = comparison.get('commits', [])
            if commits:
                result_lines.append(f"### Commits in {head}")
                for commit in commits[:10]:
                    result_lines.append(format_commit(commit, short=True))
                if len(commits) > 10:
                    result_lines.append(f"  ... and {len(commits) - 10} more commits")
                result_lines.append("")
            
            # Show changed files
            files = comparison.get('files', [])
            if files:
                result_lines.append(f"### Changed Files")
                for file_info in files[:20]:
                    result_lines.append(format_file_change(file_info))
                if len(files) > 20:
                    result_lines.append(f"  ... and {len(files) - 20} more files")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            error_msg = str(e)
            if "Not Found" in error_msg:
                return f"Error: One or both branches not found: {base} or {head}"
            return f"Error comparing branches: {error_msg}"
    
    # Create tool definitions
    list_commits_tool = types.Tool(
        name="list_commits",
        description="List recent commits in a GitHub repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "branch": {"type": "string", "description": "Branch name (optional)"},
                "per_page": {"type": "integer", "description": "Number of commits (1-100)", "default": 10}
            },
            "required": ["owner", "repo"]
        }
    )
    
    create_branch_tool = types.Tool(
        name="create_branch",
        description="Create a new branch in a GitHub repository.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "branch": {"type": "string", "description": "New branch name"},
                "source_branch": {"type": "string", "description": "Source branch", "default": "main"}
            },
            "required": ["owner", "repo", "branch"]
        }
    )
    
    compare_branches_tool = types.Tool(
        name="compare_branches",
        description="Compare two branches, commits, or tags.",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "base": {"type": "string", "description": "Base branch/commit"},
                "head": {"type": "string", "description": "Head branch/commit"}
            },
            "required": ["owner", "repo", "base", "head"]
        }
    )
    
    # Store handlers and definitions
    _tool_handlers["list_commits"] = list_commits_handler
    _tool_handlers["create_branch"] = create_branch_handler
    _tool_handlers["compare_branches"] = compare_branches_handler
    
    _tool_definitions = [list_commits_tool, create_branch_tool, compare_branches_tool]
    
    logger.info(f"Registered {len(_tool_handlers)} git operations tools")


def get_tool_handlers() -> Dict[str, Callable[[dict], Awaitable[str]]]:
    """Return dictionary of tool name to handler function."""
    return _tool_handlers


def get_tool_definitions() -> List[types.Tool]:
    """Return list of tool definitions."""
    return _tool_definitions
