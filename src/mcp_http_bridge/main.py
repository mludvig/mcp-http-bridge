"""Main entry point for MCP HTTP Bridge.

Enhancement: Allow providing an inline MCP server command instead of a JSON
configuration file. If the positional argument refers to an existing file it
is treated as before. Otherwise (and if it does not end with .json) it is
interpreted as a shell command line which is converted into an ephemeral
configuration file internally.
"""

import argparse
import asyncio
import json
import logging
import shlex
import tempfile
from pathlib import Path

from .models import BridgeSettings
from .server import run_server

logger = logging.getLogger(__name__)


async def main_async():
    """Async main function."""
    parser = argparse.ArgumentParser(
        description="MCP HTTP Bridge - Expose stdio MCP servers via HTTP"
    )

    # Create a mutually exclusive group for config vs command
    config_group = parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument(
        "--config",
        help="Path to the MCP configuration file (JSON format)",
        metavar="FILE",
    )
    config_group.add_argument(
        "--command",
        help="Inline MCP server command to run (e.g., 'uvx mcp-server-time --local-timezone=UTC')",
        metavar="CMD",
    )

    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )

    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )

    parser.add_argument(
        "--path", default="/mcp", help="Base path for MCP endpoints (default: /mcp)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--no-test-connection",
        action="store_true",
        help="Skip testing MCP server connection during startup (default: test connection)",
    )

    args = parser.parse_args()

    # Handle config file vs inline command
    inline_temp_file: Path | None = None

    if args.config:
        # Use provided config file
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Configuration file not found: {config_path}")
            return 1
    else:
        # Use inline command
        parts = shlex.split(args.command)
        if not parts:
            print("Error: Empty inline command specified")
            return 1
        command, *cmd_args = parts
        inline_config = {"server": {"command": command, "args": cmd_args}}

        # Create a temporary file holding the generated config
        tmp = tempfile.NamedTemporaryFile(
            mode="w", prefix="mcp-inline-", suffix=".json", delete=False
        )
        try:
            json.dump(inline_config, tmp)
            tmp.flush()
            inline_temp_file = Path(tmp.name)
            config_path = inline_temp_file
            logger.info(
                "Using inline command as configuration: %s %s",
                command,
                " ".join(cmd_args),
            )
        finally:
            tmp.close()

    # Create settings from CLI arguments
    settings = BridgeSettings(
        host=args.host, port=args.port, path=args.path, log_level=args.log_level
    )

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the server
    test_connection = not args.no_test_connection
    try:
        await run_server(config_path, settings, test_connection=test_connection)
        return 0
    finally:
        # Clean up temporary inline config file if used
        if inline_temp_file and inline_temp_file.exists():
            try:
                inline_temp_file.unlink()
            except Exception:  # pragma: no cover - best effort cleanup
                pass


def main():
    """Main entry point for the MCP HTTP Bridge CLI."""
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        return 0
    except Exception as e:
        logger.error(f"Server failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
