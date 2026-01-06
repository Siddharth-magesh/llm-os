"""
Base MCP Server

Abstract base class for all MCP servers in LLM-OS.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from llm_os.mcp.types.tools import Tool, ToolResult, ToolParameter, ParameterType


logger = logging.getLogger(__name__)


# Type alias for tool handlers
ToolHandler = Callable[..., Coroutine[Any, Any, ToolResult]]


@dataclass
class RegisteredTool:
    """A tool registered with a server."""
    tool: Tool
    handler: ToolHandler


class BaseMCPServer(ABC):
    """
    Abstract base class for MCP servers.

    Subclasses should:
    1. Set server_id and server_name class attributes
    2. Call register_tool() in __init__ to register tools
    3. Implement tool handler methods
    """

    server_id: str = "base"
    server_name: str = "Base Server"
    server_version: str = "1.0.0"
    server_description: str = "Base MCP server"

    def __init__(self):
        """Initialize the server."""
        self._tools: dict[str, RegisteredTool] = {}
        self._initialized = False

    @property
    def tools(self) -> list[Tool]:
        """Get list of registered tools."""
        return [rt.tool for rt in self._tools.values()]

    @property
    def tool_names(self) -> list[str]:
        """Get list of tool names."""
        return list(self._tools.keys())

    def register_tool(
        self,
        name: str,
        description: str,
        handler: ToolHandler,
        parameters: list[ToolParameter] | None = None,
        requires_confirmation: bool = False,
        permission_level: str = "read",
    ) -> None:
        """
        Register a tool with the server.

        Args:
            name: Tool name (should be unique within server)
            description: Tool description for the LLM
            handler: Async function to handle tool calls
            parameters: List of parameter definitions
            requires_confirmation: Whether to confirm before execution
            permission_level: Permission level required
        """
        tool = Tool(
            name=name,
            description=description,
            parameters=parameters or [],
            server_id=self.server_id,
            requires_confirmation=requires_confirmation,
            permission_level=permission_level,
        )

        self._tools[name] = RegisteredTool(tool=tool, handler=handler)
        logger.debug(f"Registered tool: {name} on server {self.server_id}")

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name."""
        registered = self._tools.get(name)
        return registered.tool if registered else None

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """
        Call a tool by name with the given arguments.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            ToolResult with the outcome
        """
        registered = self._tools.get(name)

        if not registered:
            return ToolResult.error_result(f"Unknown tool: {name}")

        # Validate arguments
        is_valid, error = registered.tool.validate_arguments(arguments)
        if not is_valid:
            return ToolResult.error_result(f"Invalid arguments: {error}")

        try:
            result = await registered.handler(**arguments)
            return result
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}", exc_info=True)
            return ToolResult.error_result(f"Tool execution failed: {str(e)}")

    async def initialize(self) -> None:
        """
        Initialize the server.

        Override this method to perform async initialization.
        """
        self._initialized = True

    async def shutdown(self) -> None:
        """
        Shutdown the server.

        Override this method to perform cleanup.
        """
        self._initialized = False

    @abstractmethod
    def _register_tools(self) -> None:
        """
        Register all tools for this server.

        Subclasses must implement this method and call register_tool()
        for each tool they provide.
        """
        pass

    def get_server_info(self) -> dict[str, Any]:
        """Get server information."""
        return {
            "id": self.server_id,
            "name": self.server_name,
            "version": self.server_version,
            "description": self.server_description,
            "tools": [tool.name for tool in self.tools],
            "tool_count": len(self._tools),
            "initialized": self._initialized,
        }

    # Helper methods for creating parameters

    @staticmethod
    def string_param(
        name: str,
        description: str,
        required: bool = True,
        default: str | None = None,
        enum: list[str] | None = None,
    ) -> ToolParameter:
        """Create a string parameter."""
        return ToolParameter(
            name=name,
            type=ParameterType.STRING,
            description=description,
            required=required,
            default=default,
            enum=enum,
        )

    @staticmethod
    def number_param(
        name: str,
        description: str,
        required: bool = True,
        default: float | None = None,
    ) -> ToolParameter:
        """Create a number parameter."""
        return ToolParameter(
            name=name,
            type=ParameterType.NUMBER,
            description=description,
            required=required,
            default=default,
        )

    @staticmethod
    def integer_param(
        name: str,
        description: str,
        required: bool = True,
        default: int | None = None,
    ) -> ToolParameter:
        """Create an integer parameter."""
        return ToolParameter(
            name=name,
            type=ParameterType.INTEGER,
            description=description,
            required=required,
            default=default,
        )

    @staticmethod
    def boolean_param(
        name: str,
        description: str,
        required: bool = False,
        default: bool = False,
    ) -> ToolParameter:
        """Create a boolean parameter."""
        return ToolParameter(
            name=name,
            type=ParameterType.BOOLEAN,
            description=description,
            required=required,
            default=default,
        )

    @staticmethod
    def array_param(
        name: str,
        description: str,
        item_type: ParameterType = ParameterType.STRING,
        required: bool = True,
    ) -> ToolParameter:
        """Create an array parameter."""
        return ToolParameter(
            name=name,
            type=ParameterType.ARRAY,
            description=description,
            required=required,
            items={"type": item_type.value},
        )
