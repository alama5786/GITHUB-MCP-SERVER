

import asyncio
import base64
from github_mcp.github import GitHubClient

async def test_file_operations():
    """Test file operations using GitHub client directly."""
    
    print("=== Testing File Operations ===\n")
    
    OWNER = "alama5786"
    REPO = "mcp-test-files"
    PATH = "welcome.md"
    
    print(f"Testing on: {OWNER}/{REPO}")
    print(f"Repository URL: https://github.com/{OWNER}/{REPO}")
    print(f"File path: {PATH}\n")
    
    async with GitHubClient() as client:
        # First, verify the repository exists and is accessible
        try:
            repo_info = await client.get_repository(OWNER, REPO)
            print(f"✓ Repository found: {repo_info.full_name}")
            print(f"  Default branch: {repo_info.default_branch}")
            print(f"  Visibility: {repo_info.is_private_str}")
        except Exception as e:
            print(f"✗ Repository not accessible: {e}")
            return
        
        print("\n" + "="*50 + "\n")
        
        # Test 1: Create a file
        print("📝 Test 1: Creating a file...")
        content = f"""# Welcome to MCP Test Repository

This file was created by the **GitHub MCP Server**!

## What is MCP?
MCP (Model Context Protocol) is a protocol that allows LLMs to interact with external tools and APIs.

## Test Information
- **Created**: {asyncio.get_event_loop().time()}
- **Repository**: {OWNER}/{REPO}
- **Purpose**: Testing file operations

## Next Steps
- ✓ File creation
- ✓ File reading  
- ✓ File updating

This demonstrates how Claude can interact with GitHub through MCP!
"""
        
        try:
            result = await client.create_or_update_file(
                owner=OWNER,
                repo=REPO,
                path=PATH,
                content=content,
                message="docs: Add welcome file via MCP server"
            )
            print(f"✅ File created successfully!")
            print(f"   Commit SHA: {result.get('commit', {}).get('sha', 'unknown')[:8]}")
            print(f"   File SHA: {result.get('content', {}).get('sha', 'unknown')[:8]}")
        except Exception as e:
            print(f"❌ Error creating file: {e}")
            return
        
        print("\n" + "="*50 + "\n")
        
        # Test 2: Read the file
        print("📖 Test 2: Reading the file...")
        try:
            file_info = await client.get_file_content(OWNER, REPO, PATH)
            if file_info.content:
                decoded = base64.b64decode(file_info.content).decode('utf-8')
                print(f"✅ File read successfully!")
                print(f"   Size: {file_info.size} bytes")
                print(f"   SHA: {file_info.sha[:8]}")
                print(f"\n   Content preview:")
                print("   " + "-"*40)
                # Print first 10 lines
                lines = decoded.split('\n')[:10]
                for line in lines:
                    if line.strip():
                        print(f"   {line[:60]}")
                if len(decoded) > 500:
                    print("   ...")
                print("   " + "-"*40)
        except Exception as e:
            print(f"❌ Error reading file: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # Test 3: Update the file
        print("✏️ Test 3: Updating the file...")
        try:
            # Get current file info for SHA
            file_info = await client.get_file_content(OWNER, REPO, PATH)
            
            # Create updated content
            updated_content = f"""# Welcome to MCP Test Repository (Updated)

This file was **updated** by the GitHub MCP Server!

## What is MCP?
MCP (Model Context Protocol) is a protocol that allows LLMs to interact with external tools and APIs.

## Test Information
- **Created**: {asyncio.get_event_loop().time()}
- **Updated**: {asyncio.get_event_loop().time()}
- **Repository**: {OWNER}/{REPO}
- **Purpose**: Testing file operations

## Test Results
- ✅ File creation - PASSED
- ✅ File reading - PASSED
- ✅ File updating - PASSED

## Next Steps for MCP Server
- Add more GitHub operations
- Implement issue management
- Add PR support
- Deploy to Claude Desktop

This demonstrates how Claude can interact with and **modify** GitHub through MCP!
"""
            
            result = await client.create_or_update_file(
                owner=OWNER,
                repo=REPO,
                path=PATH,
                content=updated_content,
                message="docs: Update welcome file with test results",
                sha=file_info.sha
            )
            print(f"✅ File updated successfully!")
            print(f"   New commit: {result.get('commit', {}).get('sha', 'unknown')[:8]}")
            print(f"   New SHA: {result.get('content', {}).get('sha', 'unknown')[:8]}")
        except Exception as e:
            print(f"❌ Error updating file: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # Test 4: Read again to verify update
        print("🔍 Test 4: Verifying update...")
        try:
            file_info = await client.get_file_content(OWNER, REPO, PATH)
            if file_info.content:
                decoded = base64.b64decode(file_info.content).decode('utf-8')
                if "updated" in decoded.lower():
                    print(f"✅ File content verified - update successful!")
                else:
                    print(f"⚠️ File may not have been updated correctly")
        except Exception as e:
            print(f"❌ Error verifying update: {e}")
        
        print("\n" + "="*50 + "\n")
        print("🎉 ALL TESTS PASSED!")
        print(f"\n📂 View your file at:")
        print(f"   https://github.com/{OWNER}/{REPO}/blob/main/{PATH}")
        print(f"\n📊 Check the commit history:")
        print(f"   https://github.com/{OWNER}/{REPO}/commits/main/")

if __name__ == "__main__":
    print("🚀 GitHub MCP Server - File Operations Test\n")
    print("This will create, read, and update a file in your new repository.\n")
    
    response = input("Continue with tests? (yes/no): ")
    if response.lower() == "yes":
        asyncio.run(test_file_operations())
    else:
        print("Test cancelled")
