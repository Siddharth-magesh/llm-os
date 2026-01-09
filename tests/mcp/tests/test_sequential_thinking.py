"""
Test External Sequential Thinking Server
Tests @modelcontextprotocol/server-sequential-thinking
"""
import asyncio
import sys
from pathlib import Path

# Add client to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.mcp_client import SimpleMCPClient


async def test_sequential_thinking():
    """Test the Sequential Thinking server."""
    print("="*60)
    print("Testing Sequential Thinking Server")
    print("="*60)

    client = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-sequential-thinking"])

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

        print("\n" + "="*60)
        print("SUCCESS: Sequential Thinking server working!")
        print("="*60)

    except Exception as e:
        print(f"\nERROR: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_sequential_thinking())
