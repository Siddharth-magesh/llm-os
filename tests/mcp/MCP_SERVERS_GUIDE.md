# OSSARTH MCP Servers Guide

## Overview

OSSARTH supports two types of MCP servers:

1. **Internal Servers** (Python) - Run in-process
2. **External Servers** (Node.js/other) - Run as separate processes

## Server Locations

### Internal Python Servers

**Location:** `D:\llm-os\src\llm_os\mcp\servers\`

**Existing Servers:**
- `system.py` - System information (CPU, memory, disk, network)
- `process.py` - Process management (list, kill, monitor)
- `filesystem.py` - File operations (read, write, list, search)
- `git.py` - Git operations (status, diff, commit, push)
- `applications.py` - Application management

**Custom Test Servers:**
- `D:\llm-os\tests\mcp\custom_servers\calculator_server.py` - Calculator example

### External Servers Configuration

**Location:** `D:\llm-os\src\llm_os\mcp\client\external_server.py`

**Definition:** `OFFICIAL_SERVERS` dictionary (lines 46-150)

**Available Official Servers:**

#### No API Key Required:
- `time` - Time and timezone operations
- `filesystem` - File operations
- `memory` - Knowledge graph storage
- `sequential-thinking` - Structured reasoning

#### API Key Required:
- `brave-search` - Brave web search (needs BRAVE_API_KEY)
- `google-maps` - Google Maps (needs GOOGLE_MAPS_API_KEY)
- `github` - GitHub API (needs GITHUB_PERSONAL_ACCESS_TOKEN)
- `slack` - Slack integration (needs SLACK_BOT_TOKEN)
- `postgres` - PostgreSQL (needs POSTGRES_CONNECTION_STRING)

## How to Create Custom Internal Servers

### 1. Basic Structure

```python
from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types.tools import ToolResult, ToolParameter, ParameterType


class MyServer(BaseMCPServer):
    """My custom MCP server."""

    server_id = "my-server"
    server_name = "My Server"
    server_version = "1.0.0"
    server_description = "Description of my server"

    def __init__(self):
        super().__init__()
        self._register_tools()

    def _register_tools(self) -> None:
        """Register tools."""
        self.register_tool(
            name="my_tool",
            description="What my tool does",
            handler=self._my_tool,
            parameters=[
                ToolParameter(
                    name="param1",
                    type=ParameterType.STRING,
                    description="Parameter description",
                    required=True,
                ),
            ],
            permission_level="read",
        )

    async def _my_tool(self, param1: str) -> ToolResult:
        """Tool implementation."""
        # Do something
        result = f"Processed: {param1}"

        return ToolResult.success_result(
            text=result,
            metadata_key=value
        )
```

### 2. Parameter Types

- `ParameterType.STRING` - Text
- `ParameterType.NUMBER` - Float/decimal
- `ParameterType.INTEGER` - Whole number
- `ParameterType.BOOLEAN` - True/False
- `ParameterType.ARRAY` - List
- `ParameterType.OBJECT` - Dictionary

### 3. Return Results

**Success:**
```python
return ToolResult.success_result(
    text="Result text here",
    key1=value1,
    key2=value2
)
```

**Error:**
```python
return ToolResult.error_result(
    error="Error message"
)
```

## How to Add External Servers

### 1. Add to OFFICIAL_SERVERS Dictionary

Edit: `src/llm_os/mcp/client/external_server.py`

```python
OFFICIAL_SERVERS: dict[str, ExternalServerConfig] = {
    # ... existing servers ...

    "my-server": ExternalServerConfig(
        server_id="mcp-my-server",
        name="My MCP Server",
        description="Description",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-my-server"],
        env={"API_KEY": "your_key"},  # Optional
    ),
}
```

### 2. Enable in Configuration

Edit: `llm_os/config/default.yaml`

```yaml
mcp:
  auto_start_servers:
    - "my-server"
```

## Testing Servers

### Test Internal Servers

**Run all tests:**
```bash
cd tests/mcp
run_all_tests.bat
```

**Test individual servers:**
```bash
test_internal_calculator.bat
test_existing_servers.bat
```

### Test External Servers

**Requirements:**
- Node.js and npx must be installed
- Run: `test_external_time.bat`

### Create Your Own Tests

Example test structure:
```python
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from my_package import MyServer

async def test_my_server():
    server = MyServer()

    # List tools
    print(f"Tools: {server.tool_names}")

    # Call a tool
    result = await server.call_tool("my_tool", {"param1": "test"})
    print(f"Result: {result.content[0].text}")

asyncio.run(test_my_server())
```

## Server Architecture

```
Internal Servers (Python):
  D:\llm-os\src\llm_os\mcp\servers\
  ├── base.py           (Base class)
  ├── system.py         (System info)
  ├── process.py        (Process mgmt)
  ├── filesystem.py     (Files)
  ├── git.py            (Git)
  └── applications.py   (Apps)

External Servers (Node.js):
  - Defined in: src/llm_os/mcp/client/external_server.py
  - Communicate via: JSON-RPC over stdio
  - Client: src/llm_os/mcp/client/stdio_client.py

Custom Test Servers:
  tests/mcp/custom_servers/
  └── calculator_server.py
```

## Next Steps

1. **Test Existing Servers** - Run `test_existing_servers.bat`
2. **Test Custom Server** - Run `test_internal_calculator.bat`
3. **Test External Server** - Run `test_external_time.bat` (needs Node.js)
4. **Create Your Own** - Use calculator_server.py as a template
5. **Integrate More** - Add official servers from https://mcpservers.org/

## Useful Links

- MCP Servers Catalog: https://mcpservers.org/
- Official MCP Servers: https://github.com/modelcontextprotocol/servers
- MCP Examples: https://modelcontextprotocol.io/examples
- MCP Specification: https://modelcontextprotocol.io/

## Status

✅ Internal servers: Working
✅ Custom servers: Working (calculator tested)
✅ External server support: Working (needs Node.js)
⏳ External servers: Ready to integrate (Time server tested)

All MCP infrastructure is functional and ready for integration!
