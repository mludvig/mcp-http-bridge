"""Data models for MCP HTTP bridge configuration."""

from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    command: str = Field(..., description="Command to run the MCP server")
    args: list[str] = Field(
        default_factory=list, description="Arguments for the command"
    )
    env: dict[str, str] | None = Field(
        default=None, description="Environment variables"
    )
    cwd: str | None = Field(default=None, description="Working directory")


class MCPBridgeConfig(BaseModel):
    """Main configuration for the MCP HTTP bridge - single server passthrough."""

    server: MCPServerConfig = Field(
        ..., description="MCP server configuration for 1:1 protocol bridging"
    )


class BridgeSettings(BaseModel):
    """Runtime settings for the HTTP bridge."""

    host: str = Field(default="127.0.0.1", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")
    path: str = Field(default="/mcp", description="Base path for MCP endpoints")
    log_level: str = Field(default="INFO", description="Logging level")
