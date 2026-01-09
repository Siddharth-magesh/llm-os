"""
Test Custom Calculator Server
Tests custom MCP server example
"""
import asyncio
import sys
from pathlib import Path

# Add examples to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from examples.calculator_server import CalculatorServer


async def test_calculator():
    """Test calculator server."""
    print("="*60)
    print("Testing Calculator Server")
    print("="*60)

    server = CalculatorServer()
    print(f"Server: {server.server_name} v{server.server_version}")
    print(f"Tools: {len(server.tools)}\n")

    # Test add
    print("Testing add(10, 5)...")
    result = await server.call_tool("add", {"a": 10, "b": 5})
    print(f"  Success: {result.success}")
    print(f"  Result: {result.content[0].text}")

    # Test subtract
    print("\nTesting subtract(10, 5)...")
    result = await server.call_tool("subtract", {"a": 10, "b": 5})
    print(f"  Success: {result.success}")
    print(f"  Result: {result.content[0].text}")

    # Test multiply
    print("\nTesting multiply(10, 5)...")
    result = await server.call_tool("multiply", {"a": 10, "b": 5})
    print(f"  Success: {result.success}")
    print(f"  Result: {result.content[0].text}")

    # Test divide
    print("\nTesting divide(10, 5)...")
    result = await server.call_tool("divide", {"a": 10, "b": 5})
    print(f"  Success: {result.success}")
    print(f"  Result: {result.content[0].text}")

    # Test divide by zero
    print("\nTesting divide(10, 0) [error case]...")
    result = await server.call_tool("divide", {"a": 10, "b": 0})
    print(f"  Success: {result.success}")
    print(f"  Result: {result.content[0].text}")

    print("\n" + "="*60)
    print("Calculator test complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_calculator())
