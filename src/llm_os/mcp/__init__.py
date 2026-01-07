"""
MCP (Model Context Protocol) Module

Provides the MCP server framework, tool definitions, and orchestration
for system interaction capabilities.

Supports two types of servers:
- Internal servers: Python-based, run in-process (ProcessServer, SystemServer, ApplicationsServer)
- External servers: Official/third-party MCP servers via stdio (filesystem, git, fetch, memory, etc.)
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
    OrchestratorConfig,
    ExternalServerSettings,
    ServerManager,
    ToolRouter,
    SecurityManager,
    SecurityPolicy,
    create_orchestrator,
    create_minimal_orchestrator,
    list_available_official_servers,
)
from llm_os.mcp.client import (
    StdioMCPClient,
    MCPClientPool,
    ExternalMCPServer,
    ExternalServerManager,
    ExternalServerConfig,
    OFFICIAL_SERVERS,
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
    "OrchestratorConfig",
    "ExternalServerSettings",
    "ServerManager",
    "ToolRouter",
    "SecurityManager",
    "SecurityPolicy",
    # Factory functions
    "create_orchestrator",
    "create_minimal_orchestrator",
    "list_available_official_servers",
    # External Server Client
    "StdioMCPClient",
    "MCPClientPool",
    "ExternalMCPServer",
    "ExternalServerManager",
    "ExternalServerConfig",
    "OFFICIAL_SERVERS",
]
