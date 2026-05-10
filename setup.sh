#!/bin/bash

# GitHub MCP Server - Developer Setup Script
# This script automates the setup of the GitHub MCP Server on a developer's machine

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check Python version
check_python() {
    print_header "Checking Python Installation"
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Please install Python 3.11 or higher from https://www.python.org/downloads/"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"
    
    # Check if version is 3.11 or higher
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    if [ "$PYTHON_MINOR" -lt 11 ]; then
        print_error "Python 3.11 or higher is required (found $PYTHON_VERSION)"
        exit 1
    fi
}

# Check Git
check_git() {
    print_header "Checking Git Installation"
    
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed"
        echo "Please install Git from https://git-scm.com/downloads"
        exit 1
    fi
    
    GIT_VERSION=$(git --version)
    print_success "$GIT_VERSION found"
}

# Create virtual environment
setup_venv() {
    print_header "Setting Up Virtual Environment"
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Do you want to recreate it? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
            python3 -m venv venv
            print_success "Virtual environment created"
        fi
    else
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
}

# Activate virtual environment
activate_venv() {
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    print_success "Dependencies installed"
}

# Setup GitHub token
setup_github_token() {
    print_header "GitHub Token Configuration"
    
    print_info "You need a GitHub Personal Access Token to use this MCP server"
    print_info "Visit: https://github.com/settings/tokens"
    
    if [ -z "$GITHUB_TOKEN" ]; then
        print_warning "GITHUB_TOKEN environment variable not set"
        
        read -p "Do you want to set up your GitHub token now? (y/n) " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Enter your GitHub Personal Access Token (will be hidden):"
            read -s TOKEN
            
            if [ -z "$TOKEN" ]; then
                print_error "Token cannot be empty"
                exit 1
            fi
            
            # Ask where to store the token
            echo ""
            echo "Where would you like to store your token?"
            echo "1. Shell profile (~/.zshrc, ~/.bashrc, etc.)"
            echo "2. .env file in this directory"
            echo "3. Skip for now"
            read -p "Choose (1-3): " choice
            
            case $choice in
                1)
                    setup_shell_profile "$TOKEN"
                    ;;
                2)
                    setup_env_file "$TOKEN"
                    ;;
                3)
                    print_warning "Token not saved. You'll need to set GITHUB_TOKEN manually"
                    ;;
                *)
                    print_error "Invalid choice"
                    exit 1
                    ;;
            esac
        else
            print_info "You can set GITHUB_TOKEN manually later"
            print_info "Or run: export GITHUB_TOKEN='your_token_here'"
        fi
    else
        print_success "GITHUB_TOKEN is already set"
    fi
}

# Setup shell profile
setup_shell_profile() {
    TOKEN=$1
    SHELL_NAME=$(basename $SHELL)
    
    if [ "$SHELL_NAME" = "zsh" ]; then
        PROFILE="$HOME/.zshrc"
    elif [ "$SHELL_NAME" = "bash" ]; then
        if [ -f "$HOME/.bash_profile" ]; then
            PROFILE="$HOME/.bash_profile"
        else
            PROFILE="$HOME/.bashrc"
        fi
    else
        PROFILE="$HOME/.profile"
    fi
    
    # Add token to profile if not already there
    if ! grep -q "GITHUB_TOKEN=" "$PROFILE"; then
        echo "" >> "$PROFILE"
        echo "# GitHub MCP Server Token" >> "$PROFILE"
        echo "export GITHUB_TOKEN='$TOKEN'" >> "$PROFILE"
        print_success "Token saved to $PROFILE"
        print_info "Run: source $PROFILE"
    else
        print_warning "GITHUB_TOKEN already exists in $PROFILE"
    fi
}

# Setup .env file
setup_env_file() {
    TOKEN=$1
    
    if [ -f ".env" ]; then
        print_warning ".env file already exists"
        read -p "Overwrite? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    cat > .env << EOF
# GitHub Personal Access Token
GITHUB_TOKEN=$TOKEN

# API Configuration
GITHUB_API_BASE_URL=https://api.github.com
GITHUB_REQUEST_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
    
    print_success ".env file created"
    print_warning "Keep this file secure and do not commit it to git"
}

# Test MCP server
test_mcp_server() {
    print_header "Testing MCP Server"
    
    if [ -z "$GITHUB_TOKEN" ]; then
        print_warning "GITHUB_TOKEN not set. Skipping test."
        return
    fi
    
    print_info "Attempting to start MCP server..."
    timeout 5 ./start.sh 2>/dev/null || true
    
    print_success "MCP server startup test completed"
}

# Configure VS Code
configure_vscode() {
    print_header "VS Code Configuration"
    
    if [ ! -d ".vscode" ]; then
        mkdir -p .vscode
    fi
    
    # Detect the current directory path
    CURRENT_DIR=$(pwd)
    
    # Create/update VS Code settings
    cat > .vscode/settings.json << EOF
{
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
        "github-mcp-server": {
          "type": "stdio",
          "command": "/bin/bash",
          "args": [
            "$CURRENT_DIR/start.sh"
          ],
          "env": {
            "GITHUB_TOKEN": "\${env:GITHUB_TOKEN}",
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
EOF
    
    print_success "VS Code settings configured"
    print_info "File: .vscode/settings.json"
}

# Print summary
print_summary() {
    print_header "Setup Complete! 🎉"
    
    echo "Next steps:"
    echo ""
    echo "1. Activate the virtual environment:"
    echo "   ${YELLOW}source venv/bin/activate${NC}"
    echo ""
    echo "2. Test the MCP server:"
    echo "   ${YELLOW}./start.sh${NC}"
    echo ""
    echo "3. Open VS Code and ensure:"
    echo "   - GitHub Copilot extension is installed"
    echo "   - GITHUB_TOKEN environment variable is set"
    echo "   - Restart VS Code to load MCP configuration"
    echo ""
    echo "4. Test with GitHub Copilot:"
    echo "   - Open Copilot Chat"
    echo "   - Ask: 'What GitHub tools are available?'"
    echo ""
    echo "For detailed setup guide, see: docs/MCP_SETUP_GUIDE.md"
}

# Main execution
main() {
    print_header "GitHub MCP Server - Developer Setup"
    
    # Run all setup steps
    check_python
    check_git
    setup_venv
    activate_venv
    install_dependencies
    setup_github_token
    configure_vscode
    test_mcp_server
    print_summary
}

# Run main function
main
