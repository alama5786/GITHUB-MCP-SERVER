

import asyncio
import base64
from github_mcp.github import GitHubClient

async def test_direct_file_operations():
    """Test file operations using GitHub client directly."""
    
    print("=== Testing File Operations Directly ===\n")
    
    OWNER = "alama5786"
    REPO = "terraform-provider-mcps"  # Using your existing repo
    PATH = "test-direct-file.md"
    
    async with GitHubClient() as client:
        # Test 1: Create file
        print("Test 1: Creating file...")
        try:
            content = "# Direct Test\n\nThis file was created directly via GitHub client.\nCreated at: " + str(asyncio.get_event_loop().time())
            result = await client.create_or_update_file(
                owner=OWNER,
                repo=REPO,
                path=PATH,
                content=content,
                message="Direct test: Create file"
            )
            print(f"✓ File created! Commit: {result.get('commit', {}).get('sha', 'unknown')[:8]}")
        except Exception as e:
            print(f"Error creating file: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # Test 2: Read file
        print("Test 2: Reading file...")
        try:
            file_info = await client.get_file_content(OWNER, REPO, PATH)
            if file_info.content:
                decoded = base64.b64decode(file_info.content).decode('utf-8')
                print(f"✓ File content:\n{decoded[:200]}")
            else:
                print("File exists but has no content")
        except Exception as e:
            print(f"Error reading file: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # Test 3: Update file
        print("Test 3: Updating file...")
        try:
            # First get current SHA
            file_info = await client.get_file_content(OWNER, REPO, PATH)
            
            new_content = "# Updated Direct Test\n\nThis file has been updated!\n\nSecond line of content.\nUpdated at: " + str(asyncio.get_event_loop().time())
            result = await client.create_or_update_file(
                owner=OWNER,
                repo=REPO,
                path=PATH,
                content=new_content,
                message="Direct test: Update file",
                sha=file_info.sha
            )
            print(f"✓ File updated! New commit: {result.get('commit', {}).get('sha', 'unknown')[:8]}")
        except Exception as e:
            print(f"Error updating file: {e}")

if __name__ == "__main__":
    print("This test will create and modify files in your repository: alama5786/terraform-provider-mcps")
    print("\nWARNING: This will create a file named 'test-direct-file.md' in your repository")
    response = input("\nContinue? (yes/no): ")
    if response.lower() == "yes":
        asyncio.run(test_direct_file_operations())
    else:
        print("Cancelled")
