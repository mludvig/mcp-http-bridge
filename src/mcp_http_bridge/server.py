"""Main server implementation using FastMCP proxy for 1:1 protocol bridging."""

import asyncio
import logging
import signal
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.client.transports import StdioTransport

from .config import ConfigManager
from .models import WrapperSettings

logger = logging.getLogger(__name__)


class MCPWrapperServer:
    """
    MCP Wrapper server that provides 1:1 protocol bridging.

    Uses FastMCP's proxy capabilities to bridge stdio-based MCP servers
    to HTTP streamable-http protocol without any indirection.
    """

    def __init__(self, config_path: str | Path):
        self.config_manager = ConfigManager(config_path)
        self.proxy: FastMCP | None = None
        self._shutdown_event = asyncio.Event()

    async def setup(self, test_connection: bool = True) -> None:
        """Setup the proxy server."""
        # Load configuration
        config = self.config_manager.load_config()
        server_config = config.server

        logger.info(f"Setting up proxy for MCP server: {server_config.command}")

        # Create StdioTransport for the backend MCP server
        transport = StdioTransport(
            command=server_config.command,
            args=server_config.args,
            env=server_config.env,
            cwd=server_config.cwd,
        )

        # Create FastMCP proxy that exposes the backend server directly
        self.proxy = FastMCP.as_proxy(transport, name="MCP-Wrapper-Proxy")

        # Test the connection during startup to catch issues early
        if test_connection:
            logger.info("Testing MCP server connection...")
            try:
                # Create a temporary client to test the connection
                from fastmcp import Client

                test_client = Client(transport)

                # Set a reasonable timeout for the startup test
                logger.info(
                    f"Starting MCP server: {server_config.command} {' '.join(server_config.args)}"
                )

                # Use asyncio.wait_for to add a timeout
                await asyncio.wait_for(
                    self._test_connection(test_client),
                    timeout=30.0,  # 30 second timeout
                )
                logger.info("MCP server connection test successful")
            except TimeoutError:
                logger.error("MCP server startup timed out after 30 seconds")
                logger.error(
                    f"Command: {server_config.command} {' '.join(server_config.args)}"
                )
                logger.warning(
                    "The server will continue starting, but the MCP server may not be ready immediately"
                )
            except Exception as e:
                logger.error(f"Failed to connect to MCP server during startup: {e}")
                logger.error(
                    f"Command: {server_config.command} {' '.join(server_config.args)}"
                )
                raise RuntimeError(f"MCP server startup failed: {e}") from e

        logger.info("MCP wrapper proxy setup complete")

    async def _test_connection(self, test_client):
        """Test connection to the MCP server."""
        async with test_client:
            # Try to ping - this will start the subprocess and test the connection
            await test_client.ping()

    async def start(self, settings: WrapperSettings) -> None:
        """Start the HTTP server."""
        if self.proxy is None:
            raise RuntimeError("Server not setup. Call setup() first.")

        # Setup signal handlers for graceful shutdown
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

        logger.info(
            f"Starting MCP wrapper server on {settings.host}:{settings.port}{settings.path}"
        )

        try:
            # Run the proxy with HTTP transport
            await self.proxy.run_async(
                transport="http",
                host=settings.host,
                port=settings.port,
                path=settings.path,
                log_level=settings.log_level.lower(),
            )
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._shutdown_event.set()

    async def stop(self) -> None:
        """Stop the server gracefully."""
        logger.info("Stopping MCP wrapper server...")
        self._shutdown_event.set()

        # FastMCP handles cleanup automatically
        logger.info("MCP wrapper server stopped")


async def run_server(
    config_path: str | Path, settings: WrapperSettings, test_connection: bool = True
) -> None:
    """Run the MCP wrapper server."""
    server = MCPWrapperServer(config_path)

    try:
        await server.setup(test_connection=test_connection)
        await server.start(settings)
    except Exception as e:
        logger.error(f"Failed to run server: {e}")
        raise
    finally:
        await server.stop()
