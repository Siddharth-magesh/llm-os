"""
External MCP Server Wrapper - Adapts external MCP servers to our BaseMCPServer interface.

This module provides a wrapper that makes external MCP servers (running via stdio)
compatible with our internal MCP server interface, allowing seamless integration
of official and third-party MCP servers.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from llm_os.mcp.types.tools import (
    Tool,
    ToolParameter,
    ToolResult,
    ToolContent,
    ParameterType,
)
from llm_os.mcp.types.server import ServerConfig, ServerStatus, ServerState
from llm_os.mcp.client.stdio_client import StdioMCPClient, ToolDefinition

logger = logging.getLogger(__name__)


@dataclass
class ExternalServerConfig:
    """Configuration for an external MCP server."""
    server_id: str
    name: str
    description: str
    command: str | list[str]
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    timeout: float = 30.0
    auto_start: bool = True
    enabled: bool = True


# Pre-defined configurations for MCP servers
OFFICIAL_SERVERS: dict[str, ExternalServerConfig] = {
    "filesystem": ExternalServerConfig(
        server_id="mcp-filesystem",
        name="OSSARTH Filesystem Server",
        description="Local filesystem server with OSSARTH customizations",
        command="node",
        args=[
            str(Path(__file__).parent.parent / "external-servers" / "filesystem" / "dist" / "index.js"),
            str(Path.cwd())  # Allow current working directory
        ],
        env={},
    ),
    # Additional external servers can be added here as needed
    # For now, we only use the local filesystem server
}


def _json_schema_to_parameter_type(json_type: str) -> ParameterType:
    """Convert JSON schema type to ParameterType."""
    type_map = {
        "string": ParameterType.STRING,
        "number": ParameterType.NUMBER,
        "integer": ParameterType.INTEGER,
        "boolean": ParameterType.BOOLEAN,
        "array": ParameterType.ARRAY,
        "object": ParameterType.OBJECT,
    }
    return type_map.get(json_type, ParameterType.STRING)


def _tool_definition_to_tool(
    tool_def: ToolDefinition,
    server_id: str,
) -> Tool:
    """Convert MCP ToolDefinition to our Tool type."""
    parameters: list[ToolParameter] = []
    schema = tool_def.input_schema

    if schema and "properties" in schema:
        required = set(schema.get("required", []))

        for name, prop in schema["properties"].items():
            param_type = _json_schema_to_parameter_type(prop.get("type", "string"))

            parameters.append(ToolParameter(
                name=name,
                type=param_type,
                description=prop.get("description", ""),
                required=name in required,
                default=prop.get("default"),
                enum=prop.get("enum"),
                items=prop.get("items"),
            ))

    return Tool(
        name=tool_def.name,
        description=tool_def.description,
        parameters=parameters,
        server_id=server_id,
        requires_confirmation=False,  # External servers handle their own security
        permission_level="read",  # Default, may be overridden
    )


class ExternalMCPServer:
    """
    Wrapper for external MCP servers that provides a consistent interface.

    This class wraps an external MCP server (running via stdio) and adapts it
    to work with our internal orchestration system. It handles:
    - Server lifecycle management (start/stop)
    - Tool discovery and conversion
    - Tool execution and result translation
    """

    def __init__(
        self,
        config: ExternalServerConfig,
    ):
        """
        Initialize external server wrapper.

        Args:
            config: Server configuration
        """
        self.config = config
        self._client: StdioMCPClient | None = None
        self._tools: dict[str, Tool] = {}
        self._status = ServerStatus(
            state=ServerState.STOPPED,
            server_id=config.server_id,
        )

    @property
    def server_id(self) -> str:
        return self.config.server_id

    @property
    def server_name(self) -> str:
        return self.config.name

    @property
    def server_description(self) -> str:
        return self.config.description

    @property
    def server_version(self) -> str:
        if self._client and self._client._server_info:
            return self._client._server_info.get("version", "1.0.0")
        return "1.0.0"

    @property
    def status(self) -> ServerStatus:
        return self._status

    @property
    def is_running(self) -> bool:
        return self._client is not None and self._client.is_initialized

    async def initialize(self) -> None:
        """Initialize and connect to the external server."""
        if self.is_running:
            return

        self._status = ServerStatus(
            state=ServerState.STARTING,
            server_id=self.server_id,
        )

        try:
            # Create and initialize client
            self._client = StdioMCPClient(
                command=self.config.command,
                args=self.config.args,
                env=self.config.env,
                cwd=self.config.cwd,
                timeout=self.config.timeout,
            )

            await self._client.initialize()

            # Convert tools
            self._tools = {
                tool_def.name: _tool_definition_to_tool(tool_def, self.server_id)
                for tool_def in self._client.tools
            }

            self._status = ServerStatus(
                state=ServerState.RUNNING,
                server_id=self.server_id,
                tool_count=len(self._tools),
            )

            logger.info(
                f"External server '{self.server_name}' initialized with "
                f"{len(self._tools)} tools"
            )

        except Exception as e:
            self._status = ServerStatus(
                state=ServerState.ERROR,
                server_id=self.server_id,
                error=str(e),
            )
            logger.error(f"Failed to initialize external server '{self.server_name}': {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the external server."""
        if self._client:
            await self._client.close()
            self._client = None

        self._tools.clear()
        self._status = ServerStatus(
            state=ServerState.STOPPED,
            server_id=self.server_id,
        )

        logger.info(f"External server '{self.server_name}' shutdown")

    def get_tools(self) -> list[Tool]:
        """Get all available tools."""
        return list(self._tools.values())

    def get_tool(self, name: str) -> Tool | None:
        """Get a specific tool by name."""
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        """Check if a tool exists."""
        return name in self._tools

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        """
        Call a tool on the external server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            ToolResult with execution result
        """
        if not self.is_running:
            return ToolResult.error_result(
                f"Server '{self.server_name}' is not running"
            )

        if not self.has_tool(name):
            return ToolResult.error_result(
                f"Tool '{name}' not found on server '{self.server_name}'"
            )

        try:
            result = await self._client.call_tool(name, arguments)

            # Convert MCP result to our ToolResult format
            if result.get("isError"):
                content = result.get("content", [])
                error_text = ""
                for item in content:
                    if item.get("type") == "text":
                        error_text += item.get("text", "")
                return ToolResult.error_result(error_text or "Unknown error")

            # Parse content
            contents: list[ToolContent] = []
            for item in result.get("content", []):
                item_type = item.get("type", "text")
                if item_type == "text":
                    contents.append(ToolContent(
                        type="text",
                        text=item.get("text", "")
                    ))
                elif item_type == "image":
                    contents.append(ToolContent(
                        type="image",
                        data=item.get("data", ""),
                        mime_type=item.get("mimeType", "image/png")
                    ))
                elif item_type == "resource":
                    contents.append(ToolContent(
                        type="resource",
                        resource=item.get("resource", {})
                    ))

            if not contents:
                contents = [ToolContent(type="text", text="Success")]

            return ToolResult(
                success=True,
                content=contents,
                metadata={"server_id": self.server_id}
            )

        except Exception as e:
            logger.error(f"Tool call error on '{self.server_name}': {e}")
            return ToolResult.error_result(str(e))


class ExternalServerManager:
    """
    Manager for multiple external MCP servers.

    Handles discovery, initialization, and lifecycle of external servers.
    """

    def __init__(self):
        self._servers: dict[str, ExternalMCPServer] = {}
        self._lock = asyncio.Lock()

    async def add_server(
        self,
        config: ExternalServerConfig,
        auto_initialize: bool = True,
    ) -> ExternalMCPServer:
        """Add an external server."""
        async with self._lock:
            if config.server_id in self._servers:
                return self._servers[config.server_id]

            server = ExternalMCPServer(config)

            if auto_initialize and config.enabled:
                await server.initialize()

            self._servers[config.server_id] = server
            return server

    async def add_official_server(
        self,
        server_name: str,
        auto_initialize: bool = True,
        **overrides: Any,
    ) -> ExternalMCPServer | None:
        """
        Add an official MCP server by name.

        Args:
            server_name: Name of official server (e.g., "filesystem", "git")
            auto_initialize: Whether to initialize immediately
            **overrides: Override config values

        Returns:
            ExternalMCPServer or None if not found
        """
        if server_name not in OFFICIAL_SERVERS:
            logger.warning(f"Unknown official server: {server_name}")
            return None

        config = OFFICIAL_SERVERS[server_name]

        # Apply overrides
        if overrides:
            config_dict = {
                "server_id": config.server_id,
                "name": config.name,
                "description": config.description,
                "command": config.command,
                "args": list(config.args),
                "env": dict(config.env),
                "cwd": config.cwd,
                "timeout": config.timeout,
                "auto_start": config.auto_start,
                "enabled": config.enabled,
            }
            config_dict.update(overrides)
            config = ExternalServerConfig(**config_dict)

        return await self.add_server(config, auto_initialize)

    def get_server(self, server_id: str) -> ExternalMCPServer | None:
        """Get a server by ID."""
        return self._servers.get(server_id)

    async def remove_server(self, server_id: str) -> None:
        """Remove and shutdown a server."""
        async with self._lock:
            server = self._servers.pop(server_id, None)
            if server:
                await server.shutdown()

    async def initialize_all(self) -> dict[str, bool]:
        """Initialize all registered servers."""
        results = {}
        for server_id, server in self._servers.items():
            try:
                if not server.is_running and server.config.enabled:
                    await server.initialize()
                results[server_id] = True
            except Exception as e:
                logger.error(f"Failed to initialize {server_id}: {e}")
                results[server_id] = False
        return results

    async def shutdown_all(self) -> None:
        """Shutdown all servers."""
        async with self._lock:
            for server in self._servers.values():
                await server.shutdown()

    def get_all_tools(self) -> list[Tool]:
        """Get all tools from all running servers."""
        tools = []
        for server in self._servers.values():
            if server.is_running:
                tools.extend(server.get_tools())
        return tools

    def find_tool_server(self, tool_name: str) -> ExternalMCPServer | None:
        """Find which server provides a given tool."""
        for server in self._servers.values():
            if server.is_running and server.has_tool(tool_name):
                return server
        return None

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        """Call a tool, automatically routing to the correct server."""
        server = self.find_tool_server(tool_name)
        if not server:
            return ToolResult.error_result(f"No server found for tool '{tool_name}'")

        return await server.call_tool(tool_name, arguments)

    def list_servers(self) -> list[dict[str, Any]]:
        """List all registered servers and their status."""
        return [
            {
                "server_id": server.server_id,
                "name": server.server_name,
                "description": server.server_description,
                "is_running": server.is_running,
                "tool_count": len(server.get_tools()) if server.is_running else 0,
                "status": server.status.state.value,
            }
            for server in self._servers.values()
        ]

    @staticmethod
    def list_official_servers() -> list[dict[str, str]]:
        """List available official MCP servers."""
        return [
            {
                "name": name,
                "server_id": config.server_id,
                "description": config.description,
            }
            for name, config in OFFICIAL_SERVERS.items()
        ]
