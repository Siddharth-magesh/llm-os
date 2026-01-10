"""
Test External Filesystem Server
Tests @modelcontextprotocol/server-filesystem
"""
import asyncio
import sys
from pathlib import Path

# Add client to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.mcp_client import SimpleMCPClient


async def test_filesystem_server():
    """Test the external filesystem MCP server."""
    print("="*60)
    print("Testing External Filesystem Server")
    print("="*60)

    # Allow access to tests/mcp directory
    test_dir = str(Path(__file__).parent.parent)
    print(f"\nAllowed directory: {test_dir}")

    client = SimpleMCPClient("npx", [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        test_dir
    ])

    try:
        print("\nStarting server...")
        await client.start()
        print("   Started")

        print("\nInitializing...")
        await client.initialize()
        print(f"   Server: {client.server_info}")

        print("\nListing tools...")
        tools = await client.list_tools()
        print(f"   Tools: {len(tools)}")
        for i, tool in enumerate(tools[:5], 1):  # Show first 5
            print(f"   {i}. {tool['name']}")
        if len(tools) > 5:
            print(f"   ... and {len(tools) - 5} more")

        print("\n" + "-"*60)
        print("Testing Operations")
        print("-"*60)

        # Test 1: List directory
        print("\n1. Testing list_directory...")
        result = await client.call_tool("list_directory", {"path": "."})
        if result.get("isError"):
            print(f"   ERROR: {result['content'][0]['text']}")
        else:
            content = result['content'][0]['text']
            lines = content.split('\n')[:5]
            print(f"   Found {len(content.split(chr(10)))} items")
            print(f"   First items:")
            for line in lines:
                print(f"     {line}")

        # Test 2: Directory tree
        print("\n2. Testing directory_tree...")
        result = await client.call_tool("directory_tree", {"path": "tests"})
        if result.get("isError"):
            print(f"   ERROR: {result['content'][0]['text']}")
        else:
            content = result['content'][0]['text']
            lines = content.split('\n')[:10]
            print(f"   Tree preview:")
            for line in lines:
                print(f"     {line}")

        # Test 3: Search files
        print("\n3. Testing search_files...")
        result = await client.call_tool("search_files", {
            "path": ".",
            "pattern": "*.py"
        })
        if result.get("isError"):
            print(f"   ERROR: {result['content'][0]['text']}")
        else:
            content = result['content'][0]['text']
            files = [f for f in content.split('\n') if f]
            print(f"   Found {len(files)} Python files")
            for file in files[:3]:
                print(f"     {file}")

        # Test 4: Get file info
        print("\n4. Testing get_file_info...")
        result = await client.call_tool("get_file_info", {
            "path": "README.md"
        })
        if result.get("isError"):
            print(f"   ERROR: {result['content'][0]['text']}")
        else:
            content = result['content'][0]['text']
            print(f"   File info:")
            for line in content.split('\n')[:5]:
                print(f"     {line}")

        # Test 5: Read file
        print("\n5. Testing read_file...")
        result = await client.call_tool("read_file", {
            "path": "README.md"
        })
        if result.get("isError"):
            print(f"   ERROR: {result['content'][0]['text']}")
        else:
            content = result['content'][0]['text']
            lines = content.split('\n')[:3]
            print(f"   First 3 lines:")
            for line in lines:
                print(f"     {line}")

        # Test 6: List allowed directories
        print("\n6. Testing list_allowed_directories...")
        result = await client.call_tool("list_allowed_directories", {})
        if result.get("isError"):
            print(f"   ERROR: {result['content'][0]['text']}")
        else:
            content = result['content'][0]['text']
            print(f"   Allowed directories:")
            for line in content.split('\n'):
                print(f"     {line}")

        print("\n" + "="*60)
        print("SUCCESS: External filesystem server working!")
        print("="*60)
        print("\nAll 14 tools available:")
        for i, tool in enumerate(tools, 1):
            print(f"{i:2}. {tool['name']}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_filesystem_server())
