# Purpose and overview

This project is a wrapper for MCP tools that only offer 'stdio' protocol and
exposes them via streamable-http via network access.

It takes a config file with a standard MCP definition:

```
{
  "sequential-thinking": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-sequential-thinking"
    ]
  }
}
```

It must be able to run MCP servers using `npx` (Node.JS) or `uvx` (Python) so
both runtimes must be present.

The main challenge is to create a Python script that will spawn the
`stdio`-based MCP server based on the config file and expose that with
streamable-http MCP protocol. It will be deployed in a Docker container with
both `npx` and `uvx` runtimes available.

Use `fastmcp` to listen on the network port if required. Or pass through
from network to stdio if it's easier. You will have to understand the MCP
protocol to some extent to make an informed decision on how to implement the
`mcp-http-bridge`.

## Developer notes

The script will use `uv` (and the corresponding `uv run` etc) for package
management - don't try to use `pip` directly. 

Always use `context7` to look up the latest documentation for any library.

Create a well-structured project with clear separation of concerns, create
tests. Don't go overboard with configurability, flexibility or error checking -
keep it simple, it's not a rocket science.