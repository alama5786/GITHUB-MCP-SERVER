"""Example hello world tool demonstrating MCP tool registration."""

import logging
from typing import Dict, Callable, Awaitable, Any

import mcp.types as types

logger = logging.getLogger(__name__)

# Store tool handlers globally for this module
_tool_handlers: Dict[str, Callable[[dict], Awaitable[str]]] = {}
_tool_definitions: list[types.Tool] = []


def register_tools(server) -> None:
    """Register hello world tools with the MCP server.
    
    Args:
        server: MCP server instance (GitHubMCPServer) to register tools with
    """
    global _tool_handlers, _tool_definitions
    
    logger.info("Registering hello module tools...")
    
    # Define tool 1: hello_world
    async def hello_world_handler(arguments: dict) -> str:
        """Handle hello_world tool calls."""
        name = arguments.get("name", "World")
        
        logger.info(f"hello_world called with name='{name}'")
        
        # Validate input
        if not name or len(str(name).strip()) == 0:
            return "Error: Name cannot be empty"
        
        # Clean the input
        name = str(name).strip()
        
        # Return friendly greeting
        greeting = f"Hello, {name}! Welcome to the GitHub MCP Server."
        
        logger.debug(f"Returning greeting: {greeting}")
        return greeting
    
    # Define tool 2: echo
    async def echo_handler(arguments: dict) -> str:
        """Handle echo tool calls."""
        message = arguments.get("message", "")
        uppercase = arguments.get("uppercase", False)
        
        logger.info(f"echo called with message='{message[:50] if message else ''}...', uppercase={uppercase}")
        
        if not message or len(str(message).strip()) == 0:
            return "Error: Message cannot be empty"
        
        result = str(message).strip()
        if uppercase:
            result = result.upper()
        
        return result
    
    # Create tool definitions
    hello_world_tool = types.Tool(
        name="hello_world",
        description="Say hello to someone. This demonstrates basic MCP tool functionality.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name to greet (defaults to 'World')"
                }
            },
            "required": []
        }
    )
    
    echo_tool = types.Tool(
        name="echo",
        description="Echo back a message with optional transformation to uppercase.",
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to echo back"
                },
                "uppercase": {
                    "type": "boolean",
                    "description": "Whether to convert message to uppercase",
                    "default": False
                }
            },
            "required": ["message"]
        }
    )
    
    # Store handlers
    _tool_handlers["hello_world"] = hello_world_handler
    _tool_handlers["echo"] = echo_handler
    
    # Store definitions
    _tool_definitions = [hello_world_tool, echo_tool]
    
    logger.info(f"Registered {len(_tool_handlers)} tools from hello module")


def get_tool_handlers() -> Dict[str, Callable[[dict], Awaitable[str]]]:
    """Return dictionary of tool name to handler function."""
    return _tool_handlers


def get_tool_definitions() -> list[types.Tool]:
    """Return list of tool definitions."""
    return _tool_definitions