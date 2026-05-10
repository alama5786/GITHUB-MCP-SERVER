"""Repository-related MCP tools for GitHub."""

import logging
from typing import Dict, Callable, Awaitable, Any, List

import mcp.types as types

from github_mcp.github import GitHubClient, GitHubRepository

logger = logging.getLogger(__name__)

# Store tool handlers and definitions
_tool_handlers: Dict[str, Callable[[dict], Awaitable[str]]] = {}
_tool_definitions: List[types.Tool] = []


def register_tools(server) -> None:
    """Register repository tools with the MCP server.
    
    Args:
        server: MCP server instance (GitHubMCPServer) to register tools with
    """
    global _tool_handlers, _tool_definitions
    
    logger.info("Registering repository tools...")
    
    # Create a GitHub client instance (will be initialized when first used)
    github_client = None
    
    async def get_client() -> GitHubClient:
        """Lazy initialization of GitHub client."""
        nonlocal github_client
        if github_client is None:
            github_client = GitHubClient()
            await github_client.initialize()
        return github_client
    
    # Tool 1: list_repositories
    async def list_repositories_handler(arguments: dict) -> str:
        """Handle list_repositories tool calls."""
        visibility = arguments.get("visibility", "all")
        per_page = arguments.get("per_page", 30)
        
        # Validate visibility
        if visibility not in ["all", "public", "private"]:
            return f"Error: Invalid visibility '{visibility}'. Must be 'all', 'public', or 'private'."
        
        # Validate per_page
        if not isinstance(per_page, int) or per_page < 1 or per_page > 100:
            return f"Error: per_page must be an integer between 1 and 100, got {per_page}"
        
        logger.info(f"Listing repositories with visibility={visibility}, per_page={per_page}")
        
        try:
            client = await get_client()
            repos = await client.list_repositories(
                visibility=visibility,
                per_page=per_page
            )
            
            if not repos:
                return f"No {visibility} repositories found."
            
            # Format response as markdown
            result_lines = [
                f"## Found {len(repos)} {visibility} repositories\n"
            ]
            
            for repo in repos:
                # Format: - **[name](url)**: description (⭐ stars) - language
                stars = f"⭐ {repo.stargazers_count}" if repo.stargazers_count > 0 else "No stars"
                language = f" [{repo.language}]" if repo.language else ""
                
                line = f"- **[{repo.name}]({repo.html_url})**"
                if repo.description:
                    line += f": {repo.description[:100]}"
                line += f" ({stars}{language})"
                result_lines.append(line)
            
            # Add note about pagination if needed
            if len(repos) == per_page:
                result_lines.append(f"\n*Showing first {per_page} repositories. Use 'page' parameter to see more.*")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            logger.error(f"Error listing repositories: {e}", exc_info=True)
            return f"Error listing repositories: {str(e)}"
    
    # Tool 2: get_repository
    async def get_repository_handler(arguments: dict) -> str:
        """Handle get_repository tool calls."""
        owner = arguments.get("owner", "")
        repo_name = arguments.get("repo", "")
        
        # Validate required parameters
        if not owner:
            return "Error: 'owner' parameter is required (GitHub username or organization)"
        if not repo_name:
            return "Error: 'repo' parameter is required (repository name)"
        
        logger.info(f"Getting repository {owner}/{repo_name}")
        
        try:
            client = await get_client()
            repo = await client.get_repository(owner, repo_name)
            
            # Format detailed repository information
            result_lines = [
                f"# {repo.full_name}",
                f"**Description**: {repo.description or 'No description provided'}",
                f"**Visibility**: {repo.is_private_str}",
                f"**URL**: {repo.html_url}",
                f"",
                f"## Statistics",
                f"- ⭐ **Stars**: {repo.stargazers_count}",
                f"- 👀 **Watchers**: {repo.watchers_count}",
                f"- 🍴 **Forks**: {repo.forks_count}",
                f"- 🐛 **Open Issues**: {repo.open_issues_count}",
                f"- 📅 **Created**: {repo.created_at.strftime('%Y-%m-%d')}",
                f"- 🔄 **Last Pushed**: {repo.pushed_at.strftime('%Y-%m-%d')}",
                f"- 💻 **Language**: {repo.language or 'Not specified'}",
                f"- 📦 **Size**: {repo.size} KB",
                f"",
                f"## Default Branch",
                f"- 🌿 **Branch**: {repo.default_branch}",
            ]
            
            # Add owner information if available
            if repo.owner:
                result_lines.extend([
                    f"",
                    f"## Owner",
                    f"- **Username**: {repo.owner.login}",
                    f"- **Profile**: {repo.owner.html_url}"
                ])
            
            return "\n".join(result_lines)
            
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "Not Found" in error_msg:
                return f"Repository '{owner}/{repo_name}' not found. Please check the owner and repository name."
            logger.error(f"Error getting repository {owner}/{repo_name}: {e}", exc_info=True)
            return f"Error getting repository: {error_msg}"
    
    # Tool 3: search_repositories
    async def search_repositories_handler(arguments: dict) -> str:
        """Handle search_repositories tool calls."""
        query = arguments.get("query", "")
        per_page = arguments.get("per_page", 10)
        
        # Validate required parameters
        if not query:
            return "Error: 'query' parameter is required (search query string)"
        
        # Validate per_page
        if not isinstance(per_page, int) or per_page < 1 or per_page > 100:
            return f"Error: per_page must be an integer between 1 and 100, got {per_page}"
        
        logger.info(f"Searching repositories with query='{query}', per_page={per_page}")
        
        try:
            client = await get_client()
            repos = await client.search_repositories(query, per_page=per_page)
            
            if not repos:
                return f"No repositories found matching '{query}'."
            
            # Format response as markdown
            result_lines = [
                f"## Search Results for '{query}'",
                f"Found {len(repos)} repositories\n"
            ]
            
            for i, repo in enumerate(repos, 1):
                stars = f"⭐ {repo.stargazers_count}" if repo.stargazers_count > 0 else "No stars"
                language = f" [{repo.language}]" if repo.language else ""
                
                result_lines.append(f"### {i}. [{repo.full_name}]({repo.html_url})")
                if repo.description:
                    result_lines.append(f"   {repo.description[:150]}")
                result_lines.append(f"   {stars}{language} - Updated: {repo.updated_at.strftime('%Y-%m-%d')}")
                result_lines.append("")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            logger.error(f"Error searching repositories: {e}", exc_info=True)
            return f"Error searching repositories: {str(e)}"
    
    # Create tool definitions
    list_repos_tool = types.Tool(
        name="list_repositories",
        description="List GitHub repositories for the authenticated user. Use this to show the user their repositories, find a specific repo, or get an overview of their projects.",
        inputSchema={
            "type": "object",
            "properties": {
                "visibility": {
                    "type": "string",
                    "enum": ["all", "public", "private"],
                    "description": "Filter repositories by visibility. Default is 'all'.",
                    "default": "all"
                },
                "per_page": {
                    "type": "integer",
                    "description": "Number of results per page (1-100). Default is 30.",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 100
                }
            }
        }
    )
    
    get_repo_tool = types.Tool(
        name="get_repository",
        description="Get detailed information about a specific GitHub repository by owner and name. Use this when you need repository statistics, metadata, or configuration.",
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
                }
            },
            "required": ["owner", "repo"]
        }
    )
    
    search_repos_tool = types.Tool(
        name="search_repositories",
        description="Search GitHub repositories by query. Use this to discover repositories, find examples, or explore GitHub's ecosystem. Results are sorted by relevance.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (supports GitHub search syntax like 'language:python stars:>100')"
                },
                "per_page": {
                    "type": "integer",
                    "description": "Number of results per page (1-100). Default is 10.",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["query"]
        }
    )
    
    # Store handlers
    _tool_handlers["list_repositories"] = list_repositories_handler
    _tool_handlers["get_repository"] = get_repository_handler
    _tool_handlers["search_repositories"] = search_repositories_handler
    
    # Store definitions
    _tool_definitions = [list_repos_tool, get_repo_tool, search_repos_tool]
    
    logger.info(f"Registered {len(_tool_handlers)} repository tools")


def get_tool_handlers() -> Dict[str, Callable[[dict], Awaitable[str]]]:
    """Return dictionary of tool name to handler function."""
    return _tool_handlers


def get_tool_definitions() -> List[types.Tool]:
    """Return list of tool definitions."""
    return _tool_definitions


# Cleanup function for graceful shutdown
async def cleanup():
    """Clean up GitHub client resources."""
    global github_client_instance
    if github_client_instance:
        await github_client_instance.close()
        logger.info("GitHub client closed")

# Module-level client reference for cleanup
github_client_instance = None


async def get_client() -> GitHubClient:
    """Lazy initialization of GitHub client with cleanup tracking."""
    global github_client_instance
    if github_client_instance is None:
        github_client_instance = GitHubClient()
        await github_client_instance.initialize()
    return github_client_instance