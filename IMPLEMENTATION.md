# MCP HTTP Bridge Implementation - 1:1 Protocol Bridge

## Overview

The bridge uses FastMCP's proxy capabilities to directly expose backend MCP server capabilities via HTTP streamable-http protocol.

## Architecture

### Components

1. **Configuration (`models.py`, `config.py`)**
   - Pydantic validation for configuration integrity
   - Support for command, args, env, and working directory

2. **Proxy Server (`server.py`)**
   - Uses `FastMCP.as_proxy()` with `StdioTransport`
   - Automatic subprocess management via FastMCP
   - Direct protocol translation (stdio ↔ HTTP)
   - Signal handling for graceful shutdown

3. **CLI Interface (`main.py`)**
   - Handles command-line interface
   - Configuration file + runtime settings
   - Async execution with proper error handling

## 🚀 Implementation Details

### FastMCP Integration

```python
# Create transport for backend MCP server
transport = StdioTransport(
    command=server_config.command,
    args=server_config.args,
    env=server_config.env,
    cwd=server_config.cwd
)

# Create proxy that exposes backend directly
proxy = FastMCP.as_proxy(transport, name="MCP-HTTP-Bridge")

# Run proxy with HTTP transport
await proxy.run_async(
    transport="http",
    host=settings.host,
    port=settings.port,
    path=settings.path
)
```

### Configuration Schema

```json
{
  "server": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
    "env": {"API_KEY": "secret"},
    "cwd": "/working/directory"
  }
}
```

### Request Flow

```
HTTP Client → FastMCP Proxy → StdioTransport → MCP Server
           ←                ←                ←
```

1. **HTTP Request**: Client sends streamable-HTTP request
2. **Protocol Translation**: FastMCP converts to stdio JSON-RPC
3. **Backend Processing**: MCP server processes request
4. **Response Translation**: FastMCP converts response to HTTP
5. **Client Response**: Streamable-HTTP response returned

## Testing & Validation

### Manual Testing

```bash
# Start HTTP bridge
uv run mcp-http-bridge config.json --port 8001

# Test HTTP endpoint
curl -X POST -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {...}}' \
     http://127.0.0.1:8001/mcp/
```

**Result**: Successful protocol bridging with direct backend communication

## Configuration Examples

### Basic Setup (NPX)
```json
{
  "server": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
  }
}
```

### Advanced Setup (UVX with Environment)
```json
{
  "server": {
    "command": "uvx",
    "args": ["mcp-server-git", "--repository", "."],
    "env": {
      "GIT_AUTHOR_NAME": "MCP HTTP Bridge",
      "GIT_AUTHOR_EMAIL": "bridge@example.com"
    },
    "cwd": "/path/to/repository"
  }
}
```

### Multiple Instances

For multiple MCP servers, run separate HTTP bridge instances:

```bash
# Server 1: Sequential Thinking on port 8001
uv run mcp-http-bridge config-thinking.json --port 8001

# Server 2: Filesystem on port 8002  
uv run mcp-http-bridge config-filesystem.json --port 8002

# Server 3: Git on port 8003
uv run mcp-http-bridge config-git.json --port 8003
```
