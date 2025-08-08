# GitHub Copilot Instructions for MCP HTTP Bridge

## Project Overview

This project is an HTTP bridge for stdio-based Model Context Protocol (MCP) servers. It allows exposing MCP servers that only support stdio transport via HTTP using the streamable-http protocol.

### Key Components

- **FastMCP**: Core dependency for MCP protocol handling and HTTP proxy functionality
- **Pydantic**: Used for configuration models and validation
- **uvx/uv**: Package management and execution environment

## Development Workflow

### Prerequisites
- Always use `uv` for package management and execution
- Python >=3.12 (check `pyproject.toml` for current requirement). Never attempt to downgrade Python version in pyproject.toml - if something doesn't work, make sure you're running it with `uv` and have all the dependencies installed.
- Use `uv sync --extra dev` to install dependencies, including dev dependencies.
- Tests must pass before making changes

### Use the available MCP tools

- Always consider calling "context7" MCP server to retrieve the most recent documentation
- Make use of "sequentialthinking" MCP server for complex tasks

### Running Commands
```bash
# Run the application
uv run mcp-http-bridge --config config.json
uv run mcp-http-bridge --command "uvx mcp-server-time"

# Install dependencies
uv add package-name
uv add --extra dev package-name  # dev dependencies
```

## Architecture

### Core Files
- `src/mcp_http_bridge/main.py` - CLI entry point with argument parsing
- `src/mcp_http_bridge/server.py` - HTTP server using FastMCP proxy
- `src/mcp_http_bridge/config.py` - Configuration management
- `src/mcp_http_bridge/models.py` - Pydantic data models

### Key Features
1. **Dual Input Methods**: Supports both JSON config files (`--config`) and inline commands (`--command`)
2. **FastMCP Integration**: Uses FastMCP's proxy capabilities for 1:1 protocol bridging
3. **Connection Testing**: Optional startup connection testing with timeout
4. **Comprehensive Logging**: Configurable log levels with structured output

## Common Development Tasks

### Adding New CLI Arguments
- Update `main.py` argument parser
- Update `WrapperSettings` model in `models.py` if needed
- Add corresponding tests in `tests/test_main*.py`
- Update Docker configuration if arguments affect container behavior

### Modifying Configuration
- Update `MCPServerConfig` or `MCPWrapperConfig` in `models.py`
- Update `ConfigManager` in `config.py` for loading logic
- Add tests in `tests/test_config.py`
- Update example config files if needed

### Server Behavior Changes
- Modify `MCPWrapperServer` class in `server.py`
- Update connection testing logic if needed
- Add tests in `tests/test_server.py`
- Consider impact on Docker deployment

## Testing Guidelines

### Test Structure
- `test_main*.py` - CLI argument parsing and main entry point
- `test_config.py` - Configuration loading and validation
- `test_models.py` - Pydantic model validation
- `test_server.py` - Server functionality
- `test_integration.py` - End-to-end integration tests
- `test_main_inline.py` - Inline command functionality

### Test Conventions
- Use `@pytest.mark.asyncio` for async tests
- Mock `run_server` calls in main tests to avoid actual server startup
- Use temporary files with proper cleanup for config tests
- Test both success and error cases
- Ensure mutually exclusive arguments are tested

### Running Specific Tests
```bash
# Test inline command functionality
uv run pytest tests/test_main_inline.py -v

# Test configuration handling
uv run pytest tests/test_config.py -v

# Run with coverage
uv run pytest --cov=src
```

## Docker and Deployment

### Container Structure
- Base image: `python:3.13-slim` (check Dockerfile for current version)
- Includes Node.js for `uvx` MCP server support
- Non-root user execution for security
- Port 8000 exposed by default

### Docker Compose Services
- `mcp-http-bridge`: Standard config-file based service
- `mcp-http-bridge-inline`: Example inline command service
- Both services demonstrate different usage patterns

### Environment Variables
The application doesn't use environment variables for configuration - all settings are via CLI arguments or config files.

## Common Patterns

### Adding New MCP Server Support
1. Test manually with inline command first:
   ```bash
   uv run mcp-http-bridge --command "your-mcp-server-command"
   ```
2. Create JSON config for persistent use
3. Add Docker Compose service if commonly used
4. Update documentation with example

### Troubleshooting Connection Issues
- Check `--log-level DEBUG` for detailed FastMCP logs
- Use `--no-test-connection` to skip startup testing
- Verify MCP server works standalone first
- Check server command path and arguments

### Performance Considerations
- FastMCP handles HTTP streaming and buffering
- Connection pooling managed by FastMCP
- Startup connection testing adds ~30 second timeout
- Long-running servers should use `restart: unless-stopped`

## Code Style and Quality

### Python Standards
- Follow PEP 8 (enforced by ruff)
- Use type hints consistently
- Async/await for all I/O operations
- Proper exception handling with logging

### Error Handling Patterns
```python
# CLI argument errors - return exit code
if not config_path.exists():
    print(f"Error: Configuration file not found: {config_path}")
    return 1

# Server errors - log and re-raise
try:
    await server_operation()
except Exception as e:
    logger.error(f"Server operation failed: {e}")
    raise
```

## Debugging Tips

### Common Issues
1. **Import Errors**: Make sure all dependencies are installed via `uv add`
   - Run `uv sync --extra dev` to ensure dev dependencies are included

### Useful Debug Commands
```bash
# Test argument parsing
uv run mcp-http-bridge --help

# Check FastMCP version
uv run python -c "import fastmcp; print(fastmcp.__version__)"

# Docker container inspection
docker run --rm -it mcp-http-bridge /bin/bash
```

## Future Enhancements to Consider

### Potential Features
- Authentication/authorization layers

### Architectural Notes
- FastMCP provides the core protocol handling - avoid reimplementing MCP logic
- Keep configuration simple and declarative
- Maintain Docker compatibility for easy deployment
- Consider backward compatibility when changing CLI arguments

## Dependencies and Updates

### Major Dependencies
- **fastmcp**: Core MCP protocol and HTTP proxy - pin to compatible versions
- **pydantic**: Data validation - v2.x required for current model patterns
- **pytest-asyncio**: Testing async code - ensure compatibility with Python version

### Update Strategy
- Test thoroughly with new FastMCP versions
- Check for breaking changes in Pydantic major releases
- Update Python version in Dockerfile when bumping requirements
- Maintain compatibility with uvx and recent MCP servers

## Final Notes

This project serves as a bridge, not a reimplementation of MCP. Keep the codebase focused on configuration, CLI interface, and leveraging FastMCP's capabilities rather than implementing low-level protocol details.

When in doubt, prefer explicit configuration over implicit behavior, and always ensure both config-file and inline-command workflows continue to work.
