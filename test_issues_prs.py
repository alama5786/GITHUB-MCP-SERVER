

import asyncio
from github_mcp.tools import issues_prs

class MockServer:
    pass

async def test_issues_prs():
    """Test create_issue, list_pull_requests, create_pull_request."""
    
    print("=== Testing Issues and Pull Requests ===\n")
    
    # Register tools
    mock_server = MockServer()
    issues_prs.register_tools(mock_server)
    handlers = issues_prs.get_tool_handlers()
    
    OWNER = "alama5786"
    REPO = "mcp-test-files"
    
    # Test 1: Create an issue
    print("Test 1: Creating an issue...")
    result = await handlers["create_issue"]({
        "owner": OWNER,
        "repo": REPO,
        "title": "Test MCP Integration",
        "body": "This is a test issue created by the MCP server.\n\n## Details\n- Created via API\n- Testing issue creation\n- Should be visible on GitHub",
        "labels": ["enhancement", "test"]
    })
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Test 2: List pull requests (should be empty initially)
    print("Test 2: Listing pull requests...")
    result = await handlers["list_pull_requests"]({
        "owner": OWNER,
        "repo": REPO,
        "state": "open"
    })
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Test 3: Create a pull request (using branch from Phase 7)
    print("Test 3: Creating a pull request...")
    result = await handlers["create_pull_request"]({
        "owner": OWNER,
        "repo": REPO,
        "title": "Add test file and documentation",
        "head": "test/mcp-branch",  # Branch created in Phase 7
        "base": "main",
        "body": "## Changes\n- Added branch-test-file.md\n- Testing PR creation via MCP\n\n## Testing\n- [x] File created correctly\n- [x] No merge conflicts\n\nCloses #1"  # Reference the issue we created
    })
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Test 4: List pull requests again (should show the new PR)
    print("Test 4: Listing pull requests after creation...")
    result = await handlers["list_pull_requests"]({
        "owner": OWNER,
        "repo": REPO,
        "state": "open"
    })
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Test 5: Test error handling
    print("Test 5: Error handling - invalid branch...")
    result = await handlers["create_pull_request"]({
        "owner": OWNER,
        "repo": REPO,
        "title": "Invalid PR",
        "head": "non-existent-branch",
        "base": "main"
    })
    print(result)

if __name__ == "__main__":
    print("🚀 GitHub MCP Server - Issues and PRs Test\n")
    print(f"This will create issues and PRs in: alama5786/mcp-test-files\n")
    
    response = input("Continue with tests? (yes/no): ")
    if response.lower() == "yes":
        asyncio.run(test_issues_prs())
    else:
        print("Test cancelled")
