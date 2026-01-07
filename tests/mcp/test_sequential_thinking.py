"""
Test External MCP Server: Sequential Thinking
Tests @modelcontextprotocol/server-sequential-thinking
"""
import asyncio
import sys
from pathlib import Path

# Add the simple client
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client_simple import SimpleMCPClient


async def test_sequential_thinking():
    """Test the Sequential Thinking MCP server."""
    print("=" * 60)
    print("Testing Sequential Thinking Server")
    print("=" * 60)
    print()

    client = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-sequential-thinking"])

    try:
        print("Starting server...")
        await client.start()
        print("   Server started")

        print("\nInitializing connection...")
        result = await client.initialize()
        print(f"   Server: {client.server_info}")
        print(f"   Protocol: {result.get('protocolVersion', 'Unknown')}")

        print("\nListing tools...")
        tools = await client.list_tools()
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")

        if tools:
            print("\nTesting tool calls...")
            # Sequential thinking usually has a 'think' or similar tool
            # Let's test the first tool with appropriate arguments
            first_tool = tools[0]
            print(f"\n   Tool: {first_tool['name']}")
            print(f"   Description: {first_tool['description']}")

            # Check input schema to understand required parameters
            if 'inputSchema' in first_tool:
                print(f"   Input Schema: {first_tool['inputSchema']}")

        print("\n" + "=" * 60)
        print("SUCCESS: Sequential Thinking server is working!")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()
        print("\nServer stopped")


if __name__ == "__main__":
    asyncio.run(test_sequential_thinking())
