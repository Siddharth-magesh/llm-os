"""
MCP Orchestrator

Manages MCP servers (internal Python + external stdio), tool routing, and security.

Supports two types of servers:
- Internal servers: Python-based, run in-process (ProcessServer, SystemServer, ApplicationsServer)
- External servers: Official/third-party MCP servers via stdio (filesystem, git, fetch, memory, etc.)
"""

from llm_os.mcp.orchestrator.security import (
    SecurityManager,
    SecurityPolicy,
    SecurityContext,
    SecurityAction,
    SecurityCheckResult,
    PathSandbox,
)
from llm_os.mcp.orchestrator.server_manager import (
    ServerManager,
    ServerRegistry,
    ManagedServer,
    ServerError,
    ServerNotFoundError,
    ServerAlreadyExistsError,
    ServerInitializationError,
)
from llm_os.mcp.orchestrator.tool_router import (
    ToolRouter,
    ToolDispatcher,
    RouterConfig,
    ToolRoutingError,
    ToolNotFoundError,
    ToolExecutionError,
)
from llm_os.mcp.orchestrator.orchestrator import (
    MCPOrchestrator,
    OrchestratorConfig,
    ExternalServerSettings,
    create_orchestrator,
    create_minimal_orchestrator,
    list_available_official_servers,
)

__all__ = [
    # Security
    "SecurityManager",
    "SecurityPolicy",
    "SecurityContext",
    "SecurityAction",
    "SecurityCheckResult",
    "PathSandbox",
    # Server Management
    "ServerManager",
    "ServerRegistry",
    "ManagedServer",
    "ServerError",
    "ServerNotFoundError",
    "ServerAlreadyExistsError",
    "ServerInitializationError",
    # Tool Routing
    "ToolRouter",
    "ToolDispatcher",
    "RouterConfig",
    "ToolRoutingError",
    "ToolNotFoundError",
    "ToolExecutionError",
    # Main Orchestrator
    "MCPOrchestrator",
    "OrchestratorConfig",
    "ExternalServerSettings",
    # Factory functions
    "create_orchestrator",
    "create_minimal_orchestrator",
    "list_available_official_servers",
]
