"""Process management for MCP servers."""

import asyncio
import logging
import subprocess
from typing import Dict, Optional, Tuple
from pathlib import Path

from .models import MCPServerConfig

logger = logging.getLogger(__name__)


class MCPServerProcess:
    """Represents a running MCP server process."""
    
    def __init__(self, name: str, config: MCPServerConfig):
        self.name = name
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self._stdout_queue: Optional[asyncio.Queue] = None
        self._stderr_queue: Optional[asyncio.Queue] = None
        self._running = False
    
    async def start(self) -> bool:
        """Start the MCP server process."""
        if self._running:
            logger.warning(f"MCP server '{self.name}' is already running")
            return True
        
        try:
            # Prepare environment
            env = None
            if self.config.env:
                import os
                env = os.environ.copy()
                env.update(self.config.env)
            
            # Start the process
            cmd = [self.config.command] + self.config.args
            logger.info(f"Starting MCP server '{self.name}': {' '.join(cmd)}")
            
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.config.cwd
            )
            
            self._running = True
            logger.info(f"MCP server '{self.name}' started with PID {self.process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MCP server '{self.name}': {e}")
            return False
    
    async def stop(self) -> None:
        """Stop the MCP server process."""
        if not self._running or not self.process:
            return
        
        try:
            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning(f"MCP server '{self.name}' did not terminate gracefully, killing...")
            self.process.kill()
            await self.process.wait()
        except Exception as e:
            logger.error(f"Error stopping MCP server '{self.name}': {e}")
        finally:
            self._running = False
            logger.info(f"MCP server '{self.name}' stopped")
    
    async def send_message(self, message: bytes) -> None:
        """Send a message to the MCP server's stdin."""
        if not self._running or not self.process or not self.process.stdin:
            raise RuntimeError(f"MCP server '{self.name}' is not running")
        
        try:
            self.process.stdin.write(message)
            await self.process.stdin.drain()
        except Exception as e:
            logger.error(f"Failed to send message to MCP server '{self.name}': {e}")
            raise
    
    async def read_response(self) -> Optional[bytes]:
        """Read a response from the MCP server's stdout."""
        if not self._running or not self.process or not self.process.stdout:
            return None
        
        try:
            # Read one line (MCP protocol is line-based JSON-RPC)
            line = await self.process.stdout.readline()
            return line if line else None
        except Exception as e:
            logger.error(f"Failed to read from MCP server '{self.name}': {e}")
            return None
    
    @property
    def is_running(self) -> bool:
        """Check if the process is running."""
        return self._running and self.process is not None and self.process.returncode is None


class ProcessManager:
    """Manages multiple MCP server processes."""
    
    def __init__(self):
        self._servers: Dict[str, MCPServerProcess] = {}
    
    def add_server(self, name: str, config: MCPServerConfig) -> MCPServerProcess:
        """Add a new MCP server configuration."""
        if name in self._servers:
            raise ValueError(f"MCP server '{name}' already exists")
        
        server = MCPServerProcess(name, config)
        self._servers[name] = server
        logger.debug(f"Added MCP server configuration: {name}")
        return server
    
    async def start_server(self, name: str) -> bool:
        """Start a specific MCP server."""
        if name not in self._servers:
            raise ValueError(f"MCP server '{name}' not found")
        
        return await self._servers[name].start()
    
    async def stop_server(self, name: str) -> None:
        """Stop a specific MCP server."""
        if name not in self._servers:
            logger.warning(f"MCP server '{name}' not found")
            return
        
        await self._servers[name].stop()
    
    async def stop_all(self) -> None:
        """Stop all MCP servers."""
        tasks = [server.stop() for server in self._servers.values() if server.is_running]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_server(self, name: str) -> Optional[MCPServerProcess]:
        """Get a server by name."""
        return self._servers.get(name)
    
    def list_servers(self) -> Dict[str, bool]:
        """List all servers and their running status."""
        return {name: server.is_running for name, server in self._servers.items()}
    
    async def ensure_server_running(self, name: str) -> MCPServerProcess:
        """Ensure a server is running, starting it if necessary."""
        if name not in self._servers:
            raise ValueError(f"MCP server '{name}' not found")
        
        server = self._servers[name]
        if not server.is_running:
            success = await server.start()
            if not success:
                raise RuntimeError(f"Failed to start MCP server '{name}'")
        
        return server
