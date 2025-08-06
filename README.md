# MCP Network Bridge

Enable network access to STDIO-based MCP servers through HTTP streamable protocol.

## The Problem

Many open-source MCP servers only support the local-only `stdio` protocol. For
one reason or another their developers never bothered to implement one of the
two network-enabled modes: SSE or StreamableHTTP.  In most cases that's fine -
_Claude Code_ or _Cursor_  or any other modern IDE supports MCP over `stdio`.
But when your AI application is not a stock-standard IDE that needs access to
some MCP server over the network you've got a problem. 

One option is to add Streaming HTTP support to the MCP servers that you want to
use. It's usually not very difficult but also it's not very scalable.

A better option is to *Bridge* the STDIO local-only protocol to
**StreamableHTTP** network-enabled protocol. And that's what this project is for.

Learn more about [**STDIO** and **StreamableHTTP** MCP Protocols](https://mcpcat.io/guides/comparing-stdio-sse-streamablehttp/)

## Quick Start

The [typical MCP server](https://github.com/modelcontextprotocol/servers/blob/main/src/everything/README.md)
will provide a sample config to use. It could be something like:

```json
{
  "server": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-everything"
    ]
  }
}
```

We can use the same `config.json` with `mcp-network-bridge`:

**Run with Docker**:

```bash
docker run --rm -it -p 8000:8000 -v $(pwd)/config.json:/app/config.json ghcr.io/mludvig/mcp-http-bridge
```

**Or use docker-compose**:

```bash
docker-compose up
```

Your MCP server is now available at `http://localhost:8000/mcp/`.
Test it out with [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

**MCP server network access**

With the bridge running the MCP server can now be accessed over the network:

```json
{
  "server": {
    "type": "http",
    "url": "http://127.0.0.1:8000/mcp/",
  }
}
```

## Security

This bridge doesn't implement any security or access control.
You'll have to configure something like `nginx` in front of it for TLS or Authentication support.
That's beyond the scope of this project since better and more appropriate tools already exist.

## Development

### Local Development

This project uses [uv](https://github.com/astral-sh/uv) for dependency management:

```bash
# Install dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run linting
uv run ruff check src/ tests/

# Format code
uv run ruff format src/ tests/

# Run the CLI
uv run mcp-http-bridge --help
```

### CI/CD

This project uses GitHub Actions for:

- **Continuous Integration**: Runs tests, linting, and formatting checks on every push and PR
- **Build and Release**: Automatically builds and publishes to PyPI and GHCR when tags are pushed
- **Dependency Updates**: Dependabot keeps dependencies up to date

To publish a new release:

1. Update the version in `pyproject.toml`
2. Create a git tag: `git tag v0.1.1`
3. Push the tag: `git push origin v0.1.1`
4. GitHub Actions will automatically build and publish to PyPI and GHCR

### Publishing to PyPI

The workflow uses [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) to securely publish to PyPI without storing API tokens. Make sure to configure the PyPI trusted publisher for this repository.

## Author

**[Michael Ludvig](https://github.com/mludvig)**