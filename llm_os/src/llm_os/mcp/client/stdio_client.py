"""
MCP Stdio Client - Communicates with external MCP servers via JSON-RPC over stdio.

This module implements the Model Context Protocol (MCP) client for communicating
with external MCP servers that run as separate processes using stdin/stdout.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncIterator
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MCPRequest:
    """JSON-RPC 2.0 request for MCP."""
    method: str
    params: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_json(self) -> str:
        """Convert to JSON-RPC 2.0 format."""
        return json.dumps({
            "jsonrpc": "2.0",
            "method": self.method,
            "params": self.params,
            "id": self.id
        })


@dataclass
class MCPResponse:
    """JSON-RPC 2.0 response from MCP server."""
    id: str
    result: Any = None
    error: dict[str, Any] | None = None

    @classmethod
    def from_json(cls, data: str | dict) -> MCPResponse:
        """Parse from JSON-RPC 2.0 response."""
        if isinstance(data, str):
            data = json.loads(data)
        return cls(
            id=data.get("id", ""),
            result=data.get("result"),
            error=data.get("error")
        )

    @property
    def is_error(self) -> bool:
        return self.error is not None


@dataclass
class MCPNotification:
    """JSON-RPC 2.0 notification (no response expected)."""
    method: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Convert to JSON-RPC 2.0 notification format."""
        return json.dumps({
            "jsonrpc": "2.0",
            "method": self.method,
            "params": self.params
        })


@dataclass
class ServerCapabilities:
    """MCP server capabilities."""
    tools: bool = False
    resources: bool = False
    prompts: bool = False
    logging: bool = False
    experimental: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    """Tool definition from MCP server."""
    name: str
    description: str
    input_schema: dict[str, Any]


class StdioMCPClient:
    """
    Client for communicating with MCP servers over stdio.

    This client spawns an external MCP server process and communicates
    with it using JSON-RPC 2.0 over stdin/stdout.
    """

    def __init__(
        self,
        command: str | list[str],
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        cwd: str | Path | None = None,
        timeout: float = 30.0,
    ):
        """
        Initialize stdio MCP client.

        Args:
            command: Command to run (e.g., "npx" or ["node", "server.js"])
            args: Additional command arguments
            env: Environment variables to set
            cwd: Working directory for the server process
            timeout: Default timeout for requests
        """
        if isinstance(command, str):
            self._command = [command]
        else:
            self._command = list(command)

        if args:
            self._command.extend(args)

        self._env = {**os.environ, **(env or {})}
        self._cwd = Path(cwd) if cwd else None
        self._timeout = timeout

        self._process: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task | None = None
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._notification_handlers: dict[str, list[callable]] = {}
        self._initialized = False
        self._capabilities: ServerCapabilities | None = None
        self._server_info: dict[str, Any] = {}
        self._tools: list[ToolDefinition] = []
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """Check if connected to server."""
        return (
            self._process is not None
            and self._process.returncode is None
        )

    @property
    def is_initialized(self) -> bool:
        """Check if server is initialized."""
        return self._initialized

    @property
    def capabilities(self) -> ServerCapabilities | None:
        """Get server capabilities."""
        return self._capabilities

    @property
    def tools(self) -> list[ToolDefinition]:
        """Get available tools."""
        return self._tools

    async def connect(self) -> None:
        """Start the server process and establish connection."""
        if self.is_connected:
            return

        logger.info(f"Starting MCP server: {' '.join(self._command)}")

        try:
            self._process = await asyncio.create_subprocess_exec(
                *self._command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._env,
                cwd=self._cwd,
            )

            # Start reader task
            self._reader_task = asyncio.create_task(self._read_loop())

            logger.info(f"MCP server started with PID {self._process.pid}")

        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise ConnectionError(f"Failed to start MCP server: {e}")

    async def initialize(
        self,
        client_info: dict[str, str] | None = None,
    ) -> ServerCapabilities:
        """
        Initialize the MCP connection.

        Args:
            client_info: Client information to send to server

        Returns:
            Server capabilities
        """
        if not self.is_connected:
            await self.connect()

        if self._initialized:
            return self._capabilities

        client_info = client_info or {
            "name": "llm-os",
            "version": "0.1.0"
        }

        response = await self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": client_info
            }
        )

        if response.is_error:
            raise RuntimeError(f"Failed to initialize: {response.error}")

        result = response.result or {}

        # Parse capabilities
        caps = result.get("capabilities", {})
        self._capabilities = ServerCapabilities(
            tools="tools" in caps,
            resources="resources" in caps,
            prompts="prompts" in caps,
            logging="logging" in caps,
            experimental=caps.get("experimental", {})
        )

        self._server_info = result.get("serverInfo", {})

        # Send initialized notification
        await self._notify("notifications/initialized", {})

        self._initialized = True

        # Fetch tools if available
        if self._capabilities.tools:
            await self._fetch_tools()

        logger.info(
            f"MCP server initialized: {self._server_info.get('name', 'unknown')} "
            f"v{self._server_info.get('version', 'unknown')}"
        )

        return self._capabilities

    async def _fetch_tools(self) -> None:
        """Fetch available tools from server."""
        response = await self._request("tools/list", {})

        if response.is_error:
            logger.warning(f"Failed to fetch tools: {response.error}")
            return

        tools_data = response.result.get("tools", [])
        self._tools = [
            ToolDefinition(
                name=t["name"],
                description=t.get("description", ""),
                input_schema=t.get("inputSchema", {})
            )
            for t in tools_data
        ]

        logger.info(f"Fetched {len(self._tools)} tools from server")

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """
        Call a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments
            timeout: Request timeout (uses default if not specified)

        Returns:
            Tool result
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        response = await self._request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments or {}
            },
            timeout=timeout
        )

        if response.is_error:
            return {
                "isError": True,
                "content": [{"type": "text", "text": str(response.error)}]
            }

        return response.result

    async def list_resources(self) -> list[dict[str, Any]]:
        """List available resources."""
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        if not self._capabilities or not self._capabilities.resources:
            return []

        response = await self._request("resources/list", {})

        if response.is_error:
            logger.warning(f"Failed to list resources: {response.error}")
            return []

        return response.result.get("resources", [])

    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Read a resource by URI."""
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        response = await self._request("resources/read", {"uri": uri})

        if response.is_error:
            raise RuntimeError(f"Failed to read resource: {response.error}")

        return response.result

    async def list_prompts(self) -> list[dict[str, Any]]:
        """List available prompts."""
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        if not self._capabilities or not self._capabilities.prompts:
            return []

        response = await self._request("prompts/list", {})

        if response.is_error:
            logger.warning(f"Failed to list prompts: {response.error}")
            return []

        return response.result.get("prompts", [])

    async def get_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Get a prompt by name."""
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        response = await self._request(
            "prompts/get",
            {"name": name, "arguments": arguments or {}}
        )

        if response.is_error:
            raise RuntimeError(f"Failed to get prompt: {response.error}")

        return response.result

    def on_notification(self, method: str, handler: callable) -> None:
        """Register a notification handler."""
        if method not in self._notification_handlers:
            self._notification_handlers[method] = []
        self._notification_handlers[method].append(handler)

    async def close(self) -> None:
        """Close the connection and stop the server process."""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        if self._process:
            # Send graceful shutdown
            try:
                self._process.terminate()
                await asyncio.wait_for(
                    self._process.wait(),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()

            self._process = None

        self._initialized = False
        self._pending_requests.clear()

        logger.info("MCP client closed")

    async def _request(
        self,
        method: str,
        params: dict[str, Any],
        timeout: float | None = None,
    ) -> MCPResponse:
        """Send a request and wait for response."""
        if not self.is_connected:
            raise RuntimeError("Not connected to server")

        request = MCPRequest(method=method, params=params)
        timeout = timeout or self._timeout

        # Create future for response
        future: asyncio.Future[MCPResponse] = asyncio.Future()
        self._pending_requests[request.id] = future

        try:
            # Send request
            await self._write(request.to_json())

            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout)
            return response

        except asyncio.TimeoutError:
            self._pending_requests.pop(request.id, None)
            return MCPResponse(
                id=request.id,
                error={"code": -32000, "message": "Request timeout"}
            )
        except Exception as e:
            self._pending_requests.pop(request.id, None)
            return MCPResponse(
                id=request.id,
                error={"code": -32000, "message": str(e)}
            )

    async def _notify(self, method: str, params: dict[str, Any]) -> None:
        """Send a notification (no response expected)."""
        if not self.is_connected:
            raise RuntimeError("Not connected to server")

        notification = MCPNotification(method=method, params=params)
        await self._write(notification.to_json())

    async def _write(self, message: str) -> None:
        """Write a message to the server."""
        async with self._lock:
            if self._process and self._process.stdin:
                data = message.encode() + b"\n"
                self._process.stdin.write(data)
                await self._process.stdin.drain()
                logger.debug(f"Sent: {message[:200]}...")

    async def _read_loop(self) -> None:
        """Read responses from server."""
        if not self._process or not self._process.stdout:
            return

        try:
            while True:
                line = await self._process.stdout.readline()
                if not line:
                    break

                try:
                    message = line.decode().strip()
                    if not message:
                        continue

                    logger.debug(f"Received: {message[:200]}...")

                    data = json.loads(message)

                    # Check if it's a response or notification
                    if "id" in data:
                        # Response to a request
                        response = MCPResponse.from_json(data)
                        future = self._pending_requests.pop(response.id, None)
                        if future and not future.done():
                            future.set_result(response)
                    else:
                        # Notification from server
                        method = data.get("method", "")
                        params = data.get("params", {})
                        await self._handle_notification(method, params)

                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from server: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Read loop error: {e}")
        finally:
            # Cancel pending requests
            for future in self._pending_requests.values():
                if not future.done():
                    future.set_exception(ConnectionError("Connection closed"))

    async def _handle_notification(
        self,
        method: str,
        params: dict[str, Any],
    ) -> None:
        """Handle a notification from server."""
        handlers = self._notification_handlers.get(method, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(params)
                else:
                    handler(params)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")


class MCPClientPool:
    """
    Pool of MCP clients for managing multiple server connections.
    """

    def __init__(self):
        self._clients: dict[str, StdioMCPClient] = {}
        self._lock = asyncio.Lock()

    async def add_client(
        self,
        server_id: str,
        command: str | list[str],
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        cwd: str | Path | None = None,
        auto_initialize: bool = True,
    ) -> StdioMCPClient:
        """Add and optionally initialize a new client."""
        async with self._lock:
            if server_id in self._clients:
                return self._clients[server_id]

            client = StdioMCPClient(
                command=command,
                args=args,
                env=env,
                cwd=cwd,
            )

            if auto_initialize:
                await client.initialize()

            self._clients[server_id] = client
            return client

    def get_client(self, server_id: str) -> StdioMCPClient | None:
        """Get a client by server ID."""
        return self._clients.get(server_id)

    async def remove_client(self, server_id: str) -> None:
        """Remove and close a client."""
        async with self._lock:
            client = self._clients.pop(server_id, None)
            if client:
                await client.close()

    async def close_all(self) -> None:
        """Close all clients."""
        async with self._lock:
            for client in self._clients.values():
                await client.close()
            self._clients.clear()

    def get_all_tools(self) -> dict[str, list[ToolDefinition]]:
        """Get all tools from all clients."""
        return {
            server_id: client.tools
            for server_id, client in self._clients.items()
            if client.is_initialized
        }
