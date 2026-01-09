"""
Test External Memory Server
Tests @modelcontextprotocol/server-memory
"""
import asyncio
import sys
from pathlib import Path

# Add client to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.mcp_client import SimpleMCPClient


async def test_memory_server():
    """Test the Memory MCP server."""
    print("="*60)
    print("Testing Memory Server")
    print("="*60)

    client = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-memory"])

    try:
        print("\nStarting server...")
        await client.start()
        print("   Started")

        print("\nInitializing...")
        await client.initialize()
        print(f"   Server: {client.server_info}")

        print("\nListing tools...")
        tools = await client.list_tools()
        print(f"   Tools: {[t['name'] for t in tools]}")

        print("\nTesting read_graph...")
        result = await client.call_tool("read_graph")
        print(f"   Entities: {len(result.get('structuredContent', {}).get('entities', []))}")

        print("\n" + "="*60)
        print("SUCCESS: Memory server working!")
        print("="*60)

    except Exception as e:
        print(f"\nERROR: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_memory_server())
