"""File content operations for GitHub repositories."""

import logging
import base64
from typing import Dict, Callable, Awaitable, Any, List, Optional

import mcp.types as types

from github_mcp.github import GitHubClient

logger = logging.getLogger(__name__)

# Store tool handlers and definitions
_tool_handlers: Dict[str, Callable[[dict], Awaitable[str]]] = {}
_tool_definitions: List[types.Tool] = []

# Global client reference for cleanup
github_client_instance: Optional[GitHubClient] = None


async def get_client() -> GitHubClient:
    """Lazy initialization of GitHub client."""
    global github_client_instance
    if github_client_instance is None:
        github_client_instance = GitHubClient()
        await github_client_instance.initialize()
        logger.info("GitHub client initialized for file operations")
    return github_client_instance


async def cleanup() -> None:
    """Clean up GitHub client resources."""
    global github_client_instance
    if github_client_instance:
        await github_client_instance.close()
        github_client_instance = None
        logger.info("GitHub client closed")


def register_tools(server) -> None:
    """Register file content tools with the MCP server.
    
    Args:
        server: MCP server instance (GitHubMCPServer) to register tools with
    """
    global _tool_handlers, _tool_definitions
    
    logger.info("Registering file content tools...")
    
    # Tool 1: read_file
    async def read_file_handler(arguments: dict) -> str:
        """Handle read_file tool calls."""
        owner = arguments.get("owner", "")
        repo = arguments.get("repo", "")
        path = arguments.get("path", "")
        branch = arguments.get("branch", None)
        
        # Validate required parameters
        if not owner:
            return "Error: 'owner' parameter is required (GitHub username or organization)"
        if not repo:
            return "Error: 'repo' parameter is required (repository name)"
        if not path:
            return "Error: 'path' parameter is required (file path in repository)"
        
        logger.info(f"Reading file {owner}/{repo}/{path} (branch: {branch or 'default'})")
        
        try:
            client = await get_client()
            file_info = await client.get_file_content(owner, repo, path, ref=branch)
            
            # Check if it's a file (not a directory)
            if file_info.type != "file":
                return f"Error: '{path}' is a {file_info.type}, not a file. Use directory listing tools to explore directories."
            
            # Decode content from base64
            if file_info.content:
                try:
                    decoded_content = base64.b64decode(file_info.content).decode('utf-8')
                except UnicodeDecodeError:
                    # Try with different encoding or handle binary files
                    decoded_content = f"[Binary file - {file_info.size} bytes - cannot display]"
            else:
                decoded_content = "[Empty file]"
            
            # Format response
            result_lines = [
                f"# File: {path}",
                f"**Repository**: {owner}/{repo}",
                f"**SHA**: {file_info.sha[:8]}...",
                f"**Size**: {file_info.size} bytes",
                f"**Branch**: {branch or 'default'}",
                f"",
                f"## Content",
                f"```",
                decoded_content,
                f"```"
            ]
            
            return "\n".join(result_lines)
            
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "Not Found" in error_msg:
                return f"File '{path}' not found in repository {owner}/{repo}" + (f" on branch '{branch}'" if branch else "")
            logger.error(f"Error reading file {owner}/{repo}/{path}: {e}", exc_info=True)
            return f"Error reading file: {error_msg}"
    
    # Tool 2: create_file
    async def create_file_handler(arguments: dict) -> str:
        """Handle create_file tool calls."""
        owner = arguments.get("owner", "")
        repo = arguments.get("repo", "")
        path = arguments.get("path", "")
        content = arguments.get("content", "")
        commit_message = arguments.get("commit_message", None)
        branch = arguments.get("branch", None)
        
        # Validate required parameters
        if not owner:
            return "Error: 'owner' parameter is required"
        if not repo:
            return "Error: 'repo' parameter is required"
        if not path:
            return "Error: 'path' parameter is required"
        if not content:
            return "Error: 'content' parameter is required (file content)"
        
        # Generate default commit message if not provided
        if not commit_message:
            commit_message = f"Create {path} via MCP server"
        
        logger.info(f"Creating file {owner}/{repo}/{path} (branch: {branch or 'default'})")
        
        try:
            client = await get_client()
            
            # First check if file already exists
            try:
                existing = await client.get_file_content(owner, repo, path, ref=branch)
                if existing:
                    return f"Error: File '{path}' already exists. Use update_file to modify existing files."
            except Exception as e:
                # 404 is expected - file doesn't exist
                if "404" not in str(e):
                    raise
            
            # Create the file
            result = await client.create_or_update_file(
                owner=owner,
                repo=repo,
                path=path,
                content=content,
                message=commit_message,
                branch=branch,
                sha=None  # No SHA for creation
            )
            
            # Format response
            result_lines = [
                f"✅ File created successfully!",
                f"",
                f"**Repository**: {owner}/{repo}",
                f"**Path**: {path}",
                f"**Branch**: {branch or 'default'}",
                f"**Commit**: {result.get('commit', {}).get('sha', 'unknown')[:8]}...",
                f"**Commit Message**: {commit_message}",
                f"",
                f"File has been created with {len(content)} characters."
            ]
            
            return "\n".join(result_lines)
            
        except Exception as e:
            error_msg = str(e)
            if "409" in error_msg or "Conflict" in error_msg:
                return f"Error: File '{path}' already exists. Use update_file to modify it."
            logger.error(f"Error creating file {owner}/{repo}/{path}: {e}", exc_info=True)
            return f"Error creating file: {error_msg}"
    
    # Tool 3: update_file
    async def update_file_handler(arguments: dict) -> str:
        """Handle update_file tool calls."""
        owner = arguments.get("owner", "")
        repo = arguments.get("repo", "")
        path = arguments.get("path", "")
        content = arguments.get("content", "")
        commit_message = arguments.get("commit_message", None)
        branch = arguments.get("branch", None)
        sha = arguments.get("sha", None)  # Optional SHA, will fetch if not provided
        
        # Validate required parameters
        if not owner:
            return "Error: 'owner' parameter is required"
        if not repo:
            return "Error: 'repo' parameter is required"
        if not path:
            return "Error: 'path' parameter is required"
        if not content:
            return "Error: 'content' parameter is required (new file content)"
        
        # Generate default commit message if not provided
        if not commit_message:
            commit_message = f"Update {path} via MCP server"
        
        logger.info(f"Updating file {owner}/{repo}/{path} (branch: {branch or 'default'})")
        
        try:
            client = await get_client()
            
            # If SHA not provided, fetch current file info to get SHA
            if not sha:
                try:
                    file_info = await client.get_file_content(owner, repo, path, ref=branch)
                    sha = file_info.sha
                    logger.info(f"Retrieved SHA {sha[:8]} for file {path}")
                except Exception as e:
                    if "404" in str(e):
                        return f"Error: File '{path}' does not exist. Use create_file to create new files."
                    raise
            
            # Update the file
            result = await client.create_or_update_file(
                owner=owner,
                repo=repo,
                path=path,
                content=content,
                message=commit_message,
                branch=branch,
                sha=sha
            )
            
            # Format response
            result_lines = [
                f"✅ File updated successfully!",
                f"",
                f"**Repository**: {owner}/{repo}",
                f"**Path**: {path}",
                f"**Branch**: {branch or 'default'}",
                f"**Commit**: {result.get('commit', {}).get('sha', 'unknown')[:8]}...",
                f"**Commit Message**: {commit_message}",
                f"**Old SHA**: {sha[:8]}...",
                f"**New Size**: {len(content)} characters"
            ]
            
            return "\n".join(result_lines)
            
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                return f"Error: File '{path}' not found. Use create_file to create it."
            elif "409" in error_msg:
                return f"Error: Conflict - file SHA mismatch. The file may have been modified elsewhere. Fetch the latest SHA and try again."
            logger.error(f"Error updating file {owner}/{repo}/{path}: {e}", exc_info=True)
            return f"Error updating file: {error_msg}"
    
    # Create tool definitions
    read_file_tool = types.Tool(
        name="read_file",
        description="Read the contents of a file from a GitHub repository. Use this to view configuration files, source code, documentation, or any text file in a repo.",
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
                "path": {
                    "type": "string",
                    "description": "Path to the file in the repository (e.g., 'README.md', 'src/main.py')"
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (optional, defaults to repository default branch)"
                }
            },
            "required": ["owner", "repo", "path"]
        }
    )
    
    create_file_tool = types.Tool(
        name="create_file",
        description="Create a new file in a GitHub repository. Use this to add documentation, configuration files, or source code. Fails if the file already exists to prevent accidental overwrites.",
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
                "path": {
                    "type": "string",
                    "description": "Path where the file should be created (e.g., 'docs/guide.md')"
                },
                "content": {
                    "type": "string",
                    "description": "File content as text"
                },
                "commit_message": {
                    "type": "string",
                    "description": "Commit message (optional, auto-generated if not provided)"
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (optional, defaults to repository default branch)"
                }
            },
            "required": ["owner", "repo", "path", "content"]
        }
    )
    
    update_file_tool = types.Tool(
        name="update_file",
        description="Update an existing file in a GitHub repository. Use this to modify configuration files, update documentation, or edit code. Requires the file's SHA to prevent conflicts.",
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
                "path": {
                    "type": "string",
                    "description": "Path to the file in the repository"
                },
                "content": {
                    "type": "string",
                    "description": "New file content"
                },
                "commit_message": {
                    "type": "string",
                    "description": "Commit message (optional, auto-generated if not provided)"
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (optional, defaults to repository default branch)"
                },
                "sha": {
                    "type": "string",
                    "description": "Current SHA of the file (optional, will be fetched automatically if not provided)"
                }
            },
            "required": ["owner", "repo", "path", "content"]
        }
    )
    
    # Store handlers
    _tool_handlers["read_file"] = read_file_handler
    _tool_handlers["create_file"] = create_file_handler
    _tool_handlers["update_file"] = update_file_handler
    
    # Store definitions
    _tool_definitions = [read_file_tool, create_file_tool, update_file_tool]
    
    logger.info(f"Registered {len(_tool_handlers)} file content tools")


def get_tool_handlers() -> Dict[str, Callable[[dict], Awaitable[str]]]:
    """Return dictionary of tool name to handler function."""
    return _tool_handlers


def get_tool_definitions() -> List[types.Tool]:
    """Return list of tool definitions."""
    return _tool_definitions