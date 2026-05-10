# MCP Server Setup Guide for Development Teams

This guide explains how to configure the GitHub MCP Server for multiple developers using GitHub Copilot in VS Code.

## Overview

The GitHub MCP Server can be set up on each developer's machine and integrated with GitHub Copilot in VS Code. This guide covers:

- Installing the MCP server locally
- Configuring VS Code to use the MCP server
- GitHub token management strategies
- Troubleshooting common issues

## Prerequisites

- **VS Code**: Latest version with GitHub Copilot extension installed
- **GitHub Copilot**: Active subscription
- **Python**: 3.11 or higher
- **Git**: For cloning the repository
- **GitHub Personal Access Token**: For API access

## Step 1: Install the MCP Server on Developer Machine

### Option A: Clone from GitHub (Recommended)

```bash
# Clone the repository
git clone https://github.com/alama5786/GITHUB-MCP-SERVER.git
cd GITHUB-MCP-SERVER

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option B: Use as a Package

```bash
# Install from GitHub directly
pip install git+https://github.com/alama5786/GITHUB-MCP-SERVER.git

# Or install from PyPI (when published)
pip install github-mcp-server
```

## Step 2: Configure GitHub Token

### Strategy 1: Individual Personal Access Tokens (Recommended)

Each developer should create their own GitHub Personal Access Token:

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Name: `GitHub MCP Server - [Your Name]`
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `read:org` (Read org and team membership)
   - ✅ `read:user` (Read user profile data)
5. Copy and store the token securely

### Strategy 2: Organization Token (For Teams)

If your organization uses GitHub Enterprise:

1. Go to **Organization Settings > Developer settings > Personal access tokens**
2. Create an organization token with appropriate scopes
3. Share securely with developers (e.g., via 1Password, Vault, or similar)

### Best Practices for Token Management

```
✅ DO:
- Create separate tokens per developer for audit trails
- Use tokens with minimal required scopes
- Rotate tokens regularly (every 3-6 months)
- Store tokens in secure secret managers
- Use environment variables or `.env` files (NOT committed to git)

❌ DON'T:
- Share a single token across the team
- Commit tokens to version control
- Use tokens with unnecessary permissions
- Store tokens in plain text files
```

## Step 3: Configure VS Code MCP Server

### Method 1: Using VS Code Settings (Easiest)

1. **Open VS Code Settings**:
   - Mac: `Cmd + ,`
   - Windows/Linux: `Ctrl + ,`

2. **Search for "MCP"** in settings

3. **Find GitHub Copilot settings** and locate MCP server configuration

4. **Add the MCP server configuration**:
   ```json
   {
     "servers": {
       "github-mcp-server": {
         "type": "stdio",
         "command": "/bin/bash",
         "args": [
           "${workspaceFolder}/github-mcp-server/start.sh"
         ],
         "env": {
           "GITHUB_TOKEN": "${env:GITHUB_TOKEN}",
           "GITHUB_API_BASE_URL": "https://api.github.com",
           "GITHUB_REQUEST_TIMEOUT": "30",
           "LOG_LEVEL": "INFO",
           "LOG_FORMAT": "json"
         }
       }
     }
   }
   ```

### Method 2: Using MCP Settings File

Create or edit `.vscode/settings.json` in your workspace:

```json
{
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
        "github-mcp-server": {
          "type": "stdio",
          "command": "/bin/bash",
          "args": [
            "${workspaceFolder}/github-mcp-server/start.sh"
          ],
          "env": {
            "GITHUB_TOKEN": "${env:GITHUB_TOKEN}",
            "GITHUB_API_BASE_URL": "https://api.github.com",
            "GITHUB_REQUEST_TIMEOUT": "30",
            "LOG_LEVEL": "INFO",
            "LOG_FORMAT": "json"
          }
        }
      }
    }
  }
}
```

### Method 3: Using Global MCP Configuration

Create `~/.config/Claude/mcp.json` (macOS/Linux) or `%APPDATA%\Claude\mcp.json` (Windows):

```json
{
  "servers": {
    "github-mcp-server": {
      "type": "stdio",
      "command": "/bin/bash",
      "args": [
        "/path/to/github-mcp-server/start.sh"
      ],
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}",
        "GITHUB_API_BASE_URL": "https://api.github.com",
        "GITHUB_REQUEST_TIMEOUT": "30",
        "LOG_LEVEL": "INFO",
        "LOG_FORMAT": "json"
      }
    }
  }
}
```

## Step 4: Set GitHub Token Environment Variable

### Option A: Shell Profile (Recommended)

Add to `~/.bash_profile`, `~/.zshrc`, or `~/.bashrc`:

```bash
export GITHUB_TOKEN="your_personal_access_token_here"
```

Then reload:
```bash
source ~/.zshrc  # or ~/.bash_profile on older macOS
```

### Option B: Using .env File

Create `.env` file in the MCP server directory:

```env
GITHUB_TOKEN=your_personal_access_token_here
GITHUB_API_BASE_URL=https://api.github.com
GITHUB_REQUEST_TIMEOUT=30
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**⚠️ Important**: Never commit `.env` file to git. Add to `.gitignore`:

```bash
.env
.env.local
```

### Option C: VS Code Environment (Not Recommended)

If storing in VS Code settings, use secure storage:

1. Open VS Code settings
2. Add to workspace settings (`.vscode/settings.json`):
   ```json
   {
     "github.copilot.mcp.github-mcp-server.env": {
       "GITHUB_TOKEN": "your_personal_access_token_here"
     }
   }
   ```

## Step 5: Verify Installation

### Test 1: Check MCP Server is Running

```bash
# From the MCP server directory
./start.sh

# You should see output indicating the server started
```

### Test 2: Check GitHub Token Access

```python
# Create test script: test_token.py
import os
from github_mcp.github.client import GitHubClient

token = os.getenv("GITHUB_TOKEN")
if not token:
    print("❌ GITHUB_TOKEN not set")
else:
    print(f"✅ Token found: {token[:20]}...")
    
    # Try to get user info
    async def test():
        client = GitHubClient(token)
        try:
            user = await client.get_authenticated_user()
            print(f"✅ Successfully authenticated as: {user}")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
    
    import asyncio
    asyncio.run(test())
```

Run it:
```bash
python test_token.py
```

### Test 3: Verify VS Code Integration

1. Open GitHub Copilot Chat in VS Code
2. Ask: "What GitHub tools are available?"
3. If configured correctly, Copilot should list the MCP tools

## Team Setup Checklist

For each developer, ensure:

- [ ] Python 3.11+ is installed
- [ ] Git is installed
- [ ] MCP server is cloned/installed
- [ ] Virtual environment is created
- [ ] Dependencies are installed (`pip install -r requirements.txt`)
- [ ] GitHub Personal Access Token is created
- [ ] Token is set in environment variables
- [ ] VS Code MCP configuration is added
- [ ] GitHub Copilot extension is installed and active
- [ ] MCP server connectivity is tested

## Common Configuration Scenarios

### Scenario 1: Centralized Server (For Teams)

All developers point to a single MCP server running on a central machine:

```json
{
  "servers": {
    "github-mcp-server": {
      "type": "http",
      "url": "http://mcp-server.company.local:8000",
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

### Scenario 2: Multiple Project Workspaces

If developers work on multiple projects:

1. **Create per-workspace MCP servers**:
   ```
   project1/.vscode/settings.json
   project2/.vscode/settings.json
   ```

2. **Each workspace points to its server**:
   ```json
   {
     "servers": {
       "github-mcp-project": {
        "type": "stdio",
         "command": "/bin/bash",
         "args": ["${workspaceFolder}/../github-mcp-server/start.sh"]
       }
     }
   }
   ```

### Scenario 3: Docker-based Deployment

Use Docker to ensure consistency:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN git clone https://github.com/alama5786/GITHUB-MCP-SERVER.git
RUN cd GITHUB-MCP-SERVER && pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "github_mcp.server"]
```

## Troubleshooting

### Issue: "MCP Server not found"

**Solution**:
1. Verify path to `start.sh` is correct
2. Check that `${workspaceFolder}` is resolving correctly
3. Try absolute path instead:
   ```json
   "args": ["/absolute/path/to/start.sh"]
   ```

### Issue: "GITHUB_TOKEN not set"

**Solution**:
```bash
# Check if token is in environment
echo $GITHUB_TOKEN

# If empty, set it
export GITHUB_TOKEN="your_token_here"

# Or reload shell profile
source ~/.zshrc
```

### Issue: "Authentication failed"

**Solution**:
1. Verify token is valid and not expired
2. Check token has required scopes (repo, read:org, read:user)
3. Test with curl:
   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   ```

### Issue: VS Code not connecting to MCP server

**Solution**:
1. Check VS Code output panel for errors
2. Restart VS Code
3. Run `./start.sh` manually to check for errors
4. Verify Python and dependencies are installed

## Security Best Practices

1. **Never commit tokens**: Always use `.env` files and `.gitignore`
2. **Rotate tokens regularly**: Every 3-6 months
3. **Use minimal scopes**: Only grant necessary permissions
4. **Audit token usage**: GitHub shows last used date
5. **Revoke old tokens**: Remove unused tokens
6. **Use secret managers**: 1Password, Vault, AWS Secrets Manager
7. **Monitor API usage**: Check GitHub settings for unusual activity

## Documentation References

- [GitHub MCP Server Repository](https://github.com/alama5786/GITHUB-MCP-SERVER)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub Copilot MCP Integration](https://github.com/features/copilot)
- [VS Code Settings Reference](https://code.visualstudio.com/docs/getstarted/settings)

## Support

For issues or questions:

1. Check this guide again
2. Review [GitHub MCP Server Issues](https://github.com/alama5786/GITHUB-MCP-SERVER/issues)
3. Contact the development team or create an issue
