# MCP Server Testing

Testing infrastructure for Model Context Protocol servers in OSSARTH.

## Quick Start

```bash
cd D:\llm-os\tests\mcp
python run_tests.py
```

This runs all tests automatically and shows a summary.

---

## Structure

```
tests/mcp/
├── README.md                   # This file
├── AVAILABLE_SERVERS.md        # Catalog of available servers
├── run_tests.py                # Main test runner
├── client/
│   └── mcp_client.py           # MCP client implementation
├── tests/
│   ├── test_internal_servers.py    # Test internal Python servers
│   ├── test_calculator.py          # Test custom calculator
│   ├── test_memory_server.py       # Test Memory server
│   ├── test_sequential_thinking.py # Test Sequential Thinking
│   └── test_combined.py            # Test multiple servers
└── examples/
    └── calculator_server.py    # Custom server template
```

---

## What Are MCP Servers?

**Model Context Protocol (MCP)** servers provide tools and capabilities to OSSARTH.

### Two Types:

**1. Internal Servers (Python)**
- Run in-process
- Fast (< 1ms tool calls)
- Located in: `src/llm_os/mcp/servers/`
- Examples: System, Process, Git, Filesystem, Applications

**2. External Servers (Node.js/other)**
- Run as separate processes
- Communicate via JSON-RPC 2.0
- 135+ servers available
- Examples: Memory (knowledge graphs), Sequential Thinking (reasoning)

---

## Running Tests

### All Tests
```bash
python run_tests.py
```

### Individual Tests
```bash
# Test internal Python servers
python tests/test_internal_servers.py

# Test custom calculator server
python tests/test_calculator.py

# Test external Memory server (requires Node.js)
python tests/test_memory_server.py

# Test Sequential Thinking server (requires Node.js)
python tests/test_sequential_thinking.py

# Test both external servers together
python tests/test_combined.py
```

---

## Test Results

**Current Status:** All tests passing

### Internal Servers (5 servers, 61 tools)
- System Server: 16 tools
- Process Server: 10 tools
- Git Server: 14 tools
- Filesystem Server: 13 tools
- Applications Server: 8 tools

### External Servers (2 tested, 133+ available)
- Memory Server: 9 tools (knowledge graphs)
- Sequential Thinking: 1 tool (multi-step reasoning)

**Total:** 71 tools verified working

---

## Creating Custom Servers

### Internal Server (Python)

Use `examples/calculator_server.py` as template:

```python
from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types import ToolParameter, ToolResult, ParameterType

class MyServer(BaseMCPServer):
    server_id = "myserver"
    server_name = "My Server"

    def _register_tools(self):
        self.register_tool(
            name="my_tool",
            description="What it does",
            handler=self._my_tool_handler,
            parameters=[
                ToolParameter(
                    name="input",
                    type=ParameterType.STRING,
                    description="Input parameter",
                    required=True
                )
            ]
        )

    async def _my_tool_handler(self, input: str) -> ToolResult:
        result = f"Processed: {input}"
        return ToolResult.success_result(text=result)
```

### External Server (Node.js)

Test any npm package:

```python
import asyncio
from client.mcp_client import SimpleMCPClient

async def test():
    client = SimpleMCPClient("npx", ["-y", "@scope/package-name"])
    await client.start()
    await client.initialize()

    tools = await client.list_tools()
    print([t['name'] for t in tools])

    await client.close()

asyncio.run(test())
```

---

## Adding New External Servers

### Step 1: Test It

Create `tests/test_myserver.py`:

```python
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from client.mcp_client import SimpleMCPClient

async def test_myserver():
    client = SimpleMCPClient("npx", ["-y", "@scope/package-name"])

    await client.start()
    await client.initialize()

    print(f"Server: {client.server_info}")
    tools = await client.list_tools()
    print(f"Tools: {[t['name'] for t in tools]}")

    await client.close()

asyncio.run(test_myserver())
```

### Step 2: Run Test

```bash
python tests/test_myserver.py
```

### Step 3: Integrate

If successful, add to OSSARTH configuration in `config/default.yaml`.

---

## Available Servers

See `AVAILABLE_SERVERS.md` for complete catalog of 135+ available servers.

**Popular servers ready to test:**
- Filesystem - File operations (no API key)
- Fetch - Web content (no API key)
- Time - Time utilities (no API key)
- GitHub - Code repos (free API key)
- Brave Search - Web search (free tier)
- Puppeteer - Browser automation (no API key)

---

## Requirements

### For Internal Servers
- Python 3.11+

### For External Servers
- Node.js 18+
- npm (included with Node.js)

**Install Node.js:** https://nodejs.org/

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'llm_os'"

Install OSSARTH package:
```bash
cd D:\llm-os
pip install -e .
```

### "npx not found"

Install Node.js from https://nodejs.org/

### External server timeout

Increase timeout in test file:
```python
result = await client._send_request(request, timeout=60.0)
```

### Test fails

1. Check error message
2. Verify prerequisites (Node.js for external servers)
3. Check tool parameters match inputSchema
4. Review server documentation

---

## Performance

### Internal Servers
- Initialization: < 10ms
- Tool call: < 1ms
- Memory: ~1MB per server

### External Servers
- Startup: 1-2 seconds (Node.js cold start)
- Initialization: 100-200ms (MCP handshake)
- Tool call: 50-100ms (JSON-RPC overhead)
- Memory: 30-50MB per process

**Recommendation:** Keep external servers running for multiple operations.

---

## Resources

- **Server Catalog:** `AVAILABLE_SERVERS.md`
- **MCP Specification:** https://modelcontextprotocol.io/
- **Official Servers:** https://github.com/modelcontextprotocol/servers
- **Server Directory:** https://mcpservers.org/
- **Source Code:** `D:\llm-os\src\llm_os\mcp\`

---

## Summary

- **Status:** All tests passing
- **Internal Servers:** 5 servers, 61 tools
- **External Servers:** 2 tested, 133+ available
- **Test Framework:** Automated with clear results
- **Documentation:** Complete with examples
- **Integration:** Ready for OSSARTH

**Ready to add more servers!**
