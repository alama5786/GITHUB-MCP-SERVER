#!/bin/bash
cd /Users/azizalam/Documents/Apps/GenAI/Claude_GithubMCP_Server/github-mcp-server
source venv/bin/activate
export PYTHONPATH="$PWD/src:$PYTHONPATH"
exec python3 -m github_mcp.server
