"""
Test Combined External Servers
Tests multiple external servers working together
"""
import asyncio
import sys
from pathlib import Path

# Add client to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.mcp_client import SimpleMCPClient


async def test_combined():
    """Test multiple servers together."""
    print("="*60)
    print("Testing Combined Servers")
    print("="*60)

    # Start both servers
    memory = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-memory"])
    thinking = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-sequential-thinking"])

    try:
        print("\nStarting servers...")
        await memory.start()
        await thinking.start()
        print("   Both started")

        print("\nInitializing...")
        await memory.initialize()
        await thinking.initialize()
        print("   Both initialized")

        print(f"\nMemory Server: {memory.server_info}")
        print(f"Thinking Server: {thinking.server_info}")

        print("\n" + "="*60)
        print("SUCCESS: Combined servers working!")
        print("="*60)

    except Exception as e:
        print(f"\nERROR: {e}")

    finally:
        await memory.close()
        await thinking.close()


if __name__ == "__main__":
    asyncio.run(test_combined())
