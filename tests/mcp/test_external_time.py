"""
Test External MCP Server: Time
Tests official @modelcontextprotocol/server-time via stdio
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from llm_os.mcp.client.stdio_client import StdioMCPClient


async def test_time_server():
    """Test the official Time MCP server."""
    print("=" * 60)
    print("Testing External MCP Server: Time")
    print("=" * 60)
    print()

    # Create client for Time server
    print("Starting Time MCP server...")
    client = StdioMCPClient(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-time"]
    )

    try:
        # Initialize connection (also starts server)
        print("Initializing connection...")
        await client.initialize(
            client_info={"name": "OSSARTH Test", "version": "0.1.0"}
        )
        print("✓ Server started and initialized successfully")
        print(f"✓ Server Name: {client._server_info.get('name', 'Unknown')}")
        print(f"✓ Server Version: {client._server_info.get('version', 'Unknown')}")
        print()

        # List available tools
        print("Fetching available tools...")
        tools = client.tools
        print(f"✓ Tools Available ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        print()

        # Test tool calls
        if tools:
            print("Testing Tool Calls:")
            print("-" * 60)

            # Find and test get_current_time
            time_tool = next((t for t in tools if "time" in t.name.lower()), None)
            if time_tool:
                print(f"\nTesting tool: {time_tool.name}")
                result = await client.call_tool(time_tool.name, {})
                print(f"Result: {result}")
            else:
                print("\nNo time tool found, testing first available tool...")
                result = await client.call_tool(tools[0].name, {})
                print(f"Tool: {tools[0].name}")
                print(f"Result: {result}")

        print("\n" + "=" * 60)
        print("✓ Time server test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print("\nStopping server...")
        await client.close()
        print("✓ Server stopped")


if __name__ == "__main__":
    # Check if Node.js and npx are available
    import shutil
    if not shutil.which("npx"):
        print("✗ Error: npx not found")
        print("  Please install Node.js from https://nodejs.org/")
        sys.exit(1)

    asyncio.run(test_time_server())
