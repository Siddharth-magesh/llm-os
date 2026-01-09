"""
Test Internal MCP Servers
Tests all built-in Python servers
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from llm_os.mcp.servers.system import SystemServer
from llm_os.mcp.servers.process import ProcessServer
from llm_os.mcp.servers.git import GitServer
from llm_os.mcp.servers.filesystem import FilesystemServer
from llm_os.mcp.servers.applications import ApplicationsServer


async def test_server(server_class, test_tool=None):
    """Test a server."""
    print(f"\n{'='*60}")
    print(f"Testing: {server_class.server_name}")
    print(f"{'='*60}")

    try:
        server = server_class()
        print(f"Server ID: {server.server_id}")
        print(f"Tools: {len(server.tools)}")

        if test_tool:
            tool_names = [t.name for t in server.tools]
            if test_tool in tool_names:
                print(f"\nTesting tool: {test_tool}")
                result = await server.call_tool(test_tool, {})
                print(f"  Success: {result.success}")
                if result.success and result.content:
                    output = result.content[0].text[:200]
                    print(f"  Output: {output}...")

        print(f"\n{server_class.server_name} test completed")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


async def main():
    print("="*60)
    print("Testing Internal MCP Servers")
    print("="*60)

    servers = [
        (SystemServer, "system_info"),
        (ProcessServer, "list_processes"),
        (GitServer, None),
        (FilesystemServer, "list_directory"),
        (ApplicationsServer, None),
    ]

    passed = 0
    for server_class, test_tool in servers:
        if await test_server(server_class, test_tool):
            passed += 1

    print(f"\n{'='*60}")
    print(f"Test Summary: {passed}/{len(servers)} passed")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
