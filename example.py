#!/usr/bin/env python3
"""
Example usage of MCP Wrapper.

This script demonstrates how to:
1. Create a simple MCP server configuration
2. Start the wrapper programmatically  
3. Test the HTTP endpoint
"""

import json
import asyncio
import tempfile
from pathlib import Path

from mcp_wrapper import run_server, WrapperSettings


async def example_usage():
    """Example of using MCP wrapper programmatically."""
    
    # Create a simple test configuration for sequential thinking server
    config = {
        "server": {
            "command": "npx",
            "args": [
                "-y", 
                "@modelcontextprotocol/server-sequential-thinking"
            ]
        }
    }
    
    # Write config to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        config_path = f.name
    
    try:
        print(f"Starting MCP wrapper with config: {config_path}")
        print("The server will be available at: http://127.0.0.1:8000/mcp")
        print("Press Ctrl+C to stop")
        
        # Create settings
        settings = WrapperSettings(
            host="127.0.0.1",
            port=8000,
            path="/mcp",
            log_level="INFO"
        )
        
        # Run the server
        await run_server(config_path, settings)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Clean up
        Path(config_path).unlink()


if __name__ == "__main__":
    asyncio.run(example_usage())
