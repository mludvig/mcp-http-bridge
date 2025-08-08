"""Tests for main entry point and CLI functionality."""

import argparse
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from mcp_http_bridge.main import main, main_async
from mcp_http_bridge.models import BridgeSettings


@pytest.fixture
def temp_config():
    """Create a temporary valid config file."""
    config_data = {"server": {"command": "python", "args": ["-c", "print('test')"]}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name

    yield config_path
    Path(config_path).unlink()


@pytest.mark.asyncio
async def test_main_async_minimal_args(temp_config):
    """Test main_async with minimal arguments."""
    with patch("sys.argv", ["mcp-http-bridge", "--config", temp_config]):
        with patch(
            "mcp_http_bridge.main.run_server", new_callable=AsyncMock
        ) as mock_run:
            result = await main_async()

            assert result == 0
            mock_run.assert_called_once()

            # Check the arguments passed to run_server - it uses keyword args
            mock_run.assert_called_with(
                Path(temp_config),
                BridgeSettings(
                    host="127.0.0.1", port=8000, path="/mcp/", log_level="INFO"
                ),
            )


@pytest.mark.asyncio
async def test_main_async_custom_args(temp_config):
    """Test main_async with custom arguments."""
    args = [
        "mcp-http-bridge",
        "--config",
        temp_config,
        "--host",
        "0.0.0.0",
        "--port",
        "9000",
        "--path",
        "/custom",
        "--log-level",
        "DEBUG",
    ]

    with patch("sys.argv", args):
        with patch(
            "mcp_http_bridge.main.run_server", new_callable=AsyncMock
        ) as mock_run:
            result = await main_async()

            assert result == 0
            mock_run.assert_called_once()

            # Check the arguments passed to run_server
            mock_run.assert_called_with(
                Path(temp_config),
                BridgeSettings(
                    host="0.0.0.0", port=9000, path="/custom", log_level="DEBUG"
                ),
            )


@pytest.mark.asyncio
async def test_main_async_config_not_found():
    """Test main_async with non-existent config file."""
    with patch("sys.argv", ["mcp-http-bridge", "--config", "nonexistent.json"]):
        with patch("builtins.print") as mock_print:
            result = await main_async()

            assert result == 1
            mock_print.assert_called_once()
            assert "Configuration file not found" in mock_print.call_args[0][0]


@pytest.mark.asyncio
async def test_main_async_server_error(temp_config):
    """Test main_async when server raises an error."""
    with patch("sys.argv", ["mcp-http-bridge", "--config", temp_config]):
        with patch(
            "mcp_http_bridge.main.run_server", new_callable=AsyncMock
        ) as mock_run:
            mock_run.side_effect = RuntimeError("Server failed")

            with pytest.raises(RuntimeError, match="Server failed"):
                await main_async()


def test_main_success():
    """Test main function with successful execution."""
    with patch(
        "mcp_http_bridge.main.main_async", new_callable=AsyncMock
    ) as mock_main_async:
        mock_main_async.return_value = 0

        result = main()
        assert result == 0


def test_main_keyboard_interrupt():
    """Test main function handling KeyboardInterrupt."""
    with patch(
        "mcp_http_bridge.main.main_async", new_callable=AsyncMock
    ) as mock_main_async:
        mock_main_async.side_effect = KeyboardInterrupt()

        with patch("mcp_http_bridge.main.logger") as mock_logger:
            result = main()

            assert result == 0
            mock_logger.info.assert_called_with("Shutdown requested by user")


def test_main_exception():
    """Test main function handling general exception."""
    with patch(
        "mcp_http_bridge.main.main_async", new_callable=AsyncMock
    ) as mock_main_async:
        mock_main_async.side_effect = RuntimeError("Test error")

        with patch("mcp_http_bridge.main.logger") as mock_logger:
            result = main()

            assert result == 1
            mock_logger.error.assert_called_with("Server failed: Test error")


def test_argument_parser_defaults():
    """Test argument parser with default values."""
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--path", default="/mcp")
    parser.add_argument("--log-level", default="INFO")

    args = parser.parse_args(["test.json"])

    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.path == "/mcp"
    assert args.log_level == "INFO"


def test_argument_parser_custom_values():
    """Test argument parser with custom values."""
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--path", default="/mcp")
    parser.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
    )

    args = parser.parse_args(
        [
            "test.json",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--path",
            "/custom",
            "--log-level",
            "DEBUG",
        ]
    )

    assert args.host == "0.0.0.0"
    assert args.port == 9000
    assert args.path == "/custom"
    assert args.log_level == "DEBUG"


@pytest.mark.asyncio
async def test_logging_setup(temp_config):
    """Test that logging is properly configured."""
    with patch(
        "sys.argv", ["mcp-http-bridge", "--config", temp_config, "--log-level", "DEBUG"]
    ):
        with patch("mcp_http_bridge.main.run_server", new_callable=AsyncMock):
            with patch("logging.basicConfig") as mock_logging:
                await main_async()

                mock_logging.assert_called_once()
                call_args = mock_logging.call_args[1]
                assert call_args["level"] == 10  # logging.DEBUG value
                assert "format" in call_args
