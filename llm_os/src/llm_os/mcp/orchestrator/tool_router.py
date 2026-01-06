"""
MCP Tool Router

Routes tool calls to the appropriate MCP server and handles
tool discovery, execution, and result formatting.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from llm_os.mcp.orchestrator.server_manager import ServerManager
from llm_os.mcp.orchestrator.security import SecurityManager, SecurityPolicy
from llm_os.mcp.types.tools import Tool, ToolCall, ToolResult


logger = logging.getLogger(__name__)


class ToolRoutingError(Exception):
    """Error during tool routing."""
    pass


class ToolNotFoundError(ToolRoutingError):
    """Tool not found in any server."""
    pass


class ToolExecutionError(ToolRoutingError):
    """Error during tool execution."""
    pass


@dataclass
class ToolExecutionRecord:
    """Record of a tool execution."""
    tool_call_id: str
    tool_name: str
    server_id: str
    arguments: dict[str, Any]
    result: ToolResult
    started_at: datetime
    completed_at: datetime
    duration_ms: float


@dataclass
class RouterConfig:
    """Configuration for the tool router."""
    max_concurrent_tools: int = 5
    default_timeout: float = 60.0
    retry_on_failure: bool = True
    max_retries: int = 2
    enable_caching: bool = False
    cache_ttl_seconds: float = 300.0


class ToolRouter:
    """
    Routes tool calls to appropriate MCP servers.

    Features:
    - Tool discovery across all servers
    - Intelligent routing based on tool name
    - Concurrent execution support
    - Security integration
    - Execution history tracking
    - Result caching (optional)
    """

    def __init__(
        self,
        server_manager: ServerManager,
        security_manager: SecurityManager | None = None,
        config: RouterConfig | None = None,
    ):
        """
        Initialize tool router.

        Args:
            server_manager: Server manager for accessing servers
            security_manager: Security manager for permission checks
            config: Router configuration
        """
        self.server_manager = server_manager
        self.security_manager = security_manager or SecurityManager()
        self.config = config or RouterConfig()

        self._tool_cache: dict[str, tuple[str, Tool]] = {}  # name -> (server_id, tool)
        self._result_cache: dict[str, tuple[ToolResult, datetime]] = {}
        self._execution_history: list[ToolExecutionRecord] = []
        self._execution_semaphore = asyncio.Semaphore(self.config.max_concurrent_tools)

    def refresh_tool_cache(self) -> None:
        """Refresh the tool name to server mapping cache."""
        self._tool_cache.clear()

        for server_id in self.server_manager.running_servers:
            server = self.server_manager.get_server(server_id)
            if server:
                for tool in server.tools:
                    self._tool_cache[tool.name] = (server_id, tool)

        logger.debug(f"Tool cache refreshed: {len(self._tool_cache)} tools")

    def get_all_tools(self) -> list[Tool]:
        """Get all available tools from running servers."""
        self.refresh_tool_cache()
        return [tool for _, tool in self._tool_cache.values()]

    def get_tools_for_llm(self) -> list[dict[str, Any]]:
        """Get tools in LLM-compatible format."""
        tools = self.get_all_tools()
        return [tool.to_llm_format() for tool in tools]

    def find_tool(self, tool_name: str) -> tuple[str, Tool] | None:
        """
        Find a tool by name.

        Returns (server_id, tool) or None if not found.
        """
        # Check cache first
        if tool_name in self._tool_cache:
            return self._tool_cache[tool_name]

        # Refresh cache and try again
        self.refresh_tool_cache()
        return self._tool_cache.get(tool_name)

    async def execute_tool(
        self,
        tool_call: ToolCall,
        timeout: float | None = None,
    ) -> ToolResult:
        """
        Execute a single tool call.

        Args:
            tool_call: The tool call to execute
            timeout: Execution timeout in seconds

        Returns:
            ToolResult from the execution
        """
        timeout = timeout or self.config.default_timeout
        started_at = datetime.now()

        # Find the tool
        tool_info = self.find_tool(tool_call.name)

        if not tool_info:
            return ToolResult.error_result(
                f"Tool '{tool_call.name}' not found in any running server"
            )

        server_id, tool = tool_info

        # Get the server
        server = self.server_manager.get_server(server_id)
        if not server:
            return ToolResult.error_result(
                f"Server '{server_id}' not available"
            )

        # Check cache if enabled
        if self.config.enable_caching:
            cache_key = self._make_cache_key(tool_call.name, tool_call.arguments)
            cached = self._get_cached_result(cache_key)
            if cached:
                logger.debug(f"Cache hit for {tool_call.name}")
                return cached

        # Acquire semaphore for concurrency control
        async with self._execution_semaphore:
            try:
                # Execute with security checks
                result = await self.security_manager.execute_with_security(
                    tool=tool,
                    arguments=tool_call.arguments,
                    executor=server.call_tool,
                )

                completed_at = datetime.now()
                duration_ms = (completed_at - started_at).total_seconds() * 1000

                # Record execution
                self._record_execution(
                    tool_call=tool_call,
                    server_id=server_id,
                    result=result,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                )

                # Cache result if enabled
                if self.config.enable_caching and result.success:
                    cache_key = self._make_cache_key(tool_call.name, tool_call.arguments)
                    self._cache_result(cache_key, result)

                return result

            except asyncio.TimeoutError:
                return ToolResult.error_result(
                    f"Tool '{tool_call.name}' timed out after {timeout}s"
                )
            except Exception as e:
                logger.error(f"Tool execution error: {e}", exc_info=True)
                return ToolResult.error_result(f"Execution error: {str(e)}")

    async def execute_tool_calls(
        self,
        tool_calls: list[ToolCall],
        parallel: bool = True,
        timeout: float | None = None,
    ) -> dict[str, ToolResult]:
        """
        Execute multiple tool calls.

        Args:
            tool_calls: List of tool calls to execute
            parallel: Whether to execute in parallel
            timeout: Timeout for each call

        Returns:
            Dict mapping tool_call_id to result
        """
        results: dict[str, ToolResult] = {}

        if parallel and len(tool_calls) > 1:
            # Execute in parallel
            tasks = [
                self.execute_tool(tc, timeout)
                for tc in tool_calls
            ]

            completed = await asyncio.gather(*tasks, return_exceptions=True)

            for tool_call, result in zip(tool_calls, completed):
                if isinstance(result, Exception):
                    results[tool_call.id] = ToolResult.error_result(str(result))
                else:
                    results[tool_call.id] = result
        else:
            # Execute sequentially
            for tool_call in tool_calls:
                results[tool_call.id] = await self.execute_tool(tool_call, timeout)

        return results

    async def execute_by_name(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        timeout: float | None = None,
    ) -> ToolResult:
        """
        Execute a tool by name (convenience method).

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            timeout: Execution timeout

        Returns:
            ToolResult from execution
        """
        tool_call = ToolCall(
            id=f"call_{tool_name}_{datetime.now().timestamp()}",
            name=tool_name,
            arguments=arguments,
        )
        return await self.execute_tool(tool_call, timeout)

    def _record_execution(
        self,
        tool_call: ToolCall,
        server_id: str,
        result: ToolResult,
        started_at: datetime,
        completed_at: datetime,
        duration_ms: float,
    ) -> None:
        """Record tool execution in history."""
        record = ToolExecutionRecord(
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            server_id=server_id,
            arguments=tool_call.arguments,
            result=result,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
        )

        self._execution_history.append(record)

        # Keep only recent history
        if len(self._execution_history) > 1000:
            self._execution_history = self._execution_history[-500:]

    def _make_cache_key(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Create a cache key for a tool call."""
        import hashlib
        import json

        args_str = json.dumps(arguments, sort_keys=True)
        hash_input = f"{tool_name}:{args_str}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _get_cached_result(self, cache_key: str) -> ToolResult | None:
        """Get a cached result if valid."""
        if cache_key not in self._result_cache:
            return None

        result, cached_at = self._result_cache[cache_key]
        age = (datetime.now() - cached_at).total_seconds()

        if age > self.config.cache_ttl_seconds:
            del self._result_cache[cache_key]
            return None

        return result

    def _cache_result(self, cache_key: str, result: ToolResult) -> None:
        """Cache a tool result."""
        self._result_cache[cache_key] = (result, datetime.now())

        # Limit cache size
        if len(self._result_cache) > 100:
            # Remove oldest entries
            sorted_keys = sorted(
                self._result_cache.keys(),
                key=lambda k: self._result_cache[k][1]
            )
            for key in sorted_keys[:20]:
                del self._result_cache[key]

    def clear_cache(self) -> None:
        """Clear the result cache."""
        self._result_cache.clear()

    def get_execution_history(
        self,
        limit: int = 50,
        tool_name: str | None = None,
        success_only: bool = False,
    ) -> list[ToolExecutionRecord]:
        """
        Get execution history.

        Args:
            limit: Maximum records to return
            tool_name: Filter by tool name
            success_only: Only return successful executions

        Returns:
            List of execution records
        """
        records = self._execution_history[-limit:]

        if tool_name:
            records = [r for r in records if r.tool_name == tool_name]

        if success_only:
            records = [r for r in records if r.result.success]

        return records

    def get_execution_stats(self) -> dict[str, Any]:
        """Get execution statistics."""
        if not self._execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
            }

        total = len(self._execution_history)
        successful = sum(1 for r in self._execution_history if r.result.success)
        total_duration = sum(r.duration_ms for r in self._execution_history)

        # Stats by tool
        by_tool: dict[str, dict[str, Any]] = {}
        for record in self._execution_history:
            if record.tool_name not in by_tool:
                by_tool[record.tool_name] = {
                    "executions": 0,
                    "successes": 0,
                    "total_duration_ms": 0,
                }
            by_tool[record.tool_name]["executions"] += 1
            if record.result.success:
                by_tool[record.tool_name]["successes"] += 1
            by_tool[record.tool_name]["total_duration_ms"] += record.duration_ms

        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_duration_ms": total_duration / total if total > 0 else 0.0,
            "by_tool": {
                name: {
                    **stats,
                    "success_rate": stats["successes"] / stats["executions"],
                    "average_duration_ms": stats["total_duration_ms"] / stats["executions"],
                }
                for name, stats in by_tool.items()
            },
        }


class ToolDispatcher:
    """
    High-level dispatcher for tool execution.

    Provides a simplified interface for the LLM orchestration layer.
    """

    def __init__(
        self,
        router: ToolRouter,
    ):
        """
        Initialize dispatcher.

        Args:
            router: Tool router for execution
        """
        self.router = router

    async def dispatch(
        self,
        tool_calls: list[ToolCall],
    ) -> list[tuple[str, str]]:
        """
        Dispatch tool calls and return results.

        Args:
            tool_calls: Tool calls from LLM

        Returns:
            List of (tool_call_id, result_text) tuples
        """
        results = await self.router.execute_tool_calls(tool_calls)

        return [
            (tc.id, results[tc.id].get_text())
            for tc in tool_calls
        ]

    async def dispatch_single(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> str:
        """
        Dispatch a single tool call.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Result text
        """
        result = await self.router.execute_by_name(name, arguments)
        return result.get_text()

    def list_tools(self) -> list[dict[str, Any]]:
        """Get all available tools in LLM format."""
        return self.router.get_tools_for_llm()

    def get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions for prompts."""
        tools = self.router.get_all_tools()

        if not tools:
            return "No tools available."

        lines = ["Available tools:\n"]

        for tool in tools:
            lines.append(f"- {tool.name}: {tool.description}")

            if tool.parameters:
                lines.append("  Parameters:")
                for param in tool.parameters:
                    required = "(required)" if param.required else "(optional)"
                    lines.append(f"    - {param.name} [{param.type.value}] {required}: {param.description}")

        return "\n".join(lines)
