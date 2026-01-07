"""
Test Internal MCP Server: Calculator
Tests custom Python-based MCP server
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from custom_servers.calculator_server import CalculatorServer


async def test_calculator_server():
    """Test the calculator server."""
    print("=" * 60)
    print("Testing Internal MCP Server: Calculator")
    print("=" * 60)
    print()

    # Create server
    server = CalculatorServer()

    print(f"Server ID: {server.server_id}")
    print(f"Server Name: {server.server_name}")
    print(f"Version: {server.server_version}")
    print(f"Description: {server.server_description}")
    print()

    # List tools
    print(f"Tools Available ({len(server.tools)}):")
    for tool in server.tools:
        print(f"  - {tool.name}: {tool.description}")
    print()

    # Test each operation
    print("Testing Tools:")
    print("-" * 60)

    # Test 1: Addition
    print("\n1. Testing ADD tool:")
    result = await server.call_tool("add", {"a": 15, "b": 25})
    print(f"   Input: a=15, b=25")
    print(f"   Output: {result.content[0].text if result.content else 'No output'}")
    print(f"   Success: {result.success}")
    print(f"   Metadata: {result.metadata}")

    # Test 2: Subtraction
    print("\n2. Testing SUBTRACT tool:")
    result = await server.call_tool("subtract", {"a": 100, "b": 35})
    print(f"   Input: a=100, b=35")
    print(f"   Output: {result.content[0].text if result.content else 'No output'}")
    print(f"   Success: {result.success}")

    # Test 3: Multiplication
    print("\n3. Testing MULTIPLY tool:")
    result = await server.call_tool("multiply", {"a": 12, "b": 8})
    print(f"   Input: a=12, b=8")
    print(f"   Output: {result.content[0].text if result.content else 'No output'}")
    print(f"   Success: {result.success}")

    # Test 4: Division
    print("\n4. Testing DIVIDE tool:")
    result = await server.call_tool("divide", {"a": 100, "b": 4})
    print(f"   Input: a=100, b=4")
    print(f"   Output: {result.content[0].text if result.content else 'No output'}")
    print(f"   Success: {result.success}")

    # Test 5: Division by zero (error handling)
    print("\n5. Testing DIVIDE tool (error case):")
    result = await server.call_tool("divide", {"a": 10, "b": 0})
    print(f"   Input: a=10, b=0")
    print(f"   Output: {result.content[0].text if result.content else 'No output'}")
    print(f"   Success: {result.success}")
    print(f"   Error: {result.error_message}")

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_calculator_server())
