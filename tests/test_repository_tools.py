#!/usr/bin/env python3
"""Test the repository MCP tools."""

import asyncio
import json
from github_mcp.tools.repositories import get_tool_handlers, get_tool_definitions
from github_mcp.github import GitHubClient

async def test_tools_directly():
    """Test repository tools by calling handlers directly."""
    
    print("=== Testing Repository Tools ===\n")
    
    # Get tool handlers
    handlers = get_tool_handlers()
    definitions = get_tool_definitions()
    
    print(f"Registered {len(handlers)} tools:")
    for tool_def in definitions:
        print(f"  - {tool_def.name}: {tool_def.description[:60]}...")
    
    print("\n" + "="*50 + "\n")
    
    # Test 1: List repositories
    print("Test 1: List repositories (all, per_page=3)")
    result = await handlers["list_repositories"]({"visibility": "all", "per_page": 3})
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Test 2: Get specific repository
    print("Test 2: Get repository details")
    result = await handlers["get_repository"]({"owner": "alama5786", "repo": "terraform-provider-mcps"})
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Test 3: Search repositories
    print("Test 3: Search for 'mcp python' repositories")
    result = await handlers["search_repositories"]({"query": "mcp python", "per_page": 3})
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Test 4: Error handling - invalid repo
    print("Test 4: Error handling - non-existent repository")
    result = await handlers["get_repository"]({"owner": "nonexistent", "repo": "invalid"})
    print(result)
    
    # Test 5: Error handling - missing parameters
    print("\nTest 5: Error handling - missing required parameter")
    result = await handlers["get_repository"]({"owner": "alama5786"})
    print(result)

async def test_with_client():
    """Alternative test using actual GitHub client."""
    print("\n=== Testing with Real GitHub Client ===\n")
    
    async with GitHubClient() as client:
        user = await client.get_current_user()
        print(f"Authenticated as: {user.login}")
        
        repos = await client.list_repositories(per_page=5)
        print(f"\nYour repositories:")
        for repo in repos:
            print(f"  - {repo.full_name} (⭐{repo.stargazers_count})")

if __name__ == "__main__":
    print("Choose test:")
    print("1. Test MCP tools directly")
    print("2. Test GitHub client only")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_tools_directly())
    elif choice == "2":
        asyncio.run(test_with_client())
    else:
        print("Invalid choice")