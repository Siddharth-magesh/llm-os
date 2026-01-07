"""
Custom MCP Server: Calculator
Simple calculator server for testing MCP functionality
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types.tools import ToolResult, ToolParameter, ParameterType


class CalculatorServer(BaseMCPServer):
    """Simple calculator MCP server for testing."""

    server_id = "calculator"
    server_name = "Calculator Server"
    server_version = "1.0.0"
    server_description = "Basic calculator operations for testing"

    def __init__(self):
        """Initialize calculator server."""
        super().__init__()
        self._register_tools()

    def _register_tools(self) -> None:
        """Register calculator tools."""

        # Addition
        self.register_tool(
            name="add",
            description="Add two numbers together",
            handler=self._add,
            parameters=[
                ToolParameter(
                    name="a",
                    type=ParameterType.NUMBER,
                    description="First number",
                    required=True,
                ),
                ToolParameter(
                    name="b",
                    type=ParameterType.NUMBER,
                    description="Second number",
                    required=True,
                ),
            ],
            permission_level="read",
        )

        # Subtraction
        self.register_tool(
            name="subtract",
            description="Subtract second number from first",
            handler=self._subtract,
            parameters=[
                ToolParameter(
                    name="a",
                    type=ParameterType.NUMBER,
                    description="First number",
                    required=True,
                ),
                ToolParameter(
                    name="b",
                    type=ParameterType.NUMBER,
                    description="Number to subtract",
                    required=True,
                ),
            ],
            permission_level="read",
        )

        # Multiply
        self.register_tool(
            name="multiply",
            description="Multiply two numbers",
            handler=self._multiply,
            parameters=[
                ToolParameter(
                    name="a",
                    type=ParameterType.NUMBER,
                    description="First number",
                    required=True,
                ),
                ToolParameter(
                    name="b",
                    type=ParameterType.NUMBER,
                    description="Second number",
                    required=True,
                ),
            ],
            permission_level="read",
        )

        # Divide
        self.register_tool(
            name="divide",
            description="Divide first number by second",
            handler=self._divide,
            parameters=[
                ToolParameter(
                    name="a",
                    type=ParameterType.NUMBER,
                    description="Numerator",
                    required=True,
                ),
                ToolParameter(
                    name="b",
                    type=ParameterType.NUMBER,
                    description="Denominator (cannot be zero)",
                    required=True,
                ),
            ],
            permission_level="read",
        )

    async def _add(self, a: float, b: float) -> ToolResult:
        """Add two numbers."""
        result = a + b
        return ToolResult.success_result(
            text=f"{a} + {b} = {result}",
            result=result,
            operation="addition"
        )

    async def _subtract(self, a: float, b: float) -> ToolResult:
        """Subtract two numbers."""
        result = a - b
        return ToolResult.success_result(
            text=f"{a} - {b} = {result}",
            result=result,
            operation="subtraction"
        )

    async def _multiply(self, a: float, b: float) -> ToolResult:
        """Multiply two numbers."""
        result = a * b
        return ToolResult.success_result(
            text=f"{a} × {b} = {result}",
            result=result,
            operation="multiplication"
        )

    async def _divide(self, a: float, b: float) -> ToolResult:
        """Divide two numbers."""
        if b == 0:
            return ToolResult.error_result(
                error="Cannot divide by zero"
            )

        result = a / b
        return ToolResult.success_result(
            text=f"{a} ÷ {b} = {result}",
            result=result,
            operation="division"
        )


# For testing
if __name__ == "__main__":
    import asyncio

    async def test_calculator():
        """Test calculator server."""
        server = CalculatorServer()

        print(f"Server: {server.server_name}")
        print(f"Tools: {server.tool_names}")
        print()

        # Test addition
        result = await server.call_tool("add", {"a": 10, "b": 5})
        print(f"Add: {result.content[0].text if result.content else 'No output'}")

        # Test subtraction
        result = await server.call_tool("subtract", {"a": 10, "b": 5})
        print(f"Subtract: {result.content[0].text if result.content else 'No output'}")

        # Test multiplication
        result = await server.call_tool("multiply", {"a": 10, "b": 5})
        print(f"Multiply: {result.content[0].text if result.content else 'No output'}")

        # Test division
        result = await server.call_tool("divide", {"a": 10, "b": 5})
        print(f"Divide: {result.content[0].text if result.content else 'No output'}")

        # Test division by zero
        result = await server.call_tool("divide", {"a": 10, "b": 0})
        print(f"Divide by zero: {result.content[0].text if result.content else 'No output'} (Success: {result.success})")

    asyncio.run(test_calculator())
