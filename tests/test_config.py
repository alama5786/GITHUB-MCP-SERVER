import os
import pytest
from github_mcp.config import Settings


def test_settings_load_from_env(monkeypatch):
    """Test that settings load from environment variables."""
    monkeypatch.setenv("GITHUB_TOKEN", "test_token_12345")
    monkeypatch.setenv("GITHUB_REQUEST_TIMEOUT", "60")
    
    settings = Settings()  # Re-loads from env
    
    assert settings.github_token == "test_token_12345"
    assert settings.github_request_timeout == 60


def test_settings_validation_fails_without_token():
    """Test that missing GitHub token raises validation error."""
    with pytest.raises(ValueError, match="Field required"):
        Settings(_env_file=None)  # Force no env file