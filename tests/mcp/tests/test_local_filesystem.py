"""
Test Local Filesystem Server
Tests the locally built filesystem server
"""
import asyncio
import sys
from pathlib import Path

# Add client to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.mcp_client import SimpleMCPClient


async def test_local_filesystem():
    """Test the locally built filesystem server."""
    print("="*60)
    print("Testing LOCAL Filesystem Server")
    print("="*60)

    # Path to local server
    local_server = str(Path(__file__).parent.parent.parent.parent / "external-servers" / "filesystem" / "dist" / "index.js")
    test_dir = str(Path(__file__).parent.parent)

    print(f"\nLocal server: {local_server}")
    print(f"Allowed directory: {test_dir}")

    client = SimpleMCPClient("node", [local_server, test_dir])

    try:
        print("\nStarting local server...")
        await client.start()
        print("   Started")

        print("\nInitializing...")
        await client.initialize()
        print(f"   Server: {client.server_info}")

        print("\nListing tools...")
        tools = await client.list_tools()
        print(f"   Tools: {len(tools)}")

        # Test list directory
        print("\nTesting list_directory...")
        result = await client.call_tool("list_directory", {"path": "."})
        if result.get("isError"):
            print(f"   ERROR: {result['content'][0]['text']}")
        else:
            content = result['content'][0]['text']
            lines = content.split('\n')[:5]
            print(f"   First 5 items:")
            for line in lines:
                print(f"     {line}")

        # Test read file
        print("\nTesting read_file...")
        result = await client.call_tool("read_file", {"path": "README.md"})
        if result.get("isError"):
            print(f"   ERROR: {result['content'][0]['text']}")
        else:
            content = result['content'][0]['text']
            lines = content.split('\n')[:3]
            print(f"   First 3 lines:")
            for line in lines:
                print(f"     {line}")

        print("\n" + "="*60)
        print("SUCCESS: Local filesystem server working!")
        print("="*60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_local_filesystem())
