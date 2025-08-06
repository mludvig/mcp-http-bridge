"""Main server module for MCP wrapper."""

import asyncio
import logging
import signal
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from .config import ConfigManager
from .models import WrapperSettings
from .process_manager import ProcessManager
from .protocol_bridge import MCPBridge, UnifiedMCPProxy

logger = logging.getLogger(__name__)


class MCPWrapperServer:
    """Main MCP wrapper server that coordinates all components."""
    
    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self.config_manager = ConfigManager(config_path)
        self.process_manager = ProcessManager()
        self.bridge: Optional[MCPBridge] = None
        self.unified_proxy: Optional[UnifiedMCPProxy] = None
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self) -> None:
        """Initialize the server with configuration."""
        logger.info("Initializing MCP wrapper server...")
        
        # Load configuration
        config = self.config_manager.load_config()
        
        # Set up process manager with server configurations
        for name, server_config in config.mcpServers.items():
            self.process_manager.add_server(name, server_config)
        
        # Create the bridge
        self.bridge = MCPBridge(self.process_manager)
        
        # Create unified proxy
        server_configs = {name: cfg.model_dump() for name, cfg in config.mcpServers.items()}
        self.unified_proxy = UnifiedMCPProxy(self.bridge, server_configs)
        
        logger.info(f"Initialized with {len(config.mcpServers)} MCP servers")
    
    async def start(self, settings: Optional[WrapperSettings] = None) -> None:
        """Start the HTTP server."""
        if not self.unified_proxy:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        
        if settings is None:
            settings = self.config_manager.get_settings()
        
        logger.info(f"Starting MCP wrapper server on {settings.host}:{settings.port}{settings.path}")
        
        # Set up signal handlers for graceful shutdown
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)
        
        try:
            # Start the FastMCP server
            await self.unified_proxy.run_async(
                transport="http",
                host=settings.host,
                port=settings.port,
                path=settings.path,
                log_level=settings.log_level.upper()
            )
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the server and clean up resources."""
        logger.info("Stopping MCP wrapper server...")
        
        if self.bridge:
            await self.bridge.cleanup()
        
        await self.process_manager.stop_all()
        
        self._shutdown_event.set()
        logger.info("MCP wrapper server stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.stop())
    
    async def run_until_shutdown(self, settings: Optional[WrapperSettings] = None) -> None:
        """Run the server until shutdown signal is received."""
        try:
            await self.initialize()
            
            # Start server in background
            server_task = asyncio.create_task(self.start(settings))
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
            # Cancel server task
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
                
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            await self.stop()


async def run_server(
    config_path: str | Path,
    host: str = "127.0.0.1",
    port: int = 8000,
    path: str = "/mcp",
    log_level: str = "INFO"
) -> None:
    """Run the MCP wrapper server with the given settings."""
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    settings = WrapperSettings(
        host=host,
        port=port,
        path=path,
        log_level=log_level
    )
    
    server = MCPWrapperServer(config_path)
    await server.run_until_shutdown(settings)
