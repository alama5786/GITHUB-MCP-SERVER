"""Configuration management using Pydantic Settings."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # GitHub Configuration
    github_token: str = Field(..., description="GitHub Personal Access Token")
    github_api_base_url: str = Field(
        "https://api.github.com",
        description="Base URL for GitHub API"
    )
    github_request_timeout: int = Field(
        30,
        ge=1,
        le=120,
        description="HTTP request timeout in seconds"
    )
    
    # MCP Server Configuration
    mcp_server_name: str = Field("github-mcp-server", description="Server name")
    mcp_server_version: str = Field("0.1.0", description="Server version")
    
    # Logging Configuration
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field("json", description="Log format (json or text)")
    
    @field_validator("github_token")
    @classmethod
    def validate_github_token(cls, v: str) -> str:
        """Ensure GitHub token follows expected format."""
        if not v or len(v) < 10:
            raise ValueError("GitHub token must be at least 10 characters")
        return v
    
    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Ensure log format is valid."""
        if v not in ("json", "text"):
            raise ValueError("log_format must be 'json' or 'text'")
        return v


# Global settings instance
settings = Settings()