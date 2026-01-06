"""
MCP Orchestrator

Main orchestration layer that coordinates servers, tools, and security.

Supports two types of servers:
1. Internal servers - Python-based servers running in-process (e.g., ProcessServer, SystemServer)
2. External servers - Official/third-party MCP servers running via stdio (e.g., @modelcontextprotocol/server-filesystem)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Coroutine, Type

from llm_os.mcp.orchestrator.security import (
    SecurityManager,
    SecurityPolicy,
    ConfirmationHandler,
)
from llm_os.mcp.orchestrator.server_manager import ServerManager, ServerRegistry
from llm_os.mcp.orchestrator.tool_router import ToolRouter, ToolDispatcher, RouterConfig
from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types.tools import Tool, ToolCall, ToolResult
from llm_os.mcp.types.server import ServerInfo
from llm_os.mcp.client.external_server import (
    ExternalServerManager,
    ExternalServerConfig,
    ExternalMCPServer,
    OFFICIAL_SERVERS,
)


logger = logging.getLogger(__name__)


@dataclass
class ExternalServerSettings:
    """Settings for external MCP servers."""
    # Which official servers to enable
    enabled_official: list[str] = field(default_factory=lambda: ["filesystem", "git", "fetch", "memory"])
    # Whether to use official servers (vs internal implementations)
    use_official_filesystem: bool = True
    use_official_git: bool = True
    # Custom external server configs
    custom_servers: list[ExternalServerConfig] = field(default_factory=list)
    # Additional environment variables for all external servers
    global_env: dict[str, str] = field(default_factory=dict)


@dataclass
class OrchestratorConfig:
    """Configuration for the MCP orchestrator."""
    # Server settings
    auto_start_servers: bool = True
    health_check_interval: float = 30.0
    auto_restart_servers: bool = True
    max_restart_attempts: int = 3

    # Security settings
    security_policy: SecurityPolicy = field(default_factory=SecurityPolicy)

    # Router settings
    router_config: RouterConfig = field(default_factory=RouterConfig)

    # External servers settings
    external_servers: ExternalServerSettings = field(default_factory=ExternalServerSettings)

    # Paths
    custom_servers_path: Path | None = None


class MCPOrchestrator:
    """
    Main MCP orchestration layer.

    Coordinates:
    - Server lifecycle management (internal Python servers + external stdio servers)
    - Tool discovery and routing
    - Security enforcement
    - Health monitoring

    Supports two types of servers:
    - Internal servers: Python-based, run in-process (ProcessServer, SystemServer, ApplicationsServer)
    - External servers: Official/third-party MCP servers via stdio (filesystem, git, fetch, memory, etc.)

    This is the primary interface for the LLM layer to interact
    with MCP servers and tools.
    """

    def __init__(
        self,
        config: OrchestratorConfig | None = None,
        confirmation_handler: ConfirmationHandler | None = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            config: Orchestrator configuration
            confirmation_handler: Handler for security confirmations
        """
        self.config = config or OrchestratorConfig()

        # Initialize components
        self._security_manager = SecurityManager(
            policy=self.config.security_policy,
            confirmation_handler=confirmation_handler,
        )

        self._server_manager = ServerManager(
            health_check_interval=self.config.health_check_interval,
            auto_restart=self.config.auto_restart_servers,
            max_restart_attempts=self.config.max_restart_attempts,
        )

        # Initialize external server manager
        self._external_server_manager = ExternalServerManager()

        self._tool_router = ToolRouter(
            server_manager=self._server_manager,
            security_manager=self._security_manager,
            config=self.config.router_config,
        )

        self._dispatcher = ToolDispatcher(self._tool_router)
        self._initialized = False

    @property
    def server_manager(self) -> ServerManager:
        """Get the server manager (for internal Python servers)."""
        return self._server_manager

    @property
    def external_server_manager(self) -> ExternalServerManager:
        """Get the external server manager (for stdio MCP servers)."""
        return self._external_server_manager

    @property
    def tool_router(self) -> ToolRouter:
        """Get the tool router."""
        return self._tool_router

    @property
    def security_manager(self) -> SecurityManager:
        """Get the security manager."""
        return self._security_manager

    @property
    def dispatcher(self) -> ToolDispatcher:
        """Get the tool dispatcher."""
        return self._dispatcher

    def set_confirmation_handler(self, handler: ConfirmationHandler) -> None:
        """Set the confirmation handler for security prompts."""
        self._security_manager.set_confirmation_handler(handler)

    def register_server(
        self,
        server: BaseMCPServer,
    ) -> None:
        """
        Register an MCP server.

        Args:
            server: Server instance to register
        """
        self._server_manager.register_server(server)

    def register_server_class(
        self,
        server_class: Type[BaseMCPServer],
    ) -> None:
        """
        Register a server class for later instantiation.

        Args:
            server_class: Server class to register
        """
        # Create instance and register
        server = server_class()
        self.register_server(server)

    def register_builtin_servers(self) -> None:
        """
        Register all built-in MCP servers.

        This registers:
        - Internal Python servers for Linux-specific operations (process, system, applications)
        - External official MCP servers for filesystem and git (if configured)
        """
        # Import built-in internal servers (Linux-specific, always use our implementations)
        from llm_os.mcp.servers.applications import ApplicationsServer
        from llm_os.mcp.servers.process import ProcessServer
        from llm_os.mcp.servers.system import SystemServer

        # Always register Linux-specific internal servers
        internal_servers = [
            ApplicationsServer,
            ProcessServer,
            SystemServer,
        ]

        for server_class in internal_servers:
            try:
                self.register_server_class(server_class)
                logger.info(f"Registered internal server: {server_class.server_id}")
            except Exception as e:
                logger.error(f"Failed to register {server_class.server_id}: {e}")

        # Register filesystem and git servers based on configuration
        ext_settings = self.config.external_servers

        if ext_settings.use_official_filesystem:
            # Use official MCP filesystem server
            logger.info("Using official MCP filesystem server")
        else:
            # Use our internal filesystem implementation
            from llm_os.mcp.servers.filesystem import FilesystemServer
            try:
                self.register_server_class(FilesystemServer)
                logger.info("Registered internal filesystem server")
            except Exception as e:
                logger.error(f"Failed to register FilesystemServer: {e}")

        if ext_settings.use_official_git:
            # Use official MCP git server
            logger.info("Using official MCP git server")
        else:
            # Use our internal git implementation
            from llm_os.mcp.servers.git import GitServer
            try:
                self.register_server_class(GitServer)
                logger.info("Registered internal git server")
            except Exception as e:
                logger.error(f"Failed to register GitServer: {e}")

    async def register_external_servers(self) -> dict[str, bool]:
        """
        Register and initialize configured external MCP servers.

        Returns:
            Dict mapping server_id to initialization success
        """
        results = {}
        ext_settings = self.config.external_servers

        # Register enabled official servers
        for server_name in ext_settings.enabled_official:
            if server_name not in OFFICIAL_SERVERS:
                logger.warning(f"Unknown official server: {server_name}")
                continue

            try:
                # Add global environment variables
                env_overrides = dict(ext_settings.global_env) if ext_settings.global_env else {}

                server = await self._external_server_manager.add_official_server(
                    server_name,
                    auto_initialize=True,
                    env=env_overrides if env_overrides else None,
                )
                if server:
                    results[server.server_id] = True
                    logger.info(f"Registered external server: {server_name}")
                else:
                    results[server_name] = False
            except Exception as e:
                logger.error(f"Failed to register external server {server_name}: {e}")
                results[server_name] = False

        # Register custom external servers
        for config in ext_settings.custom_servers:
            try:
                # Merge global env with server-specific env
                if ext_settings.global_env:
                    merged_env = dict(ext_settings.global_env)
                    merged_env.update(config.env)
                    config.env = merged_env

                server = await self._external_server_manager.add_server(
                    config,
                    auto_initialize=True,
                )
                results[server.server_id] = True
                logger.info(f"Registered custom external server: {config.server_id}")
            except Exception as e:
                logger.error(f"Failed to register custom server {config.server_id}: {e}")
                results[config.server_id] = False

        return results

    def register_from_registry(self) -> None:
        """Register all servers from the global registry."""
        for server_id, server_class in ServerRegistry.get_all().items():
            if server_id not in self._server_manager.server_ids:
                try:
                    self.register_server_class(server_class)
                except Exception as e:
                    logger.error(f"Failed to register {server_id}: {e}")

    async def initialize(self) -> dict[str, bool]:
        """
        Initialize all registered servers (both internal and external).

        Returns:
            Dict mapping server_id to initialization success
        """
        if self._initialized:
            # Return status of all running servers
            results = {sid: True for sid in self._server_manager.running_servers}
            for server_id in self._external_server_manager._servers:
                server = self._external_server_manager.get_server(server_id)
                if server and server.is_running:
                    results[server_id] = True
            return results

        logger.info("Initializing MCP orchestrator...")

        # Initialize internal Python servers
        internal_results = await self._server_manager.initialize_all()

        # Initialize external MCP servers
        external_results = await self.register_external_servers()

        # Combine results
        results = {**internal_results, **external_results}

        # Refresh tool cache
        self._tool_router.refresh_tool_cache()

        self._initialized = True

        # Log summary
        internal_running = len(self._server_manager.running_servers)
        internal_total = len(self._server_manager.server_ids)
        external_running = sum(1 for s in self._external_server_manager._servers.values() if s.is_running)
        external_total = len(self._external_server_manager._servers)
        total_tools = len(self.get_tools())

        logger.info(
            f"Orchestrator initialized: "
            f"{internal_running}/{internal_total} internal servers, "
            f"{external_running}/{external_total} external servers, "
            f"{total_tools} total tools"
        )

        return results

    async def shutdown(self) -> None:
        """Shutdown all servers (internal and external) and clean up."""
        logger.info("Shutting down MCP orchestrator...")

        # Shutdown internal servers
        await self._server_manager.shutdown_all()

        # Shutdown external servers
        await self._external_server_manager.shutdown_all()

        self._tool_router.clear_cache()
        self._security_manager.reset_context()

        self._initialized = False

        logger.info("Orchestrator shutdown complete")

    # Tool operations

    def get_tools(self) -> list[Tool]:
        """Get all available tools from both internal and external servers."""
        # Get tools from internal servers
        internal_tools = self._tool_router.get_all_tools()

        # Get tools from external servers
        external_tools = self._external_server_manager.get_all_tools()

        # Combine (external tools may overlap with internal if both are registered)
        # Use dict to deduplicate by tool name, preferring external servers
        tool_map = {tool.name: tool for tool in internal_tools}
        for tool in external_tools:
            tool_map[tool.name] = tool

        return list(tool_map.values())

    def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """Get tools in LLM-compatible format."""
        all_tools = self.get_tools()
        return [tool.to_llm_format() for tool in all_tools]

    def get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions."""
        all_tools = self.get_tools()
        descriptions = []
        for tool in all_tools:
            params_str = ", ".join(
                f"{p.name}: {p.type.value}"
                for p in tool.parameters
            )
            descriptions.append(
                f"- {tool.name}({params_str}): {tool.description}"
            )
        return "\n".join(descriptions)

    async def execute_tool(
        self,
        tool_call: ToolCall,
        timeout: float | None = None,
    ) -> ToolResult:
        """
        Execute a tool call (routes to internal or external server automatically).

        Args:
            tool_call: Tool call to execute
            timeout: Optional timeout

        Returns:
            Tool execution result
        """
        if not self._initialized:
            await self.initialize()

        # First check if tool exists on an external server
        external_server = self._external_server_manager.find_tool_server(tool_call.name)
        if external_server:
            return await external_server.call_tool(tool_call.name, tool_call.arguments)

        # Fall back to internal server via tool router
        return await self._tool_router.execute_tool(tool_call, timeout)

    async def execute_tools(
        self,
        tool_calls: list[ToolCall],
        parallel: bool = True,
    ) -> dict[str, ToolResult]:
        """
        Execute multiple tool calls (routes to internal or external servers).

        Args:
            tool_calls: Tool calls to execute
            parallel: Whether to execute in parallel

        Returns:
            Dict mapping tool_call_id to result
        """
        if not self._initialized:
            await self.initialize()

        if parallel:
            # Execute all in parallel
            tasks = [
                self.execute_tool(tool_call)
                for tool_call in tool_calls
            ]
            results_list = await asyncio.gather(*tasks, return_exceptions=True)

            results = {}
            for tool_call, result in zip(tool_calls, results_list):
                if isinstance(result, Exception):
                    results[tool_call.id] = ToolResult.error_result(str(result))
                else:
                    results[tool_call.id] = result
            return results
        else:
            # Execute sequentially
            results = {}
            for tool_call in tool_calls:
                results[tool_call.id] = await self.execute_tool(tool_call)
            return results

    async def call_tool(
        self,
        name: str,
        **arguments: Any,
    ) -> ToolResult:
        """
        Convenience method to call a tool by name (routes automatically).

        Args:
            name: Tool name
            **arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if not self._initialized:
            await self.initialize()

        # First check external servers
        external_server = self._external_server_manager.find_tool_server(name)
        if external_server:
            return await external_server.call_tool(name, arguments)

        # Fall back to internal server
        return await self._tool_router.execute_by_name(name, arguments)

    # Server operations

    def get_server_info(self, server_id: str) -> ServerInfo | None:
        """Get info for a specific server (internal or external)."""
        # Check internal servers first
        info = self._server_manager.get_server_info(server_id)
        if info:
            return info

        # Check external servers
        external_server = self._external_server_manager.get_server(server_id)
        if external_server:
            return ServerInfo(
                server_id=external_server.server_id,
                name=external_server.server_name,
                version=external_server.server_version,
                description=external_server.server_description,
                tool_count=len(external_server.get_tools()),
                status=external_server.status,
            )

        return None

    def get_all_servers(self) -> list[ServerInfo]:
        """Get info for all servers (internal and external)."""
        # Get internal server info
        servers = self._server_manager.get_all_server_info()

        # Add external server info
        for server in self._external_server_manager._servers.values():
            servers.append(ServerInfo(
                server_id=server.server_id,
                name=server.server_name,
                version=server.server_version,
                description=server.server_description,
                tool_count=len(server.get_tools()) if server.is_running else 0,
                status=server.status,
            ))

        return servers

    async def restart_server(self, server_id: str) -> None:
        """Restart a specific server (internal or external)."""
        # Check if it's an internal server
        if server_id in self._server_manager.server_ids:
            await self._server_manager.restart_server(server_id)
            self._tool_router.refresh_tool_cache()
            return

        # Check if it's an external server
        external_server = self._external_server_manager.get_server(server_id)
        if external_server:
            await external_server.shutdown()
            await external_server.initialize()

    # Status and monitoring

    def get_status(self) -> dict[str, Any]:
        """Get orchestrator status (including both internal and external servers)."""
        server_status = self._server_manager.get_status_summary()
        execution_stats = self._tool_router.get_execution_stats()

        # Add external server stats
        external_servers = self._external_server_manager.list_servers()
        external_running = sum(1 for s in external_servers if s["is_running"])
        external_tools = sum(s["tool_count"] for s in external_servers)

        return {
            "initialized": self._initialized,
            "internal_servers": server_status,
            "external_servers": {
                "total": len(external_servers),
                "running": external_running,
                "tools": external_tools,
                "servers": external_servers,
            },
            "tools": {
                "total": len(self.get_tools()),
                "execution_stats": execution_stats,
            },
        }

    def get_health(self) -> dict[str, Any]:
        """Get orchestrator health status."""
        server_status = self._server_manager.get_status_summary()

        external_running = sum(
            1 for s in self._external_server_manager._servers.values()
            if s.is_running
        )

        total_running = server_status["running"] + external_running
        total_tools = len(self.get_tools())

        healthy = (
            self._initialized and
            total_running > 0 and
            server_status["error"] == 0
        )

        return {
            "healthy": healthy,
            "initialized": self._initialized,
            "internal_servers_running": server_status["running"],
            "external_servers_running": external_running,
            "error_servers": server_status["error"],
            "total_tools": total_tools,
        }

    # Context management

    async def __aenter__(self) -> MCPOrchestrator:
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.shutdown()


async def create_orchestrator(
    config: OrchestratorConfig | None = None,
    register_builtin: bool = True,
    auto_initialize: bool = True,
    confirmation_handler: ConfirmationHandler | None = None,
    use_external_servers: bool = True,
) -> MCPOrchestrator:
    """
    Factory function to create and optionally initialize an orchestrator.

    Args:
        config: Orchestrator configuration
        register_builtin: Whether to register built-in servers
        auto_initialize: Whether to initialize immediately
        confirmation_handler: Handler for security confirmations
        use_external_servers: Whether to use external MCP servers (requires npx/node)

    Returns:
        Configured MCPOrchestrator instance
    """
    # If external servers are disabled, update config
    if not use_external_servers and config is None:
        config = OrchestratorConfig(
            external_servers=ExternalServerSettings(
                enabled_official=[],
                use_official_filesystem=False,
                use_official_git=False,
            )
        )
    elif not use_external_servers and config is not None:
        config.external_servers.enabled_official = []
        config.external_servers.use_official_filesystem = False
        config.external_servers.use_official_git = False

    orchestrator = MCPOrchestrator(
        config=config,
        confirmation_handler=confirmation_handler,
    )

    if register_builtin:
        orchestrator.register_builtin_servers()

    if auto_initialize:
        await orchestrator.initialize()

    return orchestrator


async def create_minimal_orchestrator(
    confirmation_handler: ConfirmationHandler | None = None,
) -> MCPOrchestrator:
    """
    Create an orchestrator with only internal Python servers (no external dependencies).

    This is useful for environments without Node.js/npx or for testing.

    Returns:
        MCPOrchestrator with only internal servers
    """
    config = OrchestratorConfig(
        external_servers=ExternalServerSettings(
            enabled_official=[],
            use_official_filesystem=False,
            use_official_git=False,
        )
    )

    return await create_orchestrator(
        config=config,
        register_builtin=True,
        auto_initialize=True,
        confirmation_handler=confirmation_handler,
        use_external_servers=False,
    )


def list_available_official_servers() -> list[dict[str, str]]:
    """
    List all available official MCP servers that can be used.

    Returns:
        List of server info dicts with name, server_id, description
    """
    return ExternalServerManager.list_official_servers()
