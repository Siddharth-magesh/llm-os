# External MCP Servers - Complete Guide

**Date:** January 7, 2026
**Status:** ✅ VERIFIED WORKING

---

## Summary

External MCP servers are standalone processes (typically Node.js packages) that communicate with OSSARTH via JSON-RPC 2.0 over stdio. They provide powerful capabilities without adding Python dependencies.

**Verified Working Servers:**
- ✅ Memory Server (@modelcontextprotocol/server-memory) - 9 tools
- ✅ Sequential Thinking Server (@modelcontextprotocol/server-sequential-thinking) - 1 tool

---

## How External Servers Work

### Architecture

```
OSSARTH (Python)
    ↓
SimpleMCPClient (JSON-RPC 2.0)
    ↓ stdin/stdout
External Server Process (Node.js/other)
    ↓
Server Tools & Capabilities
```

### Communication Protocol

1. **Start Process**: Spawn subprocess with stdin/stdout pipes
2. **Initialize**: Send JSON-RPC initialize request
3. **List Tools**: Request available tools
4. **Call Tools**: Send tool call requests with arguments
5. **Cleanup**: Terminate process gracefully

---

## Tested Servers

### 1. Memory Server

**Package:** `@modelcontextprotocol/server-memory`
**Purpose:** Knowledge graph management for entities and relationships
**Version:** 0.6.3

**Tools (9):**
- `create_entities` - Create nodes in knowledge graph
- `create_relations` - Create edges between nodes
- `add_observations` - Add facts/observations to entities
- `delete_entities` - Remove nodes
- `delete_observations` - Remove specific observations
- `delete_relations` - Remove edges
- `read_graph` - Get full graph structure
- `search_nodes` - Search by query
- `open_nodes` - Open specific nodes by name

**Example Usage:**
```python
from mcp_client_simple import SimpleMCPClient

client = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-memory"])
await client.start()
await client.initialize()

# Read empty graph
result = await client.call_tool("read_graph")
# Returns: {"entities": [], "relations": []}

# Create entity
result = await client.call_tool("create_entities", {
    "entities": [
        {
            "name": "OSSARTH",
            "entityType": "project",
            "observations": ["An LLM OS with MCP server integration"]
        }
    ]
})
```

**Customization Options:**
- No configuration file - stores data in memory
- Can be modified to persist to disk by forking the package
- Source: https://github.com/modelcontextprotocol/servers/tree/main/src/memory

### 2. Sequential Thinking Server

**Package:** `@modelcontextprotocol/server-sequential-thinking`
**Purpose:** Step-by-step problem solving with thought revision
**Version:** 0.2.0

**Tools (1):**
- `sequentialthinking` - Dynamic problem-solving through structured thoughts

**Parameters:**
- `thought` (string, required) - Current thinking step
- `nextThoughtNeeded` (boolean, required) - Whether more thinking is needed
- `thoughtNumber` (integer, required) - Current thought number
- `totalThoughts` (integer, required) - Estimated total thoughts
- `isRevision` (boolean) - Whether this revises previous thinking
- `revisesThought` (integer) - Which thought is being reconsidered
- `branchFromThought` (integer) - Branching point thought number
- `branchId` (string) - Branch identifier
- `needsMoreThoughts` (boolean) - If more thoughts are needed

**Example Usage:**
```python
client = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-sequential-thinking"])
await client.start()
await client.initialize()

# First thought
result = await client.call_tool("sequentialthinking", {
    "thought": "First, I need to understand the problem requirements",
    "nextThoughtNeeded": True,
    "thoughtNumber": 1,
    "totalThoughts": 5
})

# Follow-up thought
result = await client.call_tool("sequentialthinking", {
    "thought": "Based on step 1, I should break down the components",
    "nextThoughtNeeded": True,
    "thoughtNumber": 2,
    "totalThoughts": 5
})
```

**Customization Options:**
- Can fork and modify thinking patterns
- Source: https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking

---

## Available External Servers (Not Yet Tested)

### From modelcontextprotocol/servers

**No API Key Required:**
- `@modelcontextprotocol/server-filesystem` - File operations
- `@modelcontextprotocol/server-time` - Time/timezone operations
- `@modelcontextprotocol/server-everything` - Search Everything index
- `@modelcontextprotocol/server-fetch` - HTTP fetching
- `@modelcontextprotocol/server-puppeteer` - Browser automation

**API Key Required:**
- `@modelcontextprotocol/server-brave-search` - Web search
- `@modelcontextprotocol/server-google-maps` - Maps & places
- `@modelcontextprotocol/server-github` - GitHub API
- `@modelcontextprotocol/server-slack` - Slack integration
- `@modelcontextprotocol/server-sentry` - Error monitoring

### From mcpservers.org

Hundreds more available at: https://mcpservers.org/

---

## How to Add a New External Server

### Step 1: Test the Server

```python
# Create test file: tests/mcp/test_myserver.py
from mcp_client_simple import SimpleMCPClient

async def test_myserver():
    client = SimpleMCPClient("npx", ["-y", "@scope/server-name"])

    try:
        await client.start()
        result = await client.initialize()
        print(f"Server: {client.server_info}")

        tools = await client.list_tools()
        for tool in tools:
            print(f"Tool: {tool['name']}")
            print(f"  Schema: {tool.get('inputSchema', {})}")

    finally:
        await client.close()

asyncio.run(test_myserver())
```

### Step 2: Document Tool Parameters

```python
# Test each tool with sample data
result = await client.call_tool("tool_name", {
    "param1": "value1",
    "param2": 123
})
print(result)
```

### Step 3: Add to External Server Configuration

Edit: `D:\llm-os\src\llm_os\mcp\client\external_server.py`

```python
OFFICIAL_SERVERS = {
    "myserver": {
        "command": "npx",
        "args": ["-y", "@scope/server-name"],
        "description": "What it does",
        "requires_api_key": False,
        "env": {}
    }
}
```

### Step 4: Enable in Config

Edit: `llm_os\config\default.yaml`

```yaml
mcp:
  servers:
    external:
      myserver:
        enabled: true
```

---

## How to Customize External Servers

### Option 1: Fork and Modify (Full Control)

```bash
# Clone the server repository
git clone https://github.com/modelcontextprotocol/servers.git
cd servers/src/memory

# Make your modifications
# Edit src/index.ts or other files

# Build
npm install
npm run build

# Test locally
node dist/index.js

# In your OSSARTH code, point to local version:
client = SimpleMCPClient("node", ["D:/path/to/servers/src/memory/dist/index.js"])
```

### Option 2: Configuration via Environment Variables

Many servers accept environment variables:

```python
import os

# Set environment variables before starting server
os.environ["SERVER_CONFIG_PATH"] = "/path/to/config.json"
os.environ["MAX_MEMORY_SIZE"] = "1000"

client = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-memory"])
```

### Option 3: Wrapper Server (Python)

Create a Python wrapper that filters/transforms requests:

```python
class CustomMemoryServer:
    def __init__(self):
        self.client = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-memory"])

    async def filtered_create_entity(self, name: str, entity_type: str):
        # Add your custom logic
        if not self._is_valid_entity_type(entity_type):
            raise ValueError("Invalid entity type")

        # Forward to real server
        return await self.client.call_tool("create_entities", {
            "entities": [{
                "name": name,
                "entityType": entity_type,
                "observations": []
            }]
        })
```

---

## Integration with OSSARTH

### Current Implementation

**Location:** `D:\llm-os\src\llm_os\mcp\client\stdio_client.py`

The `StdioMCPClient` class needs updates to match our working `SimpleMCPClient`.

### Recommended Changes

1. **Replace StdioMCPClient** with our working SimpleMCPClient
2. **Add External Server Registry** in external_server.py
3. **Create Server Manager** to handle multiple external servers
4. **Add Configuration Loading** from default.yaml

### Integration Steps

```python
# 1. Copy working client
# D:\llm-os\tests\mcp\mcp_client_simple.py
#   → D:\llm-os\src\llm_os\mcp\client\stdio_client.py

# 2. Create server manager
# D:\llm-os\src\llm_os\mcp\manager\external_manager.py

class ExternalServerManager:
    def __init__(self, config: dict):
        self.servers = {}
        self.config = config

    async def start_server(self, server_name: str):
        server_config = self.config[server_name]
        client = SimpleMCPClient(
            command=server_config["command"],
            args=server_config["args"]
        )
        await client.start()
        await client.initialize()
        self.servers[server_name] = client

    async def call_tool(self, server_name: str, tool_name: str, args: dict):
        client = self.servers[server_name]
        return await client.call_tool(tool_name, args)
```

---

## Testing External Servers

### Quick Tests

```bash
# Test Memory server
cd D:\llm-os\tests\mcp
python mcp_client_simple.py

# Test Sequential Thinking server
python test_sequential_thinking.py

# Test new server
python test_myserver.py
```

### Comprehensive Test

```bash
# Run all external server tests
python test_all_external.py
```

---

## Requirements

### For External Servers

- **Node.js 18+** (required for npm packages)
- **npx** (included with Node.js)
- **npm** (included with Node.js)

Check installation:
```bash
node --version  # Should show v18.0.0 or higher
npx --version   # Should show 8.0.0 or higher
```

Install from: https://nodejs.org/

### For Python Integration

- Python 3.11+
- asyncio
- json (built-in)
- subprocess (built-in)

---

## Troubleshooting

### Server Won't Start

**Issue:** `FileNotFoundError: npx not found`

**Solution:** Install Node.js from https://nodejs.org/

---

### Timeout Errors

**Issue:** `TimeoutError: Timeout waiting for response`

**Solution:**
- Increase timeout in `_send_request(timeout=60.0)`
- Check server stderr: `await process.stderr.read()`

---

### Tool Call Fails

**Issue:** Server returns error on tool call

**Solution:**
- Check input schema: `print(tool['inputSchema'])`
- Verify required parameters are provided
- Check parameter types match schema

---

### Package Not Found

**Issue:** `npm ERR! 404 Not Found - GET https://registry.npmjs.org/@scope/server-name`

**Solution:**
- Verify package exists: https://www.npmjs.com/package/@scope/server-name
- Check spelling of package name
- Try `-y` flag: `npx -y @scope/server-name`

---

## Performance Considerations

### Memory Server
- In-memory only (no persistence)
- Fast for small graphs (<1000 nodes)
- Consider forking for disk persistence

### Sequential Thinking
- Each thought is a separate tool call
- Best for complex problems (5-20 thoughts)
- Can slow down for very long chains

### General
- External servers add process overhead (~100ms startup)
- Keep servers running for multiple tool calls
- Use connection pooling for high-volume scenarios

---

## Security Considerations

1. **API Keys**: Store in environment variables, never in code
2. **Input Validation**: Always validate before sending to external server
3. **Sandboxing**: External servers run in separate process (good isolation)
4. **Network**: Some servers may make external network calls
5. **File Access**: Filesystem server can access local files

---

## Next Steps

### Phase 1: Integration (Current)
- ✅ Verify external servers work
- ✅ Create working client implementation
- ✅ Test 2+ servers
- ⏳ Replace stdio_client.py with working version

### Phase 2: Expansion
- Add 5-10 more external servers
- Create server manager for lifecycle
- Add configuration management
- Write integration tests

### Phase 3: Customization
- Fork and customize key servers
- Add OSSARTH-specific wrappers
- Create custom external servers
- Build server marketplace

---

## Resources

- **Official Servers:** https://github.com/modelcontextprotocol/servers
- **Server Directory:** https://mcpservers.org/
- **MCP Spec:** https://modelcontextprotocol.io/
- **Examples:** https://modelcontextprotocol.io/examples

---

## Status: READY FOR INTEGRATION ✅

Both Memory and Sequential Thinking servers are verified working. The SimpleMCPClient implementation is production-ready and can be integrated into OSSARTH's main codebase.

**Key Files:**
- Working Client: `D:\llm-os\tests\mcp\mcp_client_simple.py`
- Test Scripts: `test_sequential_thinking.py`, `mcp_client_simple.py`
- This Guide: `EXTERNAL_SERVERS_GUIDE.md`
