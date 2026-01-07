"""
Test Existing Internal MCP Servers
Tests the internal servers already in the codebase
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from llm_os.mcp.servers.system import SystemServer
from llm_os.mcp.servers.process import ProcessServer
from llm_os.mcp.servers.git import GitServer
from llm_os.mcp.servers.filesystem import FilesystemServer
from llm_os.mcp.servers.applications import ApplicationsServer


async def test_server(server_class, test_tool=None):
    """Test a server and optionally call a tool."""
    print(f"\n{'='*60}")
    print(f"Testing: {server_class.server_name}")
    print(f"{'='*60}")

    try:
        # Create server instance
        server = server_class()

        print(f"Server ID: {server.server_id}")
        print(f"Version: {server.server_version}")
        print(f"Description: {server.server_description}")
        print(f"Tools: {len(server.tools)}")

        # List tools
        print(f"\nAvailable Tools:")
        for i, tool in enumerate(server.tools, 1):
            print(f"  {i}. {tool.name}: {tool.description[:50]}...")

        # Test a tool if specified
        if test_tool:
            tool_name, args = test_tool
            if tool_name in server.tool_names:
                print(f"\nTesting tool: {tool_name}")
                result = await server.call_tool(tool_name, args)
                print(f"  Success: {result.success}")
                if result.content:
                    output_text = result.content[0].text or ""
                    print(f"  Output: {output_text[:100]}...")
                else:
                    print(f"  Output: (no content)")
            else:
                print(f"\n  Tool '{tool_name}' not found")

        print(f"\n{server_class.server_name} test completed")
        return True

    except Exception as e:
        print(f"\n✗ Error testing {server_class.server_name}:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Test all existing internal servers."""
    print("="*60)
    print("OSSARTH - Testing Existing Internal MCP Servers")
    print("="*60)

    results = []

    # Test System Server
    results.append(await test_server(
        SystemServer,
        test_tool=("system_info", {})
    ))

    # Test Process Server
    results.append(await test_server(
        ProcessServer,
        test_tool=("list_processes", {"limit": 5})
    ))

    # Test Git Server (may fail if not in git repo)
    results.append(await test_server(
        GitServer,
        test_tool=None  # Skip tool test
    ))

    # Test Filesystem Server
    results.append(await test_server(
        FilesystemServer,
        test_tool=("list_directory", {"path": "."})
    ))

    # Test Applications Server
    results.append(await test_server(
        ApplicationsServer,
        test_tool=None  # Skip tool test
    ))

    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\nAll tests PASSED!")
    else:
        print("\nSome tests FAILED")

    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
