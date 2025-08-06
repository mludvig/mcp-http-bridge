"""Tests for process management."""

import asyncio
import pytest

from mcp_wrapper.process_manager import ProcessManager, MCPServerProcess
from mcp_wrapper.models import MCPServerConfig


@pytest.fixture
def process_manager():
    """Create a process manager for testing."""
    return ProcessManager()


@pytest.fixture
def sample_config():
    """Create a sample server configuration."""
    return MCPServerConfig(
        command="python",
        args=["-c", "import time; time.sleep(1); print('test')"],
        env={"TEST": "true"}
    )


def test_process_manager_add_server(process_manager, sample_config):
    """Test adding a server to the process manager."""
    server = process_manager.add_server("test-server", sample_config)
    
    assert isinstance(server, MCPServerProcess)
    assert server.name == "test-server"
    assert server.config == sample_config
    assert not server.is_running


def test_process_manager_duplicate_server(process_manager, sample_config):
    """Test adding a duplicate server raises error."""
    process_manager.add_server("test-server", sample_config)
    
    with pytest.raises(ValueError, match="already exists"):
        process_manager.add_server("test-server", sample_config)


def test_process_manager_get_server(process_manager, sample_config):
    """Test getting a server by name."""
    process_manager.add_server("test-server", sample_config)
    
    server = process_manager.get_server("test-server")
    assert server is not None
    assert server.name == "test-server"
    
    # Test non-existent server
    assert process_manager.get_server("nonexistent") is None


def test_process_manager_list_servers(process_manager, sample_config):
    """Test listing servers and their status."""
    process_manager.add_server("server1", sample_config)
    process_manager.add_server("server2", sample_config)
    
    servers = process_manager.list_servers()
    assert len(servers) == 2
    assert "server1" in servers
    assert "server2" in servers
    assert servers["server1"] is False  # Not running
    assert servers["server2"] is False  # Not running


@pytest.mark.asyncio
async def test_mcp_server_process_start_stop():
    """Test starting and stopping a server process."""
    config = MCPServerConfig(
        command="python",
        args=["-c", "import sys; import time; time.sleep(10)"]
    )
    
    server = MCPServerProcess("test", config)
    
    # Initially not running
    assert not server.is_running
    
    # Start the server
    success = await server.start()
    assert success
    assert server.is_running
    assert server.process is not None
    
    # Stop the server
    await server.stop()
    assert not server.is_running


@pytest.mark.asyncio
async def test_mcp_server_process_invalid_command():
    """Test starting a server with invalid command."""
    config = MCPServerConfig(
        command="nonexistent-command",
        args=[]
    )
    
    server = MCPServerProcess("test", config)
    success = await server.start()
    
    assert not success
    assert not server.is_running


@pytest.mark.asyncio 
async def test_process_manager_ensure_server_running(process_manager):
    """Test ensuring a server is running."""
    config = MCPServerConfig(
        command="python",
        args=["-c", "import time; time.sleep(5)"]
    )
    
    process_manager.add_server("test-server", config)
    
    # Server should start
    server = await process_manager.ensure_server_running("test-server")
    assert server.is_running
    
    # Calling again should return the same running server
    server2 = await process_manager.ensure_server_running("test-server")
    assert server is server2
    assert server.is_running
    
    # Clean up
    await process_manager.stop_all()


@pytest.mark.asyncio
async def test_process_manager_ensure_nonexistent_server(process_manager):
    """Test ensuring a nonexistent server raises error."""
    with pytest.raises(ValueError, match="not found"):
        await process_manager.ensure_server_running("nonexistent")
