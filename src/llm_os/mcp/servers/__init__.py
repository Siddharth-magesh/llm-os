"""
Built-in MCP Servers

This package contains all built-in MCP servers for LLM-OS.

Server Types:
- Internal (Python): These run in-process and are Linux-specific
  - ApplicationsServer: Linux desktop application management
  - ProcessServer: Shell/process control
  - SystemServer: System information and hardware control

- External (via stdio): These can be replaced by official MCP servers
  - FilesystemServer: File operations (can use @modelcontextprotocol/server-filesystem)
  - GitServer: Git operations (can use @modelcontextprotocol/server-git)
"""

from llm_os.mcp.servers.base import BaseMCPServer, RegisteredTool
from llm_os.mcp.servers.filesystem import FilesystemServer
from llm_os.mcp.servers.applications import ApplicationsServer
from llm_os.mcp.servers.process import ProcessServer
from llm_os.mcp.servers.system import SystemServer
from llm_os.mcp.servers.git import GitServer

__all__ = [
    # Base
    "BaseMCPServer",
    "RegisteredTool",
    # Internal servers (always Python, Linux-specific)
    "ApplicationsServer",
    "ProcessServer",
    "SystemServer",
    # Internal servers (can be replaced by official MCP servers)
    "FilesystemServer",
    "GitServer",
]

# Internal Python servers - always use these (Linux-specific)
INTERNAL_SERVERS = {
    "applications": ApplicationsServer,
    "process": ProcessServer,
    "system": SystemServer,
}

# Servers that can be replaced by official MCP servers
REPLACEABLE_SERVERS = {
    "filesystem": FilesystemServer,
    "git": GitServer,
}

# All built-in servers (for backwards compatibility)
BUILTIN_SERVERS = {
    **INTERNAL_SERVERS,
    **REPLACEABLE_SERVERS,
}
