import asyncio
from github_mcp.tools import contents

# Mock server object for registration
class MockServer:
    def __init__(self):
        self.tools = []
    
    def add_tool_handler(self, name, handler):
        pass

async def test_file_operations():
    """Test create, read, and update operations."""
    
    print("=== Testing File Operations ===\n")
    
    # Register the tools first
    mock_server = MockServer()
    contents.register_tools(mock_server)
    
    # Get handlers after registration
    handlers = contents.get_tool_handlers()
    
    print(f"Available handlers: {list(handlers.keys())}")
    print()
    
    # Get your GitHub username from the earlier test
    OWNER = "alama5786"  # Your username
    REPO = "terraform-provider-mcps"  # Your existing repo
    
    # Test 1: Create a file
    print("Test 1: Creating a new file...")
    try:
        result = await handlers["create_file"]({
            "owner": OWNER,
            "repo": REPO,
            "path": "test-mcp-readme.md",
            "content": "# Test File\n\nThis is a test file created by MCP server.\n\nCreated for Phase 6 testing.",
            "commit_message": "Test: Create test-mcp-readme.md via MCP"
        })
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    print("\n" + "="*50 + "\n")
    
    # Test 2: Read the file
    print("Test 2: Reading the created file...")
    try:
        result = await handlers["read_file"]({
            "owner": OWNER,
            "repo": REPO,
            "path": "test-mcp-readme.md"
        })
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    print("\n" + "="*50 + "\n")
    
    # Test 3: Update the file
    print("Test 3: Updating the file...")
    try:
        result = await handlers["update_file"]({
            "owner": OWNER,
            "repo": REPO,
            "path": "test-mcp-readme.md",
            "content": "# Updated Test File\n\nThis file has been updated by MCP server!\n\n## New Section\n\nAdded some more content for testing.",
            "commit_message": "Test: Update test-mcp-readme.md via MCP"
        })
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    print("\n" + "="*50 + "\n")
    
    # Test 4: Read again to verify update
    print("Test 4: Reading updated file...")
    try:
        result = await handlers["read_file"]({
            "owner": OWNER,
            "repo": REPO,
            "path": "test-mcp-readme.md"
        })
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    print("\n" + "="*50 + "\n")
    
    # Test 5: Try to create same file again (should fail)
    print("Test 5: Attempting to create existing file (should fail)...")
    try:
        result = await handlers["create_file"]({
            "owner": OWNER,
            "repo": REPO,
            "path": "test-mcp-readme.md",
            "content": "This should fail"
        })
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 6: Try to read non-existent file
    print("\nTest 6: Reading non-existent file...")
    try:
        result = await handlers["read_file"]({
            "owner": OWNER,
            "repo": REPO,
            "path": "does-not-exist-12345.txt"
        })
        print(result)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing file operations on repository: alama5786/terraform-provider-mcps")
    print("This will create and modify files in your repository!\n")
    
    response = input("Continue with tests? (yes/no): ")
    if response.lower() == "yes":
        asyncio.run(test_file_operations())
    else:
        print("Test cancelled")
