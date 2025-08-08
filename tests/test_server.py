"""Tests for server functionality."""

import json
import signal
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_http_bridge.models import BridgeSettings
from mcp_http_bridge.server import MCPBridgeServer, run_server


@pytest.fixture
def temp_config():
    """Create a temporary valid config file."""
    config_data = {
        "server": {
            "command": "python",
            "args": ["-c", "print('test')"],
            "env": {"TEST": "true"},
            "cwd": "/tmp",
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name

    yield config_path
    Path(config_path).unlink()


@pytest.fixture
def bridge_settings():
    """Create test bridge settings."""
    return BridgeSettings(host="127.0.0.1", port=8000, path="/mcp", log_level="INFO")


def test_server_init(temp_config):
    """Test MCPBridgeServer initialization."""
    server = MCPBridgeServer(temp_config)

    assert server.config_manager is not None
    assert server.proxy is None
    assert server._shutdown_event is not None


@pytest.mark.asyncio
async def test_setup_basic(temp_config):
    """Test basic server setup."""
    server = MCPBridgeServer(temp_config)

    with patch("mcp_http_bridge.server.FastMCP.as_proxy") as mock_proxy:
        mock_proxy_instance = MagicMock()
        mock_proxy.return_value = mock_proxy_instance

        with patch("mcp_http_bridge.server.StdioTransport") as mock_transport:
            mock_transport_instance = MagicMock()
            mock_transport.return_value = mock_transport_instance

            with patch("fastmcp.Client") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client.ping = AsyncMock()
                mock_client_class.return_value = mock_client

                await server.setup()

                # Verify transport was created with correct parameters
                mock_transport.assert_called_once_with(
                    command="python",
                    args=["-c", "print('test')"],
                    env={"TEST": "true"},
                    cwd="/tmp",
                )

                # Verify proxy was created
                mock_proxy.assert_called_once_with(
                    mock_transport_instance, name="MCP-HTTP-Bridge"
                )

                # Verify connection test was attempted
                mock_client.ping.assert_called_once()

                assert server.proxy is mock_proxy_instance


@pytest.mark.asyncio
async def test_setup_with_connection_timeout(temp_config):
    """Test server setup with connection timeout."""
    server = MCPBridgeServer(temp_config)

    with patch("mcp_http_bridge.server.FastMCP.as_proxy"):
        with patch("mcp_http_bridge.server.StdioTransport"):
            with patch("fastmcp.Client") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(side_effect=TimeoutError())
                mock_client_class.return_value = mock_client

                with patch("mcp_http_bridge.server.logger") as mock_logger:
                    # Should not raise exception, just log warning
                    await server.setup()

                    mock_logger.error.assert_called()
                    mock_logger.warning.assert_called()


@pytest.mark.asyncio
async def test_setup_with_connection_failure(temp_config):
    """Test server setup with connection failure."""
    server = MCPBridgeServer(temp_config)

    with patch("mcp_http_bridge.server.FastMCP.as_proxy"):
        with patch("mcp_http_bridge.server.StdioTransport"):
            with patch("fastmcp.Client") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(
                    side_effect=RuntimeError("Connection failed")
                )
                mock_client_class.return_value = mock_client

                with pytest.raises(RuntimeError, match="MCP server startup failed"):
                    await server.setup()


@pytest.mark.asyncio
async def test_test_connection_method(temp_config):
    """Test the _test_connection method."""
    server = MCPBridgeServer(temp_config)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.ping = AsyncMock()

    await server._test_connection(mock_client)

    mock_client.ping.assert_called_once()


@pytest.mark.asyncio
async def test_start_without_setup(temp_config):
    """Test starting server without setup."""
    server = MCPBridgeServer(temp_config)
    settings = BridgeSettings()

    with pytest.raises(RuntimeError, match="Server not setup"):
        await server.start(settings)


@pytest.mark.asyncio
async def test_start_with_setup(temp_config, bridge_settings):
    """Test starting server after setup."""
    server = MCPBridgeServer(temp_config)

    # Mock the proxy
    mock_proxy = AsyncMock()
    server.proxy = mock_proxy

    with patch("signal.signal") as mock_signal:
        # Mock run_async to avoid actually starting server
        mock_proxy.run_async = AsyncMock()

        await server.start(bridge_settings)

        # Verify signal handlers were set up
        assert mock_signal.call_count == 2

        # Verify proxy.run_async was called with correct parameters
        mock_proxy.run_async.assert_called_once_with(
            transport="http", host="127.0.0.1", port=8000, path="/mcp", log_level="info"
        )


@pytest.mark.asyncio
async def test_start_with_server_error(temp_config, bridge_settings):
    """Test starting server when proxy raises an error."""
    server = MCPBridgeServer(temp_config)

    mock_proxy = AsyncMock()
    mock_proxy.run_async = AsyncMock(side_effect=RuntimeError("Server error"))
    server.proxy = mock_proxy

    with patch("signal.signal"):
        with pytest.raises(RuntimeError, match="Server error"):
            await server.start(bridge_settings)


def test_signal_handler(temp_config):
    """Test signal handler functionality."""
    server = MCPBridgeServer(temp_config)

    # Initially, shutdown event should not be set
    assert not server._shutdown_event.is_set()

    # Call signal handler
    server._signal_handler(signal.SIGTERM, None)

    # Now shutdown event should be set
    assert server._shutdown_event.is_set()


@pytest.mark.asyncio
async def test_stop(temp_config):
    """Test server stop functionality."""
    server = MCPBridgeServer(temp_config)

    with patch("mcp_http_bridge.server.logger") as mock_logger:
        await server.stop()

        # Verify shutdown event is set and logging occurs
        assert server._shutdown_event.is_set()
        mock_logger.info.assert_called()


@pytest.mark.asyncio
async def test_run_server_success(temp_config, bridge_settings):
    """Test successful run_server function."""
    with patch("mcp_http_bridge.server.MCPBridgeServer") as mock_server_class:
        mock_server = AsyncMock()
        mock_server.setup = AsyncMock()
        mock_server.start = AsyncMock()
        mock_server.stop = AsyncMock()
        mock_server_class.return_value = mock_server

        await run_server(temp_config, bridge_settings)

        mock_server.setup.assert_called_once()
        mock_server.start.assert_called_once_with(bridge_settings)
        mock_server.stop.assert_called_once()


@pytest.mark.asyncio
async def test_run_server_setup_failure(temp_config, bridge_settings):
    """Test run_server when setup fails."""
    with patch("mcp_http_bridge.server.MCPBridgeServer") as mock_server_class:
        mock_server = AsyncMock()
        mock_server.setup = AsyncMock(side_effect=RuntimeError("Setup failed"))
        mock_server.stop = AsyncMock()
        mock_server_class.return_value = mock_server

        with pytest.raises(RuntimeError, match="Setup failed"):
            await run_server(temp_config, bridge_settings)

        # Ensure stop is called even on failure
        mock_server.stop.assert_called_once()


@pytest.mark.asyncio
async def test_run_server_start_failure(temp_config, bridge_settings):
    """Test run_server when start fails."""
    with patch("mcp_http_bridge.server.MCPBridgeServer") as mock_server_class:
        mock_server = AsyncMock()
        mock_server.setup = AsyncMock()
        mock_server.start = AsyncMock(side_effect=RuntimeError("Start failed"))
        mock_server.stop = AsyncMock()
        mock_server_class.return_value = mock_server

        with pytest.raises(RuntimeError, match="Start failed"):
            await run_server(temp_config, bridge_settings)

        mock_server.setup.assert_called_once()
        mock_server.stop.assert_called_once()


@pytest.mark.asyncio
async def test_setup_logs_server_info(temp_config):
    """Test that setup logs server information."""
    server = MCPBridgeServer(temp_config)

    with patch("fastmcp.FastMCP.as_proxy"):
        with patch("fastmcp.client.transports.StdioTransport"):
            with patch("fastmcp.Client") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client.ping = AsyncMock()
                mock_client_class.return_value = mock_client

                with patch("mcp_http_bridge.server.logger") as mock_logger:
                    await server.setup()

                    # Check that appropriate log messages were called
                    info_calls = [
                        call[0][0] for call in mock_logger.info.call_args_list
                    ]
                    assert any(
                        "Setting up proxy for MCP server" in msg for msg in info_calls
                    )
                    assert any(
                        "MCP HTTP bridge proxy setup complete" in msg
                        for msg in info_calls
                    )


@pytest.mark.asyncio
async def test_config_loading_during_setup(temp_config):
    """Test that configuration is properly loaded during setup."""
    server = MCPBridgeServer(temp_config)

    with patch("mcp_http_bridge.server.FastMCP.as_proxy"):
        with patch("mcp_http_bridge.server.StdioTransport") as mock_transport:
            with patch("fastmcp.Client") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client.ping = AsyncMock()
                mock_client_class.return_value = mock_client

                await server.setup()

                # Verify that the transport was created with values from config
                mock_transport.assert_called_once_with(
                    command="python",
                    args=["-c", "print('test')"],
                    env={"TEST": "true"},
                    cwd="/tmp",
                )
