# MCP Wrapper

A Python service that wraps stdio-based MCP (Model Context Protocol) servers and exposes them via HTTP using the streamable-http protocol. This allows stdio MCP servers to be accessed over the network.

## Features

- **Protocol Bridging**: Converts stdio MCP communication to HTTP streamable-http protocol
- **Multi-server Support**: Handle multiple MCP servers from a single HTTP endpoint
- **Runtime Management**: Automatically spawn and manage MCP server processes
- **Flexible Configuration**: JSON-based configuration supporting both Node.js (npx) and Python (uvx) servers
- **Production Ready**: Built with FastMCP for robust HTTP handling

## Installation

```bash
# Install using uv (recommended)
uv pip install -e .

# Or install development dependencies
uv pip install -e ".[dev]"
```

## Configuration

Create a configuration file (e.g., `config.json`) with your MCP servers:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sequential-thinking"
      ]
    },
    "filesystem": {
      "command": "npx", 
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/tmp"
      ]
    },
    "python-server": {
      "command": "uvx",
      "args": [
        "mcp-server-git",
        "--repository",
        "."
      ],
      "env": {
        "GIT_AUTHOR_NAME": "MCP Wrapper",
        "GIT_AUTHOR_EMAIL": "mcp@example.com"
      }
    }
  }
}
```

### Configuration Options

Each server configuration supports:

- `command`: The command to run (e.g., "npx", "uvx", "python")
- `args`: Array of command line arguments  
- `env`: Optional environment variables (key-value pairs)
- `cwd`: Optional working directory

## Usage

### Command Line

```bash
# Start the wrapper server
mcp-wrapper config.json

# Customize host and port
mcp-wrapper config.json --host 0.0.0.0 --port 9000

# Enable debug logging
mcp-wrapper config.json --log-level DEBUG

# Custom endpoint path
mcp-wrapper config.json --path /api/mcp
```

### Programmatic Usage

```python
import asyncio
from mcp_wrapper import run_server

async def main():
    await run_server(
        config_path="config.json",
        host="127.0.0.1", 
        port=8000,
        path="/mcp",
        log_level="INFO"
    )

asyncio.run(main())
```

### Docker Deployment

```dockerfile
FROM python:3.12-slim

# Install Node.js for npx support
RUN apt-get update && apt-get install -y nodejs npm

# Install Python and uv
RUN pip install uv

# Copy application
COPY . /app
WORKDIR /app

# Install dependencies
RUN uv pip install -e .

# Expose port
EXPOSE 8000

# Run the server
CMD ["mcp-wrapper", "config.json", "--host", "0.0.0.0"]
```

## API Endpoints

Once running, the wrapper exposes MCP servers at:

- Base URL: `http://localhost:8000/mcp` (configurable)
- Protocol: MCP streamable-http

The wrapper automatically:
1. Routes requests to appropriate MCP servers based on configuration
2. Manages server process lifecycle (start/stop as needed)
3. Bridges stdio ↔ HTTP communication
4. Handles concurrent requests efficiently

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd mcp-wrapper

# Install in development mode with dependencies
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_wrapper

# Run specific test file
pytest tests/test_config.py
```

### Project Structure

```
src/mcp_wrapper/
├── __init__.py          # Package exports
├── main.py              # CLI entry point  
├── models.py            # Pydantic data models
├── config.py            # Configuration management
├── process_manager.py   # MCP server process management
├── protocol_bridge.py   # stdio ↔ HTTP protocol bridge
└── server.py           # Main HTTP server coordination

tests/
├── test_config.py       # Configuration tests
├── test_process_manager.py  # Process management tests
└── test_integration.py  # Integration tests
```

## Architecture

The MCP wrapper consists of several key components:

1. **Config Manager**: Loads and validates JSON configuration
2. **Process Manager**: Spawns and manages MCP server subprocesses  
3. **Protocol Bridge**: Converts between stdio JSON-RPC and HTTP protocols
4. **HTTP Server**: FastMCP-based server exposing the streamable-http protocol
5. **Unified Proxy**: Coordinates multiple MCP servers under a single HTTP interface

## Requirements

- Python 3.12+
- Node.js (for npx-based MCP servers)
- uv package manager

## License

[Add your license here]

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request
