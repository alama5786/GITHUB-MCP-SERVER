

import asyncio
from github_mcp.github import GitHubClient

async def test_write_permission():
    """Test if token has write permission."""
    
    print("Testing GitHub token permissions...\n")
    
    async with GitHubClient() as client:
        # Check authentication
        user = await client.get_current_user()
        print(f"✓ Authenticated as: {user.login}")
        
        # Test write by creating a small test file
        test_repo = "mcp-test-files"
        test_path = "permission-test.txt"
        
        print(f"\nAttempting to create test file in: {user.login}/{test_repo}")
        
        try:
            result = await client.create_or_update_file(
                owner=user.login,
                repo=test_repo,
                path=test_path,
                content="This file tests write permissions. Created at: " + str(asyncio.get_event_loop().time()),
                message="test: Check write permissions"
            )
            print(f"✅ SUCCESS! Write permission confirmed!")
            print(f"   File created: https://github.com/{user.login}/{test_repo}/blob/main/{test_path}")
            print(f"   Commit: {result.get('commit', {}).get('sha', 'unknown')[:8]}")
            
        except Exception as e:
            print(f"❌ Write permission test failed: {e}")
            print("\nMake sure your token has the 'repo' scope enabled!")

if __name__ == "__main__":
    asyncio.run(test_write_permission())
