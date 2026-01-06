"""
MCP Client Module - For communicating with external MCP servers.

This module provides clients for connecting to external MCP servers
that run as separate processes using the stdio transport.
"""

from llm_os.mcp.client.stdio_client import (
    StdioMCPClient,
    MCPClientPool,
    MCPRequest,
    MCPResponse,
    MCPNotification,
    ServerCapabilities,
    ToolDefinition,
)
from llm_os.mcp.client.external_server import (
    ExternalMCPServer,
    ExternalServerManager,
    ExternalServerConfig,
    OFFICIAL_SERVERS,
)

__all__ = [
    # Stdio Client
    "StdioMCPClient",
    "MCPClientPool",
    "MCPRequest",
    "MCPResponse",
    "MCPNotification",
    "ServerCapabilities",
    "ToolDefinition",
    # External Server
    "ExternalMCPServer",
    "ExternalServerManager",
    "ExternalServerConfig",
    "OFFICIAL_SERVERS",
]
