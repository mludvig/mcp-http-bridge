"""Main entry point for MCP wrapper."""

import argparse
import asyncio
import logging
from pathlib import Path

from .server import run_server
from .models import WrapperSettings

logger = logging.getLogger(__name__)


async def main_async():
    """Async main function."""
    parser = argparse.ArgumentParser(
        description="MCP Wrapper - Expose stdio MCP servers via HTTP"
    )
    
    parser.add_argument(
        "config",
        help="Path to the MCP configuration file (JSON format)"
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    parser.add_argument(
        "--path",
        default="/mcp",
        help="Base path for MCP endpoints (default: /mcp)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Validate config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        return 1

    # Create settings from CLI arguments
    settings = WrapperSettings(
        host=args.host,
        port=args.port,
        path=args.path,
        log_level=args.log_level
    )
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the server
    await run_server(config_path, settings)
    return 0


def main():
    """Main entry point for the MCP wrapper CLI."""
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
