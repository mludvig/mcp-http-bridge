"""Tests for data models."""

import pytest
from pydantic import ValidationError

from mcp_http_bridge.models import BridgeSettings, MCPBridgeConfig, MCPServerConfig


def test_mcp_server_config_validation():
    """Test MCPServerConfig validation."""
    # Valid config
    config = MCPServerConfig(command="python")
    assert config.command == "python"
    assert config.args == []
    assert config.env is None
    assert config.cwd is None

    # Config with all fields
    config = MCPServerConfig(
        command="node",
        args=["script.js", "--verbose"],
        env={"NODE_ENV": "development"},
        cwd="/app",
    )
    assert config.command == "node"
    assert config.args == ["script.js", "--verbose"]
    assert config.env == {"NODE_ENV": "development"}
    assert config.cwd == "/app"


def test_mcp_server_config_missing_command():
    """Test MCPServerConfig with missing command."""
    with pytest.raises(ValidationError):
        MCPServerConfig()  # type: ignore


def test_mcp_bridge_config():
    """Test MCPBridgeConfig."""
    server_config = MCPServerConfig(command="python")
    config = MCPBridgeConfig(server=server_config)

    assert config.server is server_config
    assert config.server.command == "python"


def test_mcp_bridge_config_from_dict():
    """Test MCPBridgeConfig creation from dictionary."""
    config_dict = {
        "server": {"command": "python", "args": ["script.py"], "env": {"DEBUG": "1"}}
    }

    config = MCPBridgeConfig.model_validate(config_dict)
    assert config.server.command == "python"
    assert config.server.args == ["script.py"]
    assert config.server.env == {"DEBUG": "1"}


def test_bridge_settings_defaults():
    """Test BridgeSettings default values."""
    settings = BridgeSettings()

    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.path == "/mcp"
    assert settings.log_level == "INFO"


def test_bridge_settings_custom():
    """Test BridgeSettings with custom values."""
    settings = BridgeSettings(
        host="0.0.0.0", port=9000, path="/api/mcp", log_level="DEBUG"
    )

    assert settings.host == "0.0.0.0"
    assert settings.port == 9000
    assert settings.path == "/api/mcp"
    assert settings.log_level == "DEBUG"


def test_bridge_settings_model_dump():
    """Test BridgeSettings model_dump functionality."""
    settings = BridgeSettings(host="localhost", port=8080)
    dump = settings.model_dump()

    assert dump["host"] == "localhost"
    assert dump["port"] == 8080
    assert dump["path"] == "/mcp"
    assert dump["log_level"] == "INFO"


def test_server_config_field_descriptions():
    """Test that model fields have descriptions."""
    # This ensures the Field descriptions are accessible
    fields = MCPServerConfig.model_fields

    assert "command" in fields
    assert "args" in fields
    assert "env" in fields
    assert "cwd" in fields

    # Check that descriptions exist
    assert fields["command"].description is not None
    assert fields["args"].description is not None


def test_bridge_config_field_descriptions():
    """Test that BridgeSettings fields have descriptions."""
    fields = BridgeSettings.model_fields

    assert "host" in fields
    assert "port" in fields
    assert "path" in fields
    assert "log_level" in fields

    # Check that descriptions exist
    assert fields["host"].description is not None
    assert fields["port"].description is not None
