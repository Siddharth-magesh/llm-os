"""
Built-in MCP Servers

This package contains all built-in MCP servers for LLM-OS.
"""

from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.servers.filesystem import FilesystemServer
from llm_os.mcp.servers.applications import ApplicationsServer
from llm_os.mcp.servers.process import ProcessServer
from llm_os.mcp.servers.system import SystemServer
from llm_os.mcp.servers.git import GitServer

__all__ = [
    "BaseMCPServer",
    "FilesystemServer",
    "ApplicationsServer",
    "ProcessServer",
    "SystemServer",
    "GitServer",
]

# Server registry for auto-discovery
BUILTIN_SERVERS = {
    "filesystem": FilesystemServer,
    "applications": ApplicationsServer,
    "process": ProcessServer,
    "system": SystemServer,
    "git": GitServer,
}
