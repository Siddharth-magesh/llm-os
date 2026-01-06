"""
MCP (Model Context Protocol) Module

Provides the MCP server framework, tool definitions, and orchestration
for system interaction capabilities.
"""

from llm_os.mcp.types.tools import (
    Tool,
    ToolCall,
    ToolResult,
    ToolContent,
    ToolParameter,
    ParameterType,
    ToolContentType,
)
from llm_os.mcp.types.server import (
    ServerConfig,
    ServerStatus,
    ServerState,
    ServerCapabilities,
    ServerInfo,
    TransportType,
    PermissionLevel,
)
from llm_os.mcp.servers.base import BaseMCPServer, RegisteredTool
from llm_os.mcp.orchestrator import (
    MCPOrchestrator,
    ServerManager,
    ToolRouter,
    SecurityManager,
    SecurityPolicy,
)

__all__ = [
    # Tools
    "Tool",
    "ToolCall",
    "ToolResult",
    "ToolContent",
    "ToolParameter",
    "ParameterType",
    "ToolContentType",
    # Server Types
    "ServerConfig",
    "ServerStatus",
    "ServerState",
    "ServerCapabilities",
    "ServerInfo",
    "TransportType",
    "PermissionLevel",
    # Server Base
    "BaseMCPServer",
    "RegisteredTool",
    # Orchestration
    "MCPOrchestrator",
    "ServerManager",
    "ToolRouter",
    "SecurityManager",
    "SecurityPolicy",
]
