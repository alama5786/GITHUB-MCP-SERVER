import asyncio
import os
from github_mcp.github import GitHubClient
from github_mcp.config import settings

async def test_github_client():
    """Test basic GitHub client operations."""
    
    print("=== Testing GitHub Client ===\n")
    
    # Check if token is set
    if not settings.github_token or settings.github_token == "github_pat_xxxxxxxxxxxx":
        print("ERROR: Please set your GitHub token in .env file")
        print("Get a token from: https://github.com/settings/tokens")
        return
    
    async with GitHubClient() as client:
        # Test 1: Get current user
        print("Test 1: Getting current user...")
        user = await client.get_current_user()
        print(f"✓ Authenticated as: {user.login} ({user.name or 'No name'})")
        print(f"  Public repos: {user.public_repos}, Followers: {user.followers}\n")
        
        # Test 2: List repositories
        print("Test 2: Listing repositories...")
        repos = await client.list_repositories(per_page=5)
        print(f"✓ Found {len(repos)} repositories (showing first 5):")
        for repo in repos[:5]:
            print(f"  - {repo.full_name} ({repo.is_private_str}) - ⭐ {repo.stargazers_count}")
        print()
        
        # Test 3: Search repositories
        print("Test 3: Searching for 'mcp' repositories...")
        search_results = await client.search_repositories("mcp", per_page=3)
        print(f"✓ Found {len(search_results)} repositories:")
        for repo in search_results[:3]:
            print(f"  - {repo.full_name}: {repo.description[:50] if repo.description else 'No description'}...")
        
        print("\n✓ GitHub client tests passed!")

if __name__ == "__main__":
    asyncio.run(test_github_client())
