"""Tests for inline command support in CLI."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from mcp_http_bridge.main import main_async
from mcp_http_bridge.models import BridgeSettings


@pytest.mark.asyncio
async def test_main_async_inline_command_simple():
    """Test providing an inline command instead of a config file."""
    cmd = "python -c 'print(42)'"
    with patch("sys.argv", ["mcp-http-bridge", "--command", cmd]):
        with patch(
            "mcp_http_bridge.main.run_server", new_callable=AsyncMock
        ) as mock_run:
            result = await main_async()
            assert result == 0
            mock_run.assert_called_once()
            called_path = mock_run.call_args.args[0]
            assert isinstance(called_path, Path)
            # Temp file should be deleted after main_async finishes
            assert not called_path.exists()
            mock_run.assert_called_with(
                called_path,
                BridgeSettings(
                    host="127.0.0.1", port=8000, path="/mcp", log_level="INFO"
                ),
                test_connection=True,
            )


@pytest.mark.asyncio
async def test_main_async_config_file_not_found():
    """If a non-existent config file is provided, error should be returned."""
    with (
        patch("sys.argv", ["mcp-http-bridge", "--config", "nonexistent-config.json"]),
        patch("builtins.print") as mock_print,
    ):
        result = await main_async()
        assert result == 1
        mock_print.assert_called_once()
        assert "Configuration file not found" in mock_print.call_args[0][0]
