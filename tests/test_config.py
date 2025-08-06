"""Tests for configuration handling."""

import json
import tempfile
from pathlib import Path
import pytest

from mcp_wrapper.config import ConfigManager
from mcp_wrapper.models import MCPWrapperConfig, WrapperSettings


def test_config_manager_load_valid_config():
    """Test loading a valid configuration."""
    config_data = {
        "server": {
            "command": "python",
            "args": ["test.py"],
            "env": {"TEST": "true"}
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name
    
    try:
        manager = ConfigManager(config_path)
        config = manager.load_config()
        
        assert isinstance(config, MCPWrapperConfig)
        assert config.server.command == "python"
        assert config.server.args == ["test.py"]
        assert config.server.env == {"TEST": "true"}
    finally:
        Path(config_path).unlink()


def test_config_manager_file_not_found():
    """Test behavior when config file doesn't exist."""
    manager = ConfigManager("nonexistent.json")
    
    with pytest.raises(FileNotFoundError):
        manager.load_config()


def test_config_manager_invalid_json():
    """Test behavior with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json content {")
        config_path = f.name
    
    try:
        manager = ConfigManager(config_path)
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            manager.load_config()
    finally:
        Path(config_path).unlink()


def test_wrapper_settings_defaults():
    """Test default wrapper settings."""
    settings = WrapperSettings()
    
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.path == "/mcp"
    assert settings.log_level == "INFO"


def test_wrapper_settings_overrides():
    """Test wrapper settings with overrides."""
    settings = WrapperSettings(
        host="0.0.0.0",
        port=9000,
        path="/custom",
        log_level="DEBUG"
    )
    
    assert settings.host == "0.0.0.0"
    assert settings.port == 9000
    assert settings.path == "/custom"
    assert settings.log_level == "DEBUG"


def test_config_manager_get_server_info():
    """Test getting server info from configuration."""
    config_data = {
        "server": {
            "command": "python",
            "args": ["server.py"],
            "env": {"NODE_ENV": "production"}
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name
    
    try:
        manager = ConfigManager(config_path)
        manager.load_config()
        server_info = manager.get_server_info()
        
        assert server_info["command"] == "python"
        assert server_info["args"] == ["server.py"]
        assert server_info["has_env"] is True
    finally:
        Path(config_path).unlink()
