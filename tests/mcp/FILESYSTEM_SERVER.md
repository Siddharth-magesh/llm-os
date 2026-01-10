# External Filesystem MCP Server

**Complete guide to using and customizing the external filesystem MCP server in OSSARTH**

---

## Overview

The external filesystem MCP server provides comprehensive file and directory operations through the Model Context Protocol. Unlike the internal Python filesystem server, this Node.js-based external server offers advanced features like targeted file updates, regex search/replace, and better security controls.

**Why Use External Server?**
- More advanced features (regex, bulk operations)
- Better maintained (official Anthropic implementation)
- Cross-platform compatibility
- Security-first design with path validation
- Can be customized and extended

---

## Available Servers

### 1. Official Filesystem Server (Recommended)

**Package:** `@modelcontextprotocol/server-filesystem`
**Source:** https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
**Maintainer:** Anthropic (official)

**Tools (14):**
1. `read_file` - Read file contents
2. `read_multiple_files` - Read multiple files at once
3. `write_file` - Write content to file
4. `edit_file` - Selective file editing with search/replace
5. `create_directory` - Create directories
6. `list_directory` - List directory contents with sizes
7. `directory_tree` - Recursive directory tree view
8. `move_file` - Move/rename files
9. `search_files` - Search for files by pattern
10. `get_file_info` - Get file metadata
11. `list_allowed_directories` - Show accessible paths
12. `delete_file` - Delete files
13. `copy_file` - Copy files
14. `read_image` - Read and describe images

**Security Features:**
- Directory sandboxing (only access allowed paths)
- Path validation (prevents directory traversal)
- Safety annotations (read-only, idempotent, destructive)
- Dynamic access control via MCP Roots protocol

**Installation:**
```bash
npm install -g @modelcontextprotocol/server-filesystem
```

---

### 2. Advanced Filesystem Server

**Package:** `filesystem-mcp-server` (by cyanheads)
**Source:** https://github.com/cyanheads/filesystem-mcp-server
**Maintainer:** Community

**Additional Features:**
- HTTP transport (not just stdio)
- JWT authentication
- Session-aware paths
- More advanced regex support
- Metrics and logging

**Installation:**
```bash
npm install -g filesystem-mcp-server
```

---

## Official Server - Detailed Documentation

### Installation & Setup

#### Install Server
```bash
# Install globally
npm install -g @modelcontextprotocol/server-filesystem

# Or use via npx (no installation)
npx -y @modelcontextprotocol/server-filesystem
```

#### Basic Usage
```bash
# Allow access to specific directory
npx -y @modelcontextprotocol/server-filesystem /path/to/directory

# Allow multiple directories
npx -y @modelcontextprotocol/server-filesystem /path/one /path/two

# Allow home directory
npx -y @modelcontextprotocol/server-filesystem $HOME
```

---

### Tool Reference

#### 1. read_file
Read text content from a file.

**Parameters:**
```json
{
  "path": "string (required) - File path relative to allowed directories"
}
```

**Returns:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "File contents here..."
    }
  ]
}
```

**Example:**
```python
result = await client.call_tool("read_file", {
    "path": "documents/readme.txt"
})
content = result['content'][0]['text']
```

---

#### 2. write_file
Write content to a file (creates if doesn't exist).

**Parameters:**
```json
{
  "path": "string (required) - Target file path",
  "content": "string (required) - Content to write"
}
```

**Returns:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Successfully wrote to path/to/file"
    }
  ]
}
```

**Example:**
```python
result = await client.call_tool("write_file", {
    "path": "output/data.txt",
    "content": "Hello World!"
})
```

---

#### 3. edit_file
Perform targeted edits with search/replace.

**Parameters:**
```json
{
  "path": "string (required) - File to edit",
  "edits": [
    {
      "oldText": "string (required) - Text to find",
      "newText": "string (required) - Replacement text"
    }
  ],
  "dryRun": "boolean (optional) - Preview changes without applying"
}
```

**Returns:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Replaced X occurrences in file"
    }
  ]
}
```

**Example:**
```python
# Replace text
result = await client.call_tool("edit_file", {
    "path": "config.json",
    "edits": [
        {
            "oldText": '"debug": false',
            "newText": '"debug": true'
        }
    ]
})

# Dry run first
result = await client.call_tool("edit_file", {
    "path": "config.json",
    "edits": [...],
    "dryRun": True
})
```

---

#### 4. list_directory
List files and directories with details.

**Parameters:**
```json
{
  "path": "string (required) - Directory path"
}
```

**Returns:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "file1.txt (1.2 KB)\\nfile2.py (3.5 KB)\\nsubdir/ (directory)..."
    }
  ]
}
```

**Example:**
```python
result = await client.call_tool("list_directory", {
    "path": "projects"
})
```

---

#### 5. directory_tree
Get recursive directory tree.

**Parameters:**
```json
{
  "path": "string (required) - Root directory"
}
```

**Returns:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "project/\\n├── src/\\n│   ├── main.py\\n│   └── utils.py\\n└── tests/..."
    }
  ]
}
```

**Example:**
```python
result = await client.call_tool("directory_tree", {
    "path": "."
})
print(result['content'][0]['text'])
```

---

#### 6. search_files
Search for files by name pattern.

**Parameters:**
```json
{
  "path": "string (required) - Search root",
  "pattern": "string (required) - Glob pattern (e.g., '*.py', '**/*.txt')",
  "excludePatterns": ["string[] (optional) - Patterns to exclude"]
}
```

**Returns:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "/path/file1.py\\n/path/file2.py..."
    }
  ]
}
```

**Example:**
```python
# Find all Python files
result = await client.call_tool("search_files", {
    "path": "src",
    "pattern": "**/*.py",
    "excludePatterns": ["**/test_*.py", "**/__pycache__/**"]
})
```

---

#### 7. get_file_info
Get detailed file metadata.

**Parameters:**
```json
{
  "path": "string (required) - File path"
}
```

**Returns:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Size: 1024 bytes\\nCreated: 2026-01-01...\\nModified: 2026-01-09..."
    }
  ]
}
```

**Example:**
```python
result = await client.call_tool("get_file_info", {
    "path": "document.pdf"
})
```

---

#### 8. create_directory
Create a new directory (with parents if needed).

**Parameters:**
```json
{
  "path": "string (required) - Directory path"
}
```

**Example:**
```python
result = await client.call_tool("create_directory", {
    "path": "projects/new_project/src"
})
```

---

#### 9. move_file
Move or rename files/directories.

**Parameters:**
```json
{
  "source": "string (required) - Source path",
  "destination": "string (required) - Destination path"
}
```

**Example:**
```python
# Rename file
result = await client.call_tool("move_file", {
    "source": "old_name.txt",
    "destination": "new_name.txt"
})

# Move to different directory
result = await client.call_tool("move_file", {
    "source": "file.txt",
    "destination": "archive/file.txt"
})
```

---

### Security & Access Control

#### Directory Sandboxing

The server ONLY allows operations within specified directories:

```bash
# Allow single directory
npx -y @modelcontextprotocol/server-filesystem /home/user/projects

# Allow multiple directories
npx -y @modelcontextprotocol/server-filesystem /home/user/projects /home/user/documents

# On Windows
npx -y @modelcontextprotocol/server-filesystem "C:\Users\username\Projects"
```

**Important:** Without specifying directories, the server will not work.

#### Path Validation

All paths are validated to prevent:
- Directory traversal attacks (`../../../etc/passwd`)
- Symlink exploits
- Access outside allowed directories

#### Safety Annotations

Each tool has safety hints:
- **Read-only**: `read_file`, `list_directory`, `get_file_info`
- **Idempotent**: `write_file`, `create_directory`
- **Destructive**: `delete_file`, `move_file`

OSSARTH can use these hints to require user confirmation for destructive operations.

---

## Customization Guide

### Option 1: Configuration (No Code Changes)

#### Environment Variables
```bash
# Set environment for server
export FS_BASE_DIR="/path/to/root"
export FS_MAX_FILE_SIZE="10485760"  # 10MB

npx -y @modelcontextprotocol/server-filesystem $FS_BASE_DIR
```

#### Wrapper Script
Create `custom-filesystem-server.sh`:
```bash
#!/bin/bash
# Custom filesystem server with preset configuration

BASE_DIR="${HOME}/ossarth-workspace"
ALLOWED_DIRS=(
    "$BASE_DIR"
    "${HOME}/Documents"
    "/tmp/ossarth"
)

npx -y @modelcontextprotocol/server-filesystem "${ALLOWED_DIRS[@]}"
```

Make executable:
```bash
chmod +x custom-filesystem-server.sh
```

Use in OSSARTH:
```python
client = StdioMCPClient("./custom-filesystem-server.sh", [])
```

---

### Option 2: Fork & Modify (Full Control)

#### Step 1: Clone Repository
```bash
git clone https://github.com/modelcontextprotocol/servers.git
cd servers/src/filesystem
```

#### Step 2: Install Dependencies
```bash
npm install
```

#### Step 3: Understand Structure
```
filesystem/
├── src/
│   └── index.ts          # Main server implementation
├── package.json          # Dependencies and scripts
└── tsconfig.json         # TypeScript configuration
```

#### Step 4: Add Custom Tools

Edit `src/index.ts`:

```typescript
// Add new tool
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      // ... existing tools ...
      {
        name: "compress_file",
        description: "Compress a file using gzip",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "File to compress"
            }
          },
          required: ["path"]
        }
      }
    ]
  };
});

// Add tool handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "compress_file") {
    const filePath = args.path as string;
    // Add compression logic here
    const fs = await import('fs/promises');
    const zlib = await import('zlib');
    const { promisify } = await import('util');
    const gzip = promisify(zlib.gzip);

    const content = await fs.readFile(filePath);
    const compressed = await gzip(content);
    await fs.writeFile(`${filePath}.gz`, compressed);

    return {
      content: [
        {
          type: "text",
          text: `Compressed ${filePath} to ${filePath}.gz`
        }
      ]
    };
  }

  // ... existing tool handlers ...
});
```

#### Step 5: Build
```bash
npm run build
```

#### Step 6: Test Locally
```bash
node dist/index.js /path/to/test
```

#### Step 7: Use in OSSARTH
```python
client = StdioMCPClient(
    "node",
    ["/path/to/servers/src/filesystem/dist/index.js", "/allowed/path"]
)
```

---

### Option 3: Python Wrapper (Best for OSSARTH)

Create a Python wrapper that adds functionality:

```python
# D:\llm-os\src\llm_os\mcp\wrappers\filesystem_wrapper.py

from llm_os.mcp.client.stdio_client import StdioMCPClient
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FilesystemServerWrapper:
    """
    Wrapper around external filesystem server with additional functionality.
    """

    def __init__(self, allowed_dirs: list[str]):
        """Initialize with allowed directories."""
        self.allowed_dirs = [str(Path(d).resolve()) for d in allowed_dirs]
        self.client = StdioMCPClient(
            "npx",
            ["-y", "@modelcontextprotocol/server-filesystem"] + self.allowed_dirs
        )

    async def initialize(self):
        """Initialize the filesystem server."""
        await self.client.initialize()
        logger.info(f"Filesystem server initialized with {len(self.allowed_dirs)} allowed directories")

    async def read_file(self, path: str) -> str:
        """Read a file with additional validation."""
        # Add custom validation
        if not self._is_allowed_path(path):
            raise PermissionError(f"Access denied: {path}")

        result = await self.client.call_tool("read_file", {"path": path})
        if result.get("isError"):
            raise RuntimeError(result["content"][0]["text"])

        return result["content"][0]["text"]

    async def write_file(self, path: str, content: str) -> None:
        """Write a file with backup."""
        # Create backup if file exists
        backup_result = await self.client.call_tool("get_file_info", {"path": path})
        if not backup_result.get("isError"):
            await self._create_backup(path)

        # Write file
        result = await self.client.call_tool("write_file", {
            "path": path,
            "content": content
        })

        if result.get("isError"):
            raise RuntimeError(result["content"][0]["text"])

    async def search_code(self, pattern: str, extensions: list[str]) -> list[str]:
        """Search for code files with specific extensions."""
        results = []
        for ext in extensions:
            result = await self.client.call_tool("search_files", {
                "path": ".",
                "pattern": f"**/*{ext}"
            })

            if not result.get("isError"):
                files = result["content"][0]["text"].split("\n")
                results.extend([f for f in files if f])

        return results

    async def safe_delete(self, path: str, confirm: bool = True) -> None:
        """Delete with confirmation and trash support."""
        if confirm:
            # In real implementation, prompt user
            logger.warning(f"Deleting: {path}")

        # Move to trash instead of permanent delete
        trash_path = Path(".trash") / Path(path).name
        await self.client.call_tool("move_file", {
            "source": path,
            "destination": str(trash_path)
        })

    def _is_allowed_path(self, path: str) -> bool:
        """Check if path is within allowed directories."""
        path_obj = Path(path).resolve()
        return any(
            str(path_obj).startswith(allowed)
            for allowed in self.allowed_dirs
        )

    async def _create_backup(self, path: str) -> None:
        """Create backup of file."""
        backup_path = f"{path}.backup"
        await self.client.call_tool("copy_file", {
            "source": path,
            "destination": backup_path
        })

    async def close(self):
        """Close the client."""
        await self.client.close()
```

**Usage:**
```python
# In OSSARTH
wrapper = FilesystemServerWrapper([
    "/home/user/projects",
    "/home/user/documents"
])

await wrapper.initialize()

# Use enhanced methods
content = await wrapper.read_file("project/readme.md")
await wrapper.write_file("output.txt", "Hello!")
code_files = await wrapper.search_code("*.py", [".py", ".pyx"])
await wrapper.safe_delete("old_file.txt")

await wrapper.close()
```

---

## Integration with OSSARTH

### Step 1: Test the Server

Create `D:\llm-os\tests\mcp\tests\test_filesystem_external.py`:

```python
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from client.mcp_client import SimpleMCPClient


async def test_filesystem():
    """Test external filesystem server."""
    print("Testing External Filesystem Server")
    print("="*60)

    # Allow current directory
    client = SimpleMCPClient("npx", [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        str(Path.cwd())
    ])

    try:
        await client.start()
        await client.initialize()

        print(f"Server: {client.server_info}")
        tools = await client.list_tools()
        print(f"Tools: {len(tools)}")

        # Test read
        result = await client.call_tool("list_directory", {"path": "."})
        print(f"\\nCurrent directory:\\n{result['content'][0]['text'][:200]}...")

        print("\\n" + "="*60)
        print("SUCCESS!")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_filesystem())
```

Run:
```bash
cd D:\llm-os\tests\mcp
python tests/test_filesystem_external.py
```

### Step 2: Add to Configuration

Edit `D:\llm-os\config\default.yaml`:

```yaml
mcp:
  servers:
    external:
      filesystem:
        enabled: true
        package: "@modelcontextprotocol/server-filesystem"
        args:
          - "${HOME}/Documents"
          - "${HOME}/Projects"
        env: {}
```

### Step 3: Update Server Manager

The existing `stdio_client.py` already supports this. Just register the server:

```python
# In orchestrator or server manager
from llm_os.mcp.client.stdio_client import MCPClientPool

pool = MCPClientPool()

await pool.add_client(
    server_id="filesystem_external",
    command="npx",
    args=[
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/user/projects"
    ]
)

# Use tools
client = pool.get_client("filesystem_external")
result = await client.call_tool("read_file", {"path": "readme.md"})
```

---

## Comparison: Internal vs External

| Feature | Internal (Python) | External (Node.js) |
|---------|------------------|-------------------|
| Speed | <1ms | ~50ms |
| Tools | 13 tools | 14 tools |
| Regex | No | Yes (edit_file) |
| Bulk Ops | Limited | Yes (read_multiple) |
| Security | Basic | Advanced |
| Maintenance | You | Anthropic |
| Customization | Easy (Python) | Medium (TypeScript) |
| Dependencies | None | Node.js |

**Recommendation:** Use external server for:
- Production deployments
- Advanced features (regex, bulk operations)
- Better security requirements
- Official support and updates

Use internal server for:
- Quick prototyping
- Python-only environments
- Custom business logic

---

## Resources

- **Official Server:** https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- **Npm Package:** https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem
- **MCP Specification:** https://modelcontextprotocol.io/
- **Server Directory:** https://mcpservers.org/servers/modelcontextprotocol/filesystem
- **Advanced Server:** https://github.com/cyanheads/filesystem-mcp-server

---

## Next Steps

1. Test the external filesystem server
2. Choose customization approach (wrapper recommended)
3. Integrate with OSSARTH orchestrator
4. Add configuration to default.yaml
5. Test with actual file operations
6. Disable or remove internal filesystem server if not needed

---

**Status:** Ready for Integration
**Recommended:** Official @modelcontextprotocol/server-filesystem with Python wrapper
