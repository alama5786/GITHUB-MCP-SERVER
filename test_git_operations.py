

import asyncio
from github_mcp.tools import git_operations

class MockServer:
    pass

async def test_git_operations():
    """Test list_commits, create_branch, and compare_branches."""
    
    print("=== Testing Git Operations ===\n")
    
    # Register tools
    mock_server = MockServer()
    git_operations.register_tools(mock_server)
    handlers = git_operations.get_tool_handlers()
    
    OWNER = "alama5786"
    REPO = "mcp-test-files"
    
    # Test 1: List commits
    print("Test 1: Listing commits...")
    result = await handlers["list_commits"]({
        "owner": OWNER,
        "repo": REPO,
        "per_page": 5
    })
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Test 2: Create a new branch
    print("Test 2: Creating a new branch...")
    branch_name = "test/mcp-branch"
    result = await handlers["create_branch"]({
        "owner": OWNER,
        "repo": REPO,
        "branch": branch_name,
        "source_branch": "main"
    })
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Test 3: Compare branches (main vs new branch - should be identical)
    print("Test 3: Comparing main vs new branch...")
    result = await handlers["compare_branches"]({
        "owner": OWNER,
        "repo": REPO,
        "base": "main",
        "head": branch_name
    })
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Test 4: Create a file on the new branch (using direct client to demonstrate changes)
    print("Test 4: Creating a commit on the new branch...")
    from github_mcp.github import GitHubClient
    
    async with GitHubClient() as client:
        # Create a file on the new branch
        await client.create_or_update_file(
            owner=OWNER,
            repo=REPO,
            path="branch-test-file.md",
            content="# Branch Test\n\nThis file was created on the test branch.",
            message="test: Add file on branch",
            branch=branch_name
        )
        print(f"   ✓ File created on branch '{branch_name}'")
    
    print("\n" + "="*60 + "\n")
    
    # Test 5: Compare branches again (should show differences)
    print("Test 5: Comparing main vs new branch (after changes)...")
    result = await handlers["compare_branches"]({
        "owner": OWNER,
        "repo": REPO,
        "base": "main",
        "head": branch_name
    })
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Test 6: Validate branch name (invalid)
    print("Test 6: Testing invalid branch name...")
    result = await handlers["create_branch"]({
        "owner": OWNER,
        "repo": REPO,
        "branch": "bad/branch//name",
        "source_branch": "main"
    })
    print(result)

if __name__ == "__main__":
    print("🚀 GitHub MCP Server - Git Operations Test\n")
    print(f"This will create a branch and files in: alama5786/mcp-test-files\n")
    
    response = input("Continue with tests? (yes/no): ")
    if response.lower() == "yes":
        asyncio.run(test_git_operations())
    else:
        print("Test cancelled")