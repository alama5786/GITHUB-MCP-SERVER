

import asyncio
import sys
from typing import List

# MCP SDK imports
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Local imports
from github_mcp.config import settings
from github_mcp.logging_config import setup_logging

# Import tool modules
from github_mcp.tools import hello, repositories, contents, git_operations, issues_prs

# Setup logging early
setup_logging(log_level=settings.log_level, log_format=settings.log_format)
import logging

logger = logging.getLogger(__name__)


class GitHubMCPServer:
    """Main MCP server managing tool registration and lifecycle."""
    
    def __init__(self):
        """Initialize MCP server with tool registry."""
        self.server = Server(settings.mcp_server_name)
        self.tool_handlers = {}  # Store tool name -> handler function
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register all tool modules with the MCP server."""
        logger.info("Registering tools...")
        
        # Register all tool modules
        hello.register_tools(self)
        repositories.register_tools(self)
        contents.register_tools(self)
        git_operations.register_tools(self)  # ADDED: Git operations tools
        issues_prs.register_tools(self)
        
        # Set up the list_tools handler
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """Return list of all registered tools."""
            tools = []
            
            # Get tools from all modules
            tools.extend(hello.get_tool_definitions())
            tools.extend(repositories.get_tool_definitions())
            tools.extend(contents.get_tool_definitions())
            tools.extend(git_operations.get_tool_definitions())  # ADDED
            tools.extend(issues_prs.get_tool_definitions())
            
            logger.info(f"Listing {len(tools)} tools")
            return tools
        
        # Set up the call_tool handler
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Route tool calls to appropriate handlers."""
            logger.info(f"Tool call received: {name}")
            
            # Check hello module
            if name in hello.get_tool_handlers():
                result = await hello.get_tool_handlers()[name](arguments)
                return [types.TextContent(type="text", text=result)]
            
            # Check repositories module
            if name in repositories.get_tool_handlers():
                result = await repositories.get_tool_handlers()[name](arguments)
                return [types.TextContent(type="text", text=result)]
            
            # Check contents module
            if name in contents.get_tool_handlers():
                result = await contents.get_tool_handlers()[name](arguments)
                return [types.TextContent(type="text", text=result)]
            
            # Check git_operations module (ADDED)
            if name in git_operations.get_tool_handlers():
                result = await git_operations.get_tool_handlers()[name](arguments)
                return [types.TextContent(type="text", text=result)]

            # Check issues_prs module
            if name in issues_prs.get_tool_handlers():
                result = await issues_prs.get_tool_handlers()[name](arguments)
                return [types.TextContent(type="text", text=result)]
            
            error_msg = f"Unknown tool: {name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        total_handlers = (
            len(hello.get_tool_handlers()) + 
            len(repositories.get_tool_handlers()) + 
            len(contents.get_tool_handlers()) +
            len(git_operations.get_tool_handlers()) +
            len(issues_prs.get_tool_handlers()) # ADDED
        )
        logger.info(f"Tool registration complete, registered {total_handlers} tool handlers")
    
    def add_tool_handler(self, tool_name: str, handler_func):
        """Add a tool handler to the registry."""
        self.tool_handlers[tool_name] = handler_func
        logger.debug(f"Added tool handler: {tool_name}")
    
    async def run(self) -> None:
        """Run the MCP server using STDIO transport."""
        logger.info(f"Starting {settings.mcp_server_name} v{settings.mcp_server_version}")
        logger.info(f"Log level: {settings.log_level}")
        
        try:
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=settings.mcp_server_name,
                        server_version=settings.mcp_server_version,
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )
        except Exception as e:
            logger.error(f"Error in server run: {e}", exc_info=True)
            raise
    
    def shutdown(self) -> None:
        """Clean shutdown procedure."""
        logger.info("Shutting down MCP server...")


async def main() -> None:
    """Main entry point for the MCP server."""
    server_instance = None
    try:
        server_instance = GitHubMCPServer()
        await server_instance.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        if server_instance:
            server_instance.shutdown()
            # Cleanup GitHub client
            try:
                from github_mcp.tools.contents import cleanup as cleanup_contents
                from github_mcp.tools.git_operations import cleanup as cleanup_git
                await cleanup_contents()
                await cleanup_git()
            except Exception as e:
                logger.debug(f"Cleanup error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
