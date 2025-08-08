# GitHub Copilot Instructions for MCP HTTP Bridge

## Project Overview

This project is an HTTP bridge for stdio-based Model Context Protocol (MCP) servers. It exposes MCP servers that only support stdio transport via HTTP using the streamable-http protocol.

## Key Components

- **FastMCP**: Core MCP protocol handling and HTTP proxy functionality
- **uv**: Package management and execution (always use `uv`, never `pip` directly)
- Supports both `npx` (Node.js) and `uvx` (Python) MCP servers
- Python >=3.12 required

## Development Workflow

### Essential Commands
```bash
# Install dependencies
uv sync --extra dev

# Run the application
uv run mcp-http-bridge --config config.json
uv run mcp-http-bridge --command "uvx mcp-server-time"

# Run tests
uv run pytest
```

### Use Available MCP Tools

- Always use **context7** MCP server to retrieve latest documentation
- Use **sequentialthinking** MCP server for complex tasks

## Architecture

### Core Files

- `src/mcp_http_bridge/main.py` - CLI entry point
- `src/mcp_http_bridge/server.py` - HTTP server using FastMCP proxy
- `src/mcp_http_bridge/config.py` - Configuration management
- `src/mcp_http_bridge/models.py` - Pydantic data models

### Key Features

- Dual input methods: JSON config files (`--config`) and inline commands (`--command`)
- Uses FastMCP for 1:1 protocol bridging
- Optional connection testing with timeout
- Docker deployment ready

## Development Principles

- Keep it simple - avoid overengineering
- Use `uv` for all package management
- Test both config-file and inline-command workflows
- Follow PEP 8 standards
- Use async/await for I/O operations
- FastMCP handles the protocol - focus on configuration and CLI interface
