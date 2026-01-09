"""
Simple MCP Client - Working implementation for external MCP servers
Implements JSON-RPC 2.0 over stdio for MCP protocol
"""
import asyncio
import json
import uuid
from pathlib import Path
from typing import Any, Optional


class SimpleMCPClient:
    """Simple working MCP client for external servers."""

    def __init__(self, command: str, args: list[str]):
        """Initialize client."""
        self.command = command
        self.args = args
        self.process: Optional[asyncio.subprocess.Process] = None
        self.initialized = False
        self.server_info = {}
        self.capabilities = {}
        self.tools = []

    async def start(self):
        """Start the MCP server process."""
        # Use full path to npx on Windows
        cmd = self.command
        if cmd == "npx" and not cmd.endswith(".cmd"):
            cmd = r"C:\Program Files\nodejs\npx.cmd"

        full_command = [cmd] + self.args

        self.process = await asyncio.create_subprocess_exec(
            *full_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Give server time to start
        await asyncio.sleep(1)

    async def initialize(self, client_name: str = "OSSARTH", client_version: str = "0.1.0"):
        """Initialize the MCP connection."""
        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": client_name,
                    "version": client_version
                }
            }
        }

        response = await self._send_request(request)

        if response and "result" in response:
            result = response["result"]
            self.server_info = result.get("serverInfo", {})
            self.capabilities = result.get("capabilities", {})
            self.initialized = True

            # Send initialized notification
            await self._send_notification("notifications/initialized", {})

            return result
        else:
            raise Exception(f"Failed to initialize: {response}")

    async def list_tools(self):
        """List available tools."""
        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }

        response = await self._send_request(request)

        if response and "result" in response:
            self.tools = response["result"].get("tools", [])
            return self.tools
        else:
            return []

    async def call_tool(self, tool_name: str, arguments: dict = None):
        """Call a tool."""
        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }

        response = await self._send_request(request)

        if response and "result" in response:
            return response["result"]
        else:
            return response

    async def _send_request(self, request: dict, timeout: float = 30.0):
        """Send a request and wait for response."""
        if not self.process or not self.process.stdin:
            raise Exception("Process not started")

        request_id = request["id"]

        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()

        # Read response (line by line until we find our response)
        start_time = asyncio.get_event_loop().time()

        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Timeout waiting for response to {request['method']}")

            try:
                # Read with timeout
                line = await asyncio.wait_for(
                    self.process.stdout.readline(),
                    timeout=5.0
                )

                if not line:
                    # Check stderr
                    try:
                        stderr = await asyncio.wait_for(
                            self.process.stderr.read(1024),
                            timeout=0.1
                        )
                        if stderr:
                            print(f"[stderr] {stderr.decode().strip()}")
                    except asyncio.TimeoutError:
                        pass
                    continue

                # Parse JSON response
                response = json.loads(line.decode().strip())

                # Check if this is our response
                if response.get("id") == request_id:
                    return response

                # Otherwise it might be a notification, ignore for now

            except asyncio.TimeoutError:
                continue
            except json.JSONDecodeError as e:
                print(f"[warning] Failed to parse: {line.decode()}")
                continue

    async def _send_notification(self, method: str, params: dict):
        """Send a notification (no response expected)."""
        if not self.process or not self.process.stdin:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }

        notification_json = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_json.encode())
        await self.process.stdin.drain()

    async def close(self):
        """Close the connection."""
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()


# Test function
async def test_client():
    """Test the MCP client."""
    print("Testing Simple MCP Client")
    print("=" * 60)

    # Test Memory server (npm package)
    print("\n1. Testing Memory Server...")
    client = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-memory"])

    try:
        await client.start()
        print("   Started")

        result = await client.initialize()
        print(f"   Server: {client.server_info}")

        tools = await client.list_tools()
        print(f"   Tools: {[t['name'] for t in tools]}")

        if tools:
            # Test read_graph (no arguments needed)
            print(f"\n   Testing tool: read_graph")
            graph_result = await client.call_tool("read_graph")
            print(f"   Result: {graph_result}")

            # Test create_entities
            print(f"\n   Testing tool: create_entities")
            entities_result = await client.call_tool("create_entities", {
                "entities": [
                    {
                        "name": "test_entity",
                        "entityType": "concept",
                        "observations": ["This is a test observation"]
                    }
                ]
            })
            print(f"   Result: {entities_result}")

    finally:
        await client.close()

    print("\nSuccess!")


if __name__ == "__main__":
    asyncio.run(test_client())
