# Team Deployment Guide for GitHub MCP Server

This guide covers different deployment strategies for distributing the GitHub MCP Server across your development team.

## Quick Start (For Individual Developers)

```bash
# 1. Clone the repository
git clone https://github.com/alama5786/GITHUB-MCP-SERVER.git
cd GITHUB-MCP-SERVER

# 2. Run the automated setup script
chmod +x setup.sh
./setup.sh

# 3. The script will:
#    - Check Python and Git installation
#    - Create virtual environment
#    - Install dependencies
#    - Prompt for GitHub token setup
#    - Configure VS Code
```

---

## Deployment Strategy 1: Individual Machine Setup (Recommended for Small Teams)

**Best for**: 2-10 developers, each with their own token

### Process

1. **Each developer clones the repo**:
   ```bash
   git clone https://github.com/alama5786/GITHUB-MCP-SERVER.git
   cd GITHUB-MCP-SERVER
   ```

2. **Each developer runs setup**:
   ```bash
   ./setup.sh
   ```

3. **Each developer creates their own token**:
   - GitHub Settings → Personal access tokens
   - Create token with scopes: `repo`, `read:org`, `read:user`
   - Store securely in environment variable or `.env` file

### Advantages
✅ Individual tokens for audit trails  
✅ Easy to revoke access per person  
✅ No shared credentials  
✅ Works offline (once set up)  

### Disadvantages
❌ Manual setup per developer  
❌ Need to manage token rotation  

### Setup Documentation Template

Create a file `docs/TEAM_SETUP_CHECKLIST.md`:

```markdown
# MCP Server Setup Checklist

## For Each Developer

- [ ] Install Python 3.11+
- [ ] Install Git
- [ ] Clone the repository: `git clone https://github.com/alama5786/GITHUB-MCP-SERVER.git`
- [ ] Run setup script: `./setup.sh`
- [ ] Create GitHub Personal Access Token at https://github.com/settings/tokens
- [ ] Set GITHUB_TOKEN in shell profile or .env file
- [ ] Restart VS Code
- [ ] Verify: Open Copilot Chat and test GitHub MCP tools

**Support**: Contact [Team Lead] with issues
```

---

## Deployment Strategy 2: Shared Server (For Larger Teams)

**Best for**: 10+ developers, shared infrastructure

### Architecture

```
┌─────────────────────────────┐
│   Central MCP Server        │
│   (Running on Linux VM)     │
│   Port: 8000                │
└─────────────────────────────┘
         ↑
    ┌────┴────┬────────┬────────┐
    ↓         ↓        ↓        ↓
 Dev 1    Dev 2     Dev 3    Dev 4
(VS Code) (VS Code) (VS Code) (VS Code)
```

### Installation on Central Server

1. **Install on server**:
   ```bash
   # SSH into server
   ssh deploy@mcp-server.company.local
   
   git clone https://github.com/alama5786/GITHUB-MCP-SERVER.git
   cd GITHUB-MCP-SERVER
   
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Setup as systemd service** (`/etc/systemd/system/mcp-server.service`):
   ```ini
   [Unit]
   Description=GitHub MCP Server
   After=network.target
   
   [Service]
   Type=simple
   User=mcp-server
   WorkingDirectory=/opt/github-mcp-server
   Environment="GITHUB_TOKEN=your_org_token_here"
   Environment="PYTHONUNBUFFERED=1"
   ExecStart=/opt/github-mcp-server/venv/bin/python -m github_mcp.server
   Restart=on-failure
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Start service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable mcp-server
   sudo systemctl start mcp-server
   sudo systemctl status mcp-server
   ```

### Client Configuration (Each Developer)

Add to `.vscode/settings.json`:

```json
{
  "github.copilot.advanced": {
    "mcp": {
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
  }
}
```

### Advantages
✅ Single point of management  
✅ Easy to update  
✅ Shared resources  
✅ Can be monitored/backed up  

### Disadvantages
❌ Single point of failure  
❌ All developers share token (audit trail)  
❌ Network dependency  
❌ Requires infrastructure  

---

## Deployment Strategy 3: Docker-based Deployment

**Best for**: Teams using container infrastructure (Kubernetes, Docker Compose)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/alama5786/GITHUB-MCP-SERVER.git .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m mcp-server
USER mcp-server

# Set environment
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Start MCP server
CMD ["python", "-m", "github_mcp.server"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      LOG_LEVEL: INFO
      LOG_FORMAT: json
    restart: unless-stopped
    networks:
      - mcp-network
    volumes:
      - mcp-logs:/app/logs

  # Optional: Monitor service
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

networks:
  mcp-network:
    driver: bridge

volumes:
  mcp-logs:
```

### Deploy to Kubernetes

Create `mcp-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: github-mcp-server
  labels:
    app: github-mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: github-mcp-server
  template:
    metadata:
      labels:
        app: github-mcp-server
    spec:
      containers:
      - name: mcp-server
        image: registry.company.local/github-mcp-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: github-mcp-secrets
              key: token
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: github-mcp-server
spec:
  selector:
    app: github-mcp-server
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: LoadBalancer
```

Deploy:
```bash
# Create secret
kubectl create secret generic github-mcp-secrets --from-literal=token=$GITHUB_TOKEN

# Deploy
kubectl apply -f mcp-deployment.yaml

# Check status
kubectl get pods
kubectl get service github-mcp-server
```

---

## Deployment Strategy 4: GitHub Codespaces (Cloud-based)

**Best for**: Distributed teams, no local setup required

### Setup in Codespaces

1. **Create `.devcontainer/devcontainer.json`**:
   ```json
   {
     "name": "GitHub MCP Server",
     "image": "mcr.microsoft.com/vscode/devcontainers/python:3.11",
     "features": {
       "ghcr.io/devcontainers/features/git:1": {}
     },
     "postCreateCommand": "bash setup.sh",
     "customizations": {
       "vscode": {
         "extensions": [
           "GitHub.copilot"
         ]
       }
     }
   }
   ```

2. **Developer workflow**:
   ```bash
   # Open in Codespaces from GitHub repo
   # Codespace automatically:
   # - Installs Python, Git, dependencies
   # - Runs setup.sh
   # - Configures VS Code
   ```

### Advantages
✅ No local setup required  
✅ Same environment for all developers  
✅ Cloud-based (works from anywhere)  
✅ Easy onboarding  

---

## Comparison Table

| Strategy | Setup | Maintenance | Scalability | Cost | Security |
|----------|-------|-------------|-------------|------|----------|
| Individual | Simple | High | Low | Low | High |
| Shared Server | Medium | Medium | Medium | Low | Medium |
| Docker | Medium | Low | High | Low | High |
| Kubernetes | Complex | Low | Very High | Medium | High |
| Codespaces | Simple | Low | Medium | High | High |

---

## Token Management Strategy

### For Individual Deployments

```bash
# Each developer creates token at https://github.com/settings/tokens

# Store securely in shell profile
echo 'export GITHUB_TOKEN="ghp_..."' >> ~/.zshrc

# Or in .env (NOT committed)
echo 'GITHUB_TOKEN=ghp_...' > .env
```

### For Team/Shared Deployments

**Option 1: Organization Token (Recommended)**
- Create at Organization Settings → Personal access tokens (beta)
- Share via secure secret manager (1Password, Vault, etc.)
- Rotate every 3-6 months

**Option 2: Shared Service Account**
```bash
# Create a GitHub user: github-mcp-bot
# Create token for that account
# Everyone uses same token (less ideal for audit)
```

**Option 3: OAuth2 Flow**
- Implement OAuth2 for developer auth
- Each developer signs in with GitHub account
- More complex but better for audit trails

---

## Monitoring & Maintenance

### Health Check Script

Create `health-check.sh`:

```bash
#!/bin/bash

# Test token validity
curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | jq '.login'

# Test MCP server connectivity
./start.sh &
sleep 2
kill %1

echo "✅ Health check passed"
```

### Token Rotation

Schedule monthly token rotations:

```bash
#!/bin/bash
# rotate-tokens.sh - Run monthly

echo "⚠️  Rotate GitHub tokens:"
echo "1. Create new token at https://github.com/settings/tokens"
echo "2. Update .env or environment variable"
echo "3. Restart all MCP servers"
echo "4. Revoke old token"
```

### Logging & Monitoring

Enable logging:
```json
{
  "LOG_LEVEL": "DEBUG",
  "LOG_FORMAT": "json"
}
```

Monitor logs:
```bash
# Real-time logs
tail -f logs/mcp-server.log

# JSON parsing
jq '.level, .message' logs/mcp-server.log
```

---

## Troubleshooting by Strategy

### Individual Setup Issues
- Python version: `python3 --version`
- Token: `echo $GITHUB_TOKEN`
- VS Code: Check `.vscode/settings.json` path

### Shared Server Issues
- Service status: `systemctl status mcp-server`
- Logs: `journalctl -u mcp-server -f`
- Network: `curl http://mcp-server.company.local:8000`

### Docker Issues
- Container logs: `docker logs mcp-server`
- Rebuild: `docker-compose build --no-cache`
- Port conflict: `lsof -i :8000`

### Kubernetes Issues
- Pod logs: `kubectl logs deployment/github-mcp-server`
- Describe: `kubectl describe pod <pod-name>`
- Events: `kubectl get events`

---

## Additional Resources

- [MCP Setup Guide](./MCP_SETUP_GUIDE.md)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication)
- [VS Code Settings](https://code.visualstudio.com/docs/getstarted/settings)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
