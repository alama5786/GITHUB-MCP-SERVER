# GitHub MCP Server

A Model Context Protocol (MCP) server that provides GitHub API integration, enabling AI assistants to interact with GitHub repositories, issues, pull requests, and more.

## Overview

This project implements a MCP server that acts as a bridge between AI assistants (like Claude) and the GitHub API. It allows AI assistants to perform various GitHub operations such as:

- **Repository Management**: List, search, and get details about repositories
- **Content Operations**: Read files, get repository contents
- **Git Operations**: Clone repositories, perform git operations
- **Issue & PR Management**: Create, list, and manage issues and pull requests
- **Authentication**: Secure token-based authentication with GitHub

## Features

### 🔧 Core Tools

- **Repository Tools**: List repositories, get repository details, search repositories
- **Content Tools**: Read files, browse repository contents
- **Git Operations**: Clone, pull, push, and other git operations
- **Issue/PR Tools**: Create and manage issues and pull requests
- **Hello Tools**: Basic connectivity and testing tools

### 🔒 Security

- Secure GitHub Personal Access Token authentication
- Environment-based configuration
- No sensitive data stored in code
- GitHub's secret scanning protection

### 🚀 Performance

- Asynchronous HTTP requests using httpx
- Rate limiting and retry mechanisms
- Efficient API usage with proper pagination

## Installation

### Prerequisites

- Python 3.11 or higher
- GitHub Personal Access Token with appropriate permissions

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/alama5786/GITHUB-MCP-SERVER.git
   cd GITHUB-MCP-SERVER
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your GitHub token
   ```

5. **Run the server**:
   ```bash
   ./start.sh
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# GitHub Personal Access Token (required)
GITHUB_TOKEN=your_github_token_here

# API Configuration
GITHUB_API_BASE_URL=https://api.github.com
GITHUB_REQUEST_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### GitHub Token Setup

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Generate a new token with the following scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read org and team membership)
   - `read:user` (Read user profile data)
3. Copy the token and add it to your `.env` file

## Usage

### Starting the Server

The server can be started in two ways:

1. **Using the start script** (recommended):
   ```bash
   ./start.sh
   ```

2. **Manual execution**:
   ```bash
   source venv/bin/activate
   export PYTHONPATH="$PWD/src:$PYTHONPATH"
   python3 -m github_mcp.server
   ```

### Integration with AI Assistants

This MCP server is designed to work with AI assistants that support the Model Context Protocol. Configure your AI assistant to connect to this server for GitHub operations.

## Project Structure

```
src/github_mcp/
├── __init__.py
├── server.py              # Main MCP server implementation
├── config.py              # Configuration management
├── logging_config.py      # Logging setup
├── github/                # GitHub API client
│   ├── __init__.py
│   ├── client.py          # GitHub API client
│   ├── models.py          # Data models
│   ├── exceptions.py      # Custom exceptions
│   └── rate_limiter.py    # Rate limiting
├── tools/                 # MCP tool implementations
│   ├── __init__.py
│   ├── hello.py           # Basic tools
│   ├── repositories.py    # Repository operations
│   ├── contents.py        # Content operations
│   ├── git_operations.py  # Git operations
│   └── issues_prs.py      # Issues and PRs
└── utils/
    └── retry.py           # Retry utilities
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=github_mcp
```

### Code Quality

The project uses several tools for code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **MyPy**: Type checking

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type check
mypy src/
```

### Building

```bash
# Build the package
python -m build

# Install locally
pip install -e .
```

## API Reference

### Available Tools

#### Repository Tools
- `list_repositories`: List user's repositories
- `get_repository`: Get repository details
- `search_repositories`: Search for repositories

#### Content Tools
- `get_file_contents`: Read file contents
- `list_directory`: List directory contents

#### Git Operations
- `clone_repository`: Clone a repository
- `git_status`: Get git status
- `git_log`: Get commit history

#### Issue/PR Tools
- `list_issues`: List repository issues
- `create_issue`: Create a new issue
- `list_pull_requests`: List pull requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions:

1. Check the [Issues](https://github.com/alama5786/GITHUB-MCP-SERVER/issues) page
2. Create a new issue with detailed information
3. For security issues, please email the maintainers directly

## Changelog

### Version 0.1.0
- Initial release
- Basic GitHub API integration
- Repository, content, and issue management tools
- MCP protocol implementation
- Comprehensive test suite

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the protocol specification
- [GitHub REST API](https://docs.github.com/en/rest) for the underlying API
- All contributors and the open-source community