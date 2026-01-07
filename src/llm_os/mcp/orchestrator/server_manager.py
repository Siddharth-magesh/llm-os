"""
MCP Server Manager

Manages the lifecycle of MCP servers including registration,
initialization, health monitoring, and shutdown.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Type

from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types.server import (
    ServerConfig,
    ServerStatus,
    ServerState,
    ServerCapabilities,
    ServerInfo,
)
from llm_os.mcp.types.tools import Tool


logger = logging.getLogger(__name__)


class ServerError(Exception):
    """Base exception for server errors."""
    pass


class ServerNotFoundError(ServerError):
    """Server not found."""
    pass


class ServerAlreadyExistsError(ServerError):
    """Server already registered."""
    pass


class ServerInitializationError(ServerError):
    """Server failed to initialize."""
    pass


@dataclass
class ManagedServer:
    """A server managed by the server manager."""
    server: BaseMCPServer
    config: ServerConfig
    status: ServerStatus
    capabilities: ServerCapabilities = field(default_factory=ServerCapabilities)
    health_task: asyncio.Task | None = None


class ServerManager:
    """
    Manages MCP server lifecycle.

    Features:
    - Server registration and discovery
    - Automatic initialization
    - Health monitoring
    - Graceful shutdown
    - Server hot-reload support
    """

    def __init__(
        self,
        health_check_interval: float = 30.0,
        auto_restart: bool = True,
        max_restart_attempts: int = 3,
    ):
        """
        Initialize server manager.

        Args:
            health_check_interval: Seconds between health checks
            auto_restart: Whether to auto-restart failed servers
            max_restart_attempts: Maximum restart attempts before giving up
        """
        self.health_check_interval = health_check_interval
        self.auto_restart = auto_restart
        self.max_restart_attempts = max_restart_attempts

        self._servers: dict[str, ManagedServer] = {}
        self._server_classes: dict[str, Type[BaseMCPServer]] = {}
        self._restart_counts: dict[str, int] = {}
        self._health_monitor_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()

    @property
    def server_ids(self) -> list[str]:
        """Get list of registered server IDs."""
        return list(self._servers.keys())

    @property
    def running_servers(self) -> list[str]:
        """Get list of running server IDs."""
        return [
            sid for sid, ms in self._servers.items()
            if ms.status.state == ServerState.RUNNING
        ]

    def register_server_class(
        self,
        server_id: str,
        server_class: Type[BaseMCPServer],
    ) -> None:
        """
        Register a server class for later instantiation.

        Args:
            server_id: Unique server identifier
            server_class: Server class to instantiate
        """
        self._server_classes[server_id] = server_class
        logger.debug(f"Registered server class: {server_id}")

    def register_server(
        self,
        server: BaseMCPServer,
        config: ServerConfig | None = None,
    ) -> None:
        """
        Register an instantiated server.

        Args:
            server: Server instance
            config: Optional configuration (will use server defaults if not provided)
        """
        server_id = server.server_id

        if server_id in self._servers:
            raise ServerAlreadyExistsError(f"Server '{server_id}' already registered")

        # Create config from server if not provided
        if config is None:
            config = ServerConfig(
                id=server.server_id,
                name=server.server_name,
                description=server.server_description,
                version=server.server_version,
            )

        # Create initial status
        status = ServerStatus(
            server_id=server_id,
            state=ServerState.STOPPED,
            tool_count=len(server.tools),
        )

        self._servers[server_id] = ManagedServer(
            server=server,
            config=config,
            status=status,
        )

        logger.info(f"Registered server: {server_id}")

    def unregister_server(self, server_id: str) -> None:
        """
        Unregister a server.

        Args:
            server_id: Server to unregister
        """
        if server_id not in self._servers:
            raise ServerNotFoundError(f"Server '{server_id}' not found")

        # Ensure server is stopped
        managed = self._servers[server_id]
        if managed.status.state == ServerState.RUNNING:
            raise ServerError(f"Cannot unregister running server '{server_id}'")

        del self._servers[server_id]
        logger.info(f"Unregistered server: {server_id}")

    def get_server(self, server_id: str) -> BaseMCPServer | None:
        """Get a server instance by ID."""
        managed = self._servers.get(server_id)
        return managed.server if managed else None

    def get_server_info(self, server_id: str) -> ServerInfo | None:
        """Get full server info by ID."""
        managed = self._servers.get(server_id)
        if not managed:
            return None

        return ServerInfo(
            config=managed.config,
            status=managed.status,
            capabilities=managed.capabilities,
            tools=[tool.name for tool in managed.server.tools],
        )

    def get_all_server_info(self) -> list[ServerInfo]:
        """Get info for all registered servers."""
        return [
            self.get_server_info(sid)
            for sid in self._servers
            if self.get_server_info(sid) is not None
        ]

    async def initialize_server(self, server_id: str) -> None:
        """
        Initialize a specific server.

        Args:
            server_id: Server to initialize
        """
        if server_id not in self._servers:
            raise ServerNotFoundError(f"Server '{server_id}' not found")

        managed = self._servers[server_id]

        if managed.status.state == ServerState.RUNNING:
            logger.warning(f"Server '{server_id}' already running")
            return

        managed.status.state = ServerState.STARTING

        try:
            await managed.server.initialize()
            managed.status.state = ServerState.RUNNING
            managed.status.started_at = datetime.now()
            managed.status.last_heartbeat = datetime.now()
            managed.status.tool_count = len(managed.server.tools)
            self._restart_counts[server_id] = 0

            logger.info(f"Initialized server: {server_id}")

        except Exception as e:
            managed.status.state = ServerState.ERROR
            managed.status.last_error = str(e)
            managed.status.error_count += 1
            logger.error(f"Failed to initialize server '{server_id}': {e}")
            raise ServerInitializationError(f"Failed to initialize '{server_id}': {e}")

    async def shutdown_server(self, server_id: str) -> None:
        """
        Shutdown a specific server.

        Args:
            server_id: Server to shutdown
        """
        if server_id not in self._servers:
            raise ServerNotFoundError(f"Server '{server_id}' not found")

        managed = self._servers[server_id]

        if managed.status.state != ServerState.RUNNING:
            return

        managed.status.state = ServerState.STOPPING

        try:
            await managed.server.shutdown()
            managed.status.state = ServerState.STOPPED
            managed.status.pid = None
            logger.info(f"Shutdown server: {server_id}")

        except Exception as e:
            managed.status.state = ServerState.ERROR
            managed.status.last_error = str(e)
            logger.error(f"Error shutting down server '{server_id}': {e}")

    async def initialize_all(self) -> dict[str, bool]:
        """
        Initialize all registered servers.

        Returns:
            Dict mapping server_id to success status
        """
        results = {}

        for server_id in self._servers:
            try:
                await self.initialize_server(server_id)
                results[server_id] = True
            except ServerInitializationError:
                results[server_id] = False

        # Start health monitor if not running
        if self._health_monitor_task is None or self._health_monitor_task.done():
            self._health_monitor_task = asyncio.create_task(
                self._health_monitor_loop()
            )

        return results

    async def shutdown_all(self) -> None:
        """Shutdown all running servers."""
        # Stop health monitor
        self._shutdown_event.set()
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass

        # Shutdown servers in parallel
        shutdown_tasks = [
            self.shutdown_server(server_id)
            for server_id in self.running_servers
        ]

        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)

        logger.info("All servers shutdown")

    async def restart_server(self, server_id: str) -> None:
        """
        Restart a server.

        Args:
            server_id: Server to restart
        """
        await self.shutdown_server(server_id)
        await asyncio.sleep(0.5)  # Brief pause
        await self.initialize_server(server_id)

    def get_all_tools(self) -> list[Tool]:
        """Get all tools from all running servers."""
        tools = []

        for server_id in self.running_servers:
            managed = self._servers[server_id]
            tools.extend(managed.server.tools)

        return tools

    def get_tools_by_server(self) -> dict[str, list[Tool]]:
        """Get tools grouped by server ID."""
        result = {}

        for server_id in self.running_servers:
            managed = self._servers[server_id]
            result[server_id] = managed.server.tools

        return result

    def find_tool_server(self, tool_name: str) -> str | None:
        """Find which server provides a tool."""
        for server_id in self.running_servers:
            managed = self._servers[server_id]
            if tool_name in managed.server.tool_names:
                return server_id

        return None

    async def check_server_health(self, server_id: str) -> bool:
        """
        Check health of a specific server.

        Returns True if healthy, False otherwise.
        """
        if server_id not in self._servers:
            return False

        managed = self._servers[server_id]

        if managed.status.state != ServerState.RUNNING:
            return False

        try:
            # Basic health check - just verify server is responsive
            # Servers can override initialize() to perform deeper checks
            managed.status.last_heartbeat = datetime.now()
            return True

        except Exception as e:
            managed.status.last_error = str(e)
            return False

    async def _health_monitor_loop(self) -> None:
        """Background task to monitor server health."""
        logger.debug("Starting health monitor")

        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.health_check_interval)

                for server_id in list(self.running_servers):
                    healthy = await self.check_server_health(server_id)

                    if not healthy and self.auto_restart:
                        # Attempt restart
                        restart_count = self._restart_counts.get(server_id, 0)

                        if restart_count < self.max_restart_attempts:
                            logger.warning(
                                f"Server '{server_id}' unhealthy, "
                                f"attempting restart ({restart_count + 1}/{self.max_restart_attempts})"
                            )
                            self._restart_counts[server_id] = restart_count + 1

                            try:
                                await self.restart_server(server_id)
                            except Exception as e:
                                logger.error(f"Failed to restart '{server_id}': {e}")
                        else:
                            logger.error(
                                f"Server '{server_id}' exceeded max restart attempts, "
                                f"marking as failed"
                            )
                            managed = self._servers[server_id]
                            managed.status.state = ServerState.ERROR

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")

        logger.debug("Health monitor stopped")

    def get_status_summary(self) -> dict[str, Any]:
        """Get summary of all server statuses."""
        summary = {
            "total_servers": len(self._servers),
            "running": 0,
            "stopped": 0,
            "error": 0,
            "total_tools": 0,
            "servers": {},
        }

        for server_id, managed in self._servers.items():
            state = managed.status.state

            if state == ServerState.RUNNING:
                summary["running"] += 1
                summary["total_tools"] += len(managed.server.tools)
            elif state == ServerState.STOPPED:
                summary["stopped"] += 1
            elif state == ServerState.ERROR:
                summary["error"] += 1

            summary["servers"][server_id] = {
                "state": state.value,
                "tools": len(managed.server.tools),
                "uptime_seconds": managed.status.uptime_seconds,
                "error_count": managed.status.error_count,
                "last_error": managed.status.last_error,
            }

        return summary


class ServerRegistry:
    """
    Registry of available server classes.

    Allows dynamic server discovery and instantiation.
    """

    _instance: ServerRegistry | None = None
    _servers: dict[str, Type[BaseMCPServer]] = {}

    def __new__(cls) -> ServerRegistry:
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, server_class: Type[BaseMCPServer]) -> Type[BaseMCPServer]:
        """
        Register a server class (can be used as decorator).

        Usage:
            @ServerRegistry.register
            class MyServer(BaseMCPServer):
                server_id = "my_server"
                ...
        """
        server_id = server_class.server_id
        cls._servers[server_id] = server_class
        logger.debug(f"Registered server in registry: {server_id}")
        return server_class

    @classmethod
    def get(cls, server_id: str) -> Type[BaseMCPServer] | None:
        """Get a server class by ID."""
        return cls._servers.get(server_id)

    @classmethod
    def get_all(cls) -> dict[str, Type[BaseMCPServer]]:
        """Get all registered server classes."""
        return cls._servers.copy()

    @classmethod
    def create(cls, server_id: str, **kwargs: Any) -> BaseMCPServer | None:
        """Create a server instance by ID."""
        server_class = cls.get(server_id)
        if server_class:
            return server_class(**kwargs)
        return None

    @classmethod
    def clear(cls) -> None:
        """Clear all registered servers."""
        cls._servers.clear()
