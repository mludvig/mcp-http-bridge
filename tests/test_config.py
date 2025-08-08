"""Tests for configuration handling."""

import json
import tempfile
from pathlib import Path

import pytest

from mcp_http_bridge.config import ConfigManager
from mcp_http_bridge.models import BridgeSettings, MCPBridgeConfig


def test_config_manager_load_valid_config():
    """Test loading a valid configuration."""
    config_data = {
        "server": {"command": "python", "args": ["test.py"], "env": {"TEST": "true"}}
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name

    try:
        manager = ConfigManager(config_path)
        config = manager.load_config()

        assert isinstance(config, MCPBridgeConfig)
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
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("invalid json content {")
        config_path = f.name

    try:
        manager = ConfigManager(config_path)

        with pytest.raises(ValueError, match="Invalid JSON"):
            manager.load_config()
    finally:
        Path(config_path).unlink()


def test_config_manager_invalid_schema():
    """Test behavior with invalid configuration schema."""
    config_data = {
        "server": {
            # Missing required 'command' field
            "args": ["test.py"]
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name

    try:
        manager = ConfigManager(config_path)

        with pytest.raises(ValueError, match="Failed to load config"):
            manager.load_config()
    finally:
        Path(config_path).unlink()


def test_config_property_without_loading():
    """Test accessing config property before loading."""
    manager = ConfigManager("test.json")

    with pytest.raises(RuntimeError, match="Configuration not loaded"):
        _ = manager.config


def test_config_property_after_loading():
    """Test accessing config property after loading."""
    config_data = {"server": {"command": "python", "args": ["test.py"]}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name

    try:
        manager = ConfigManager(config_path)
        loaded_config = manager.load_config()

        # Test that property returns the same config
        assert manager.config is loaded_config
        assert manager.config.server.command == "python"
    finally:
        Path(config_path).unlink()


def test_get_settings_defaults():
    """Test getting default settings."""
    manager = ConfigManager("test.json")
    settings = manager.get_settings()

    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.path == "/mcp"
    assert settings.log_level == "INFO"


def test_get_settings_with_overrides():
    """Test getting settings with overrides."""
    manager = ConfigManager("test.json")
    settings = manager.get_settings(host="0.0.0.0", port=9000, log_level="DEBUG")

    assert settings.host == "0.0.0.0"
    assert settings.port == 9000
    assert settings.path == "/mcp"  # Not overridden
    assert settings.log_level == "DEBUG"


def test_get_settings_cached():
    """Test that settings are cached properly."""
    manager = ConfigManager("test.json")
    settings1 = manager.get_settings()
    settings2 = manager.get_settings()

    # Should return the same instance when no overrides
    assert settings1 is settings2


def test_get_server_info_without_config():
    """Test getting server info without loaded config."""
    manager = ConfigManager("test.json")
    server_info = manager.get_server_info()

    assert server_info == {}


def test_get_server_info_with_minimal_config():
    """Test getting server info with minimal configuration."""
    config_data = {"server": {"command": "python"}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name

    try:
        manager = ConfigManager(config_path)
        manager.load_config()
        server_info = manager.get_server_info()

        assert server_info["command"] == "python"
        assert server_info["args"] == []
        assert server_info["has_env"] is False
        assert server_info["cwd"] is None
    finally:
        Path(config_path).unlink()


def test_bridge_settings_defaults():
    """Test default bridge settings."""
    settings = BridgeSettings()

    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.path == "/mcp"
    assert settings.log_level == "INFO"


def test_bridge_settings_overrides():
    """Test bridge settings with overrides."""
    settings = BridgeSettings(
        host="0.0.0.0", port=9000, path="/custom", log_level="DEBUG"
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
            "env": {"NODE_ENV": "production"},
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
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


def test_mcp_server_config_defaults():
    """Test MCPServerConfig with minimal data."""
    from mcp_http_bridge.models import MCPServerConfig

    config = MCPServerConfig(command="test")
    assert config.command == "test"
    assert config.args == []
    assert config.env is None
    assert config.cwd is None


def test_mcp_server_config_full():
    """Test MCPServerConfig with all fields."""
    from mcp_http_bridge.models import MCPServerConfig

    config = MCPServerConfig(
        command="python",
        args=["script.py", "--flag"],
        env={"VAR": "value"},
        cwd="/path/to/dir",
    )

    assert config.command == "python"
    assert config.args == ["script.py", "--flag"]
    assert config.env == {"VAR": "value"}
    assert config.cwd == "/path/to/dir"
