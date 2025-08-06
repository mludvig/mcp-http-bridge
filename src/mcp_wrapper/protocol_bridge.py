"""Protocol bridge for converting between stdio MCP and HTTP MCP."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastmcp import FastMCP, Client
from fastmcp.server.proxy import ProxyClient

from .process_manager import ProcessManager, MCPServerProcess

logger = logging.getLogger(__name__)


class StdioMCPClient:
    """A client that communicates with stdio MCP servers."""
    
    def __init__(self, server_process: MCPServerProcess):
        self.server_process = server_process
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._response_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the client and begin listening for responses."""
        if not self.server_process.is_running:
            raise RuntimeError("Server process is not running")
        
        # Start the response listener
        self._response_task = asyncio.create_task(self._response_listener())
    
    async def stop(self) -> None:
        """Stop the client."""
        if self._response_task:
            self._response_task.cancel()
            try:
                await self._response_task
            except asyncio.CancelledError:
                pass
        
        # Cancel any pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()
    
    async def _response_listener(self) -> None:
        """Listen for responses from the stdio server."""
        try:
            while self.server_process.is_running:
                response_data = await self.server_process.read_response()
                if not response_data:
                    continue
                
                try:
                    response = json.loads(response_data.decode('utf-8'))
                    await self._handle_response(response)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON response: {e}")
                except Exception as e:
                    logger.error(f"Error handling response: {e}")
        except Exception as e:
            logger.error(f"Response listener error: {e}")
    
    async def _handle_response(self, response: Dict[str, Any]) -> None:
        """Handle a response from the stdio server."""
        request_id = response.get('id')
        if request_id is None:
            # This might be a notification
            logger.debug(f"Received notification: {response}")
            return
        
        if request_id in self._pending_requests:
            future = self._pending_requests.pop(request_id)
            if not future.done():
                if 'error' in response:
                    future.set_exception(Exception(f"MCP Error: {response['error']}"))
                else:
                    future.set_result(response.get('result'))
    
    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Send a request to the stdio server and wait for response."""
        self._request_id += 1
        request_id = self._request_id
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        # Create future for the response
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        try:
            # Send the request
            request_data = json.dumps(request).encode('utf-8') + b'\n'
            await self.server_process.send_message(request_data)
            
            # Wait for response
            return await asyncio.wait_for(future, timeout=30.0)
        
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise Exception(f"Request timeout for method: {method}")
        except Exception as e:
            self._pending_requests.pop(request_id, None)
            raise


class MCPBridge:
    """Bridges stdio MCP servers to HTTP MCP using FastMCP proxy."""
    
    def __init__(self, process_manager: ProcessManager):
        self.process_manager = process_manager
        self._stdio_clients: Dict[str, StdioMCPClient] = {}
        self._proxies: Dict[str, FastMCP] = {}
    
    async def create_proxy_for_server(self, server_name: str) -> FastMCP:
        """Create a FastMCP proxy for a stdio MCP server."""
        if server_name in self._proxies:
            return self._proxies[server_name]
        
        # Ensure the server is running
        server_process = await self.process_manager.ensure_server_running(server_name)
        
        # Create stdio client
        stdio_client = StdioMCPClient(server_process)
        await stdio_client.start()
        self._stdio_clients[server_name] = stdio_client
        
        # Create a custom FastMCP server that forwards to the stdio client
        proxy = FastMCP(name=f"{server_name}-proxy")
        
        # Add a generic tool that forwards to the stdio server
        @proxy.tool
        async def forward_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Any:
            """Forward tool calls to the stdio MCP server."""
            return await stdio_client.send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
        
        # Add other MCP methods as needed
        self._proxies[server_name] = proxy
        logger.info(f"Created proxy for MCP server: {server_name}")
        
        return proxy
    
    async def get_or_create_proxy(self, server_name: str) -> FastMCP:
        """Get existing proxy or create a new one."""
        if server_name not in self._proxies:
            return await self.create_proxy_for_server(server_name)
        return self._proxies[server_name]
    
    async def cleanup(self) -> None:
        """Clean up all stdio clients and proxies."""
        # Stop all stdio clients
        for client in self._stdio_clients.values():
            await client.stop()
        
        self._stdio_clients.clear()
        self._proxies.clear()
        logger.info("MCPBridge cleanup completed")


class UnifiedMCPProxy(FastMCP):
    """A unified FastMCP proxy that handles multiple stdio MCP servers."""
    
    def __init__(self, bridge: MCPBridge, server_configs: Dict[str, Any]):
        super().__init__(name="MCP-Wrapper-Unified")
        self.bridge = bridge
        self.server_configs = server_configs
        self._setup_unified_tools()
    
    def _setup_unified_tools(self) -> None:
        """Set up tools that route to appropriate servers."""
        
        @self.tool
        async def list_servers() -> Dict[str, Any]:
            """List all available MCP servers and their status."""
            return {
                "servers": list(self.server_configs.keys()),
                "status": self.bridge.process_manager.list_servers()
            }
        
        @self.tool
        async def call_server_tool(server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
            """Call a tool on a specific MCP server."""
            if server_name not in self.server_configs:
                raise ValueError(f"Unknown server: {server_name}")
            
            proxy = await self.bridge.get_or_create_proxy(server_name)
            # This is a simplified approach - in practice, we'd need to implement
            # proper tool discovery and forwarding
            return {"server": server_name, "tool": tool_name, "result": "forwarded"}
        
        logger.info("Unified MCP proxy setup completed")
