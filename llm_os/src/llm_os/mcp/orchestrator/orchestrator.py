"""
MCP Orchestrator

Main orchestration layer that coordinates servers, tools, and security.
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


logger = logging.getLogger(__name__)


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

    # Paths
    custom_servers_path: Path | None = None


class MCPOrchestrator:
    """
    Main MCP orchestration layer.

    Coordinates:
    - Server lifecycle management
    - Tool discovery and routing
    - Security enforcement
    - Health monitoring

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

        self._tool_router = ToolRouter(
            server_manager=self._server_manager,
            security_manager=self._security_manager,
            config=self.config.router_config,
        )

        self._dispatcher = ToolDispatcher(self._tool_router)
        self._initialized = False

    @property
    def server_manager(self) -> ServerManager:
        """Get the server manager."""
        return self._server_manager

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
        """Register all built-in MCP servers."""
        # Import built-in servers
        from llm_os.mcp.servers.filesystem import FilesystemServer
        from llm_os.mcp.servers.applications import ApplicationsServer
        from llm_os.mcp.servers.process import ProcessServer
        from llm_os.mcp.servers.system import SystemServer
        from llm_os.mcp.servers.git import GitServer

        # Register each server
        builtin_servers = [
            FilesystemServer,
            ApplicationsServer,
            ProcessServer,
            SystemServer,
            GitServer,
        ]

        for server_class in builtin_servers:
            try:
                self.register_server_class(server_class)
                logger.info(f"Registered built-in server: {server_class.server_id}")
            except Exception as e:
                logger.error(f"Failed to register {server_class.server_id}: {e}")

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
        Initialize all registered servers.

        Returns:
            Dict mapping server_id to initialization success
        """
        if self._initialized:
            return {sid: True for sid in self._server_manager.running_servers}

        logger.info("Initializing MCP orchestrator...")

        # Initialize all servers
        results = await self._server_manager.initialize_all()

        # Refresh tool cache
        self._tool_router.refresh_tool_cache()

        self._initialized = True

        # Log summary
        running = len(self._server_manager.running_servers)
        total = len(self._server_manager.server_ids)
        logger.info(f"Orchestrator initialized: {running}/{total} servers running")

        return results

    async def shutdown(self) -> None:
        """Shutdown all servers and clean up."""
        logger.info("Shutting down MCP orchestrator...")

        await self._server_manager.shutdown_all()
        self._tool_router.clear_cache()
        self._security_manager.reset_context()

        self._initialized = False

        logger.info("Orchestrator shutdown complete")

    # Tool operations

    def get_tools(self) -> list[Tool]:
        """Get all available tools."""
        return self._tool_router.get_all_tools()

    def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """Get tools in LLM-compatible format."""
        return self._tool_router.get_tools_for_llm()

    def get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions."""
        return self._dispatcher.get_tool_descriptions()

    async def execute_tool(
        self,
        tool_call: ToolCall,
        timeout: float | None = None,
    ) -> ToolResult:
        """
        Execute a tool call.

        Args:
            tool_call: Tool call to execute
            timeout: Optional timeout

        Returns:
            Tool execution result
        """
        if not self._initialized:
            await self.initialize()

        return await self._tool_router.execute_tool(tool_call, timeout)

    async def execute_tools(
        self,
        tool_calls: list[ToolCall],
        parallel: bool = True,
    ) -> dict[str, ToolResult]:
        """
        Execute multiple tool calls.

        Args:
            tool_calls: Tool calls to execute
            parallel: Whether to execute in parallel

        Returns:
            Dict mapping tool_call_id to result
        """
        if not self._initialized:
            await self.initialize()

        return await self._tool_router.execute_tool_calls(tool_calls, parallel)

    async def call_tool(
        self,
        name: str,
        **arguments: Any,
    ) -> ToolResult:
        """
        Convenience method to call a tool by name.

        Args:
            name: Tool name
            **arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if not self._initialized:
            await self.initialize()

        return await self._tool_router.execute_by_name(name, arguments)

    # Server operations

    def get_server_info(self, server_id: str) -> ServerInfo | None:
        """Get info for a specific server."""
        return self._server_manager.get_server_info(server_id)

    def get_all_servers(self) -> list[ServerInfo]:
        """Get info for all servers."""
        return self._server_manager.get_all_server_info()

    async def restart_server(self, server_id: str) -> None:
        """Restart a specific server."""
        await self._server_manager.restart_server(server_id)
        self._tool_router.refresh_tool_cache()

    # Status and monitoring

    def get_status(self) -> dict[str, Any]:
        """Get orchestrator status."""
        server_status = self._server_manager.get_status_summary()
        execution_stats = self._tool_router.get_execution_stats()

        return {
            "initialized": self._initialized,
            "servers": server_status,
            "tools": {
                "total": len(self._tool_router.get_all_tools()),
                "execution_stats": execution_stats,
            },
        }

    def get_health(self) -> dict[str, Any]:
        """Get orchestrator health status."""
        server_status = self._server_manager.get_status_summary()

        healthy = (
            self._initialized and
            server_status["running"] > 0 and
            server_status["error"] == 0
        )

        return {
            "healthy": healthy,
            "initialized": self._initialized,
            "running_servers": server_status["running"],
            "error_servers": server_status["error"],
            "total_tools": server_status["total_tools"],
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
) -> MCPOrchestrator:
    """
    Factory function to create and optionally initialize an orchestrator.

    Args:
        config: Orchestrator configuration
        register_builtin: Whether to register built-in servers
        auto_initialize: Whether to initialize immediately
        confirmation_handler: Handler for security confirmations

    Returns:
        Configured MCPOrchestrator instance
    """
    orchestrator = MCPOrchestrator(
        config=config,
        confirmation_handler=confirmation_handler,
    )

    if register_builtin:
        orchestrator.register_builtin_servers()

    if auto_initialize:
        await orchestrator.initialize()

    return orchestrator
