# LLM-OS: MCP Architecture and Design

## Overview

The Model Context Protocol (MCP) is the backbone of LLM-OS, providing standardized interfaces between the LLM and system operations. This document details the MCP architecture, server design patterns, and implementation strategy.

---

## 1. Understanding MCP

### 1.1 What is MCP?

**Model Context Protocol (MCP)** is an open standard introduced by Anthropic in November 2024 to standardize how AI systems interact with external tools and data sources.

**Key Concepts**:
- **Server**: Provides tools, resources, and prompts to AI clients
- **Client**: Connects to servers and uses their capabilities
- **Transport**: Communication layer (stdio, HTTP, WebSocket)
- **Tools**: Functions the AI can call to perform actions
- **Resources**: Data sources the AI can read
- **Prompts**: Pre-defined prompt templates

### 1.2 MCP in LLM-OS Context

```
┌─────────────────────────────────────────────────────────────────┐
│                        LLM-OS Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Input → NL-Shell → LLM → MCP Client → MCP Servers        │
│                                      │              │            │
│                                      │              ▼            │
│                                      │     ┌─────────────────┐  │
│                                      │     │ Filesystem      │  │
│                                      │     │ Applications    │  │
│                                      │     │ Browser         │  │
│                                      │     │ Git             │  │
│                                      │     │ System          │  │
│                                      │     │ Media           │  │
│                                      │     │ ...             │  │
│                                      │     └─────────────────┘  │
│                                      │              │            │
│                                      │              ▼            │
│   User Output ← NL-Shell ← LLM ← ────┴──── Results              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Why MCP for LLM-OS?

| Benefit | Description |
|---------|-------------|
| **Standardization** | Common interface for all tools |
| **Modularity** | Add/remove capabilities easily |
| **Ecosystem** | 1000s of existing MCP servers |
| **Security** | Per-server permission control |
| **Extensibility** | Users can create custom servers |
| **Industry Adoption** | OpenAI, Google, Microsoft support MCP |

---

## 2. MCP Protocol Deep Dive

### 2.1 Server Capabilities

MCP servers can provide three types of capabilities:

#### Tools
Executable functions the LLM can call:
```json
{
  "name": "read_file",
  "description": "Read contents of a file at the specified path",
  "inputSchema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "Absolute path to the file"
      }
    },
    "required": ["path"]
  }
}
```

#### Resources
Data sources the LLM can access:
```json
{
  "uri": "file:///home/user/documents",
  "name": "User Documents",
  "description": "User's document folder",
  "mimeType": "inode/directory"
}
```

#### Prompts
Pre-defined prompt templates:
```json
{
  "name": "explain_code",
  "description": "Explain code in detail",
  "arguments": [
    {
      "name": "code",
      "description": "The code to explain",
      "required": true
    }
  ]
}
```

### 2.2 Transport Layers

| Transport | Use Case | Pros | Cons |
|-----------|----------|------|------|
| **stdio** | Local servers | Simple, secure | Process per server |
| **HTTP/SSE** | Remote servers | Network capable | More complex |
| **WebSocket** | Real-time | Bidirectional | Connection management |

**LLM-OS Default**: stdio for local servers (security, simplicity)

### 2.3 Communication Flow

```
1. Client Discovery
   Client ─────────────────────────────────────────────────► Server
         "initialize" request with capabilities
   Client ◄───────────────────────────────────────────────── Server
         "initialize" response with server capabilities

2. Tool Discovery
   Client ─────────────────────────────────────────────────► Server
         "tools/list" request
   Client ◄───────────────────────────────────────────────── Server
         List of available tools

3. Tool Execution
   Client ─────────────────────────────────────────────────► Server
         "tools/call" with tool name and arguments
   Client ◄───────────────────────────────────────────────── Server
         Tool result (text, images, etc.)
```

---

## 3. LLM-OS MCP Architecture

### 3.1 Component Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                          MCP Orchestrator                         │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Server      │  │ Tool        │  │ Context                 │  │
│  │ Manager     │  │ Router      │  │ Manager                 │  │
│  │             │  │             │  │                         │  │
│  │ - Start     │  │ - Select    │  │ - Conversation history  │  │
│  │ - Stop      │  │   server    │  │ - Tool results          │  │
│  │ - Monitor   │  │ - Route     │  │ - User preferences      │  │
│  │ - Discover  │  │   requests  │  │ - Session state         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│         │                │                      │                │
│         ▼                ▼                      ▼                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    MCP Server Pool                        │   │
│  │                                                           │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │   │
│  │  │filesys │ │ apps   │ │browser │ │  git   │ │ system │ │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │   │
│  │  │ media  │ │ docker │ │database│ │network │ │ custom │ │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Server Manager

Responsible for lifecycle management of MCP servers:

```python
class ServerManager:
    """Manages MCP server lifecycle"""

    async def discover_servers(self) -> list[ServerConfig]:
        """Scan for available MCP servers"""
        # Check /etc/llm-os/mcp-servers/
        # Check ~/.config/llm-os/mcp-servers/
        # Check environment for remote servers
        pass

    async def start_server(self, server_id: str) -> MCPConnection:
        """Start an MCP server process"""
        pass

    async def stop_server(self, server_id: str) -> None:
        """Stop an MCP server process"""
        pass

    async def get_server_status(self, server_id: str) -> ServerStatus:
        """Check if server is running and healthy"""
        pass

    async def list_all_tools(self) -> list[Tool]:
        """Aggregate tools from all running servers"""
        pass
```

### 3.3 Tool Router

Selects appropriate server for each tool request:

```python
class ToolRouter:
    """Routes tool calls to appropriate MCP servers"""

    def __init__(self, server_manager: ServerManager):
        self.server_manager = server_manager
        self.tool_registry: dict[str, str] = {}  # tool_name -> server_id

    async def build_registry(self) -> None:
        """Build mapping of tools to servers"""
        for server in await self.server_manager.list_servers():
            tools = await server.list_tools()
            for tool in tools:
                self.tool_registry[tool.name] = server.id

    async def route_tool_call(
        self,
        tool_name: str,
        arguments: dict
    ) -> ToolResult:
        """Route tool call to appropriate server"""
        server_id = self.tool_registry.get(tool_name)
        if not server_id:
            raise ToolNotFoundError(tool_name)

        server = await self.server_manager.get_server(server_id)
        return await server.call_tool(tool_name, arguments)
```

### 3.4 Context Manager

Maintains conversation and execution context:

```python
class ContextManager:
    """Manages conversation and tool execution context"""

    def __init__(self):
        self.conversation_history: list[Message] = []
        self.tool_results: dict[str, any] = {}
        self.session_state: dict[str, any] = {}
        self.last_referenced: dict[str, any] = {}  # For pronouns/references

    def add_user_message(self, content: str) -> None:
        """Add user message to history"""
        self.conversation_history.append(
            Message(role="user", content=content)
        )

    def add_assistant_message(self, content: str) -> None:
        """Add assistant message to history"""
        self.conversation_history.append(
            Message(role="assistant", content=content)
        )

    def add_tool_result(self, tool_name: str, result: any) -> None:
        """Store tool result for context"""
        self.tool_results[tool_name] = result
        # Update references
        if 'files' in str(result):
            self.last_referenced['files'] = result

    def get_context_for_llm(self, max_tokens: int = 8000) -> list[Message]:
        """Get relevant context for LLM request"""
        # Implement context window management
        pass
```

---

## 4. MCP Server Categories

### 4.1 Core System Servers

| Server | Tools | Priority |
|--------|-------|----------|
| **filesystem** | read, write, list, move, copy, delete | P0 |
| **process** | run, list, kill, status | P0 |
| **system** | info, users, services, shutdown | P0 |
| **network** | ping, dns, connections, firewall | P1 |
| **package** | install, remove, update, search | P1 |

### 4.2 Application Servers

| Server | Tools | Priority |
|--------|-------|----------|
| **applications** | launch, close, list, focus | P0 |
| **browser** | open, navigate, search, screenshot | P0 |
| **vscode** | open_project, open_file, extensions | P1 |
| **terminal** | new_session, run_command, history | P1 |

### 4.3 Development Servers

| Server | Tools | Priority |
|--------|-------|----------|
| **git** | clone, commit, push, pull, status, diff | P0 |
| **docker** | run, stop, build, compose, logs | P1 |
| **database** | query, connect, tables, backup | P2 |
| **python** | run, pip, venv, debug | P1 |

### 4.4 Productivity Servers

| Server | Tools | Priority |
|--------|-------|----------|
| **clipboard** | copy, paste, history | P1 |
| **screenshot** | capture, region, window | P1 |
| **notifications** | send, schedule, list | P2 |
| **calendar** | events, reminders, schedule | P2 |

### 4.5 Media Servers

| Server | Tools | Priority |
|--------|-------|----------|
| **audio** | play, pause, volume, devices | P2 |
| **video** | play, pause, seek, info | P2 |
| **image** | view, resize, convert, info | P2 |

---

## 5. MCP Server Implementation

### 5.1 Python Server Template

```python
#!/usr/bin/env python3
"""Template for LLM-OS MCP Server"""

import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent

# Create server instance
server = Server("server-name")

# Define tools
@server.list_tools()
async def list_tools():
    """Return list of available tools"""
    return [
        Tool(
            name="tool_name",
            description="What this tool does",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter description"
                    }
                },
                "required": ["param1"]
            }
        )
    ]

# Implement tools
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    if name == "tool_name":
        result = do_something(arguments["param1"])
        return [TextContent(type="text", text=str(result))]
    raise ValueError(f"Unknown tool: {name}")

# Run server
async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### 5.2 Example: Filesystem Server

```python
#!/usr/bin/env python3
"""Filesystem MCP Server for LLM-OS"""

import os
import shutil
from pathlib import Path
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("filesystem")

ALLOWED_PATHS = [
    Path.home(),
    Path("/tmp"),
    Path("/var/log")
]

def is_path_allowed(path: str) -> bool:
    """Check if path is within allowed directories"""
    p = Path(path).resolve()
    return any(p.is_relative_to(allowed) for allowed in ALLOWED_PATHS)

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="read_file",
            description="Read the contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_directory",
            description="List contents of a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"},
                    "show_hidden": {"type": "boolean", "default": False}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="move_file",
            description="Move a file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Source path"},
                    "destination": {"type": "string", "description": "Destination path"}
                },
                "required": ["source", "destination"]
            }
        ),
        Tool(
            name="copy_file",
            description="Copy a file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Source path"},
                    "destination": {"type": "string", "description": "Destination path"}
                },
                "required": ["source", "destination"]
            }
        ),
        Tool(
            name="delete",
            description="Delete a file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to delete"},
                    "recursive": {"type": "boolean", "default": False}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="create_directory",
            description="Create a new directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to create"}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="file_info",
            description="Get information about a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="search_files",
            description="Search for files matching a pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to search"},
                    "pattern": {"type": "string", "description": "Glob pattern (e.g., *.py)"}
                },
                "required": ["directory", "pattern"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "read_file":
            path = arguments["path"]
            if not is_path_allowed(path):
                return [TextContent(type="text", text=f"Error: Access denied to {path}")]

            with open(path, 'r') as f:
                content = f.read()
            return [TextContent(type="text", text=content)]

        elif name == "write_file":
            path = arguments["path"]
            content = arguments["content"]
            if not is_path_allowed(path):
                return [TextContent(type="text", text=f"Error: Access denied to {path}")]

            with open(path, 'w') as f:
                f.write(content)
            return [TextContent(type="text", text=f"Successfully wrote to {path}")]

        elif name == "list_directory":
            path = arguments["path"]
            show_hidden = arguments.get("show_hidden", False)
            if not is_path_allowed(path):
                return [TextContent(type="text", text=f"Error: Access denied to {path}")]

            entries = []
            for entry in Path(path).iterdir():
                if not show_hidden and entry.name.startswith('.'):
                    continue
                entry_type = "DIR" if entry.is_dir() else "FILE"
                size = entry.stat().st_size if entry.is_file() else "-"
                entries.append(f"{entry_type}\t{size}\t{entry.name}")

            result = f"Contents of {path}:\n" + "\n".join(entries)
            return [TextContent(type="text", text=result)]

        elif name == "move_file":
            source = arguments["source"]
            destination = arguments["destination"]
            if not (is_path_allowed(source) and is_path_allowed(destination)):
                return [TextContent(type="text", text="Error: Access denied")]

            shutil.move(source, destination)
            return [TextContent(type="text", text=f"Moved {source} to {destination}")]

        elif name == "copy_file":
            source = arguments["source"]
            destination = arguments["destination"]
            if not (is_path_allowed(source) and is_path_allowed(destination)):
                return [TextContent(type="text", text="Error: Access denied")]

            if Path(source).is_dir():
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
            return [TextContent(type="text", text=f"Copied {source} to {destination}")]

        elif name == "delete":
            path = arguments["path"]
            recursive = arguments.get("recursive", False)
            if not is_path_allowed(path):
                return [TextContent(type="text", text=f"Error: Access denied to {path}")]

            p = Path(path)
            if p.is_dir():
                if recursive:
                    shutil.rmtree(path)
                else:
                    p.rmdir()
            else:
                p.unlink()
            return [TextContent(type="text", text=f"Deleted {path}")]

        elif name == "create_directory":
            path = arguments["path"]
            if not is_path_allowed(path):
                return [TextContent(type="text", text=f"Error: Access denied to {path}")]

            Path(path).mkdir(parents=True, exist_ok=True)
            return [TextContent(type="text", text=f"Created directory {path}")]

        elif name == "file_info":
            path = arguments["path"]
            if not is_path_allowed(path):
                return [TextContent(type="text", text=f"Error: Access denied to {path}")]

            p = Path(path)
            stat = p.stat()
            info = {
                "name": p.name,
                "path": str(p.absolute()),
                "type": "directory" if p.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "permissions": oct(stat.st_mode)[-3:]
            }
            return [TextContent(type="text", text=str(info))]

        elif name == "search_files":
            directory = arguments["directory"]
            pattern = arguments["pattern"]
            if not is_path_allowed(directory):
                return [TextContent(type="text", text=f"Error: Access denied to {directory}")]

            matches = list(Path(directory).rglob(pattern))
            result = f"Found {len(matches)} files matching '{pattern}':\n"
            result += "\n".join(str(m) for m in matches[:100])  # Limit results
            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### 5.3 Example: Applications Server

```python
#!/usr/bin/env python3
"""Applications MCP Server for LLM-OS"""

import subprocess
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("applications")

# Application registry
APP_REGISTRY = {
    "firefox": {"command": "firefox", "category": "browser"},
    "chrome": {"command": "google-chrome", "category": "browser"},
    "chromium": {"command": "chromium-browser", "category": "browser"},
    "vscode": {"command": "code", "category": "development"},
    "terminal": {"command": "gnome-terminal", "category": "utility"},
    "files": {"command": "nautilus", "category": "utility"},
    "calculator": {"command": "gnome-calculator", "category": "utility"},
    "vlc": {"command": "vlc", "category": "media"},
    "gimp": {"command": "gimp", "category": "graphics"},
    "libreoffice": {"command": "libreoffice", "category": "office"},
}

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="launch_app",
            description="Launch an application by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name of the application (e.g., firefox, vscode)"
                    },
                    "arguments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional arguments to pass to the application"
                    }
                },
                "required": ["app_name"]
            }
        ),
        Tool(
            name="list_apps",
            description="List available applications",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by category (browser, development, utility, media, graphics, office)"
                    }
                }
            }
        ),
        Tool(
            name="close_app",
            description="Close an application by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name of the application to close"
                    }
                },
                "required": ["app_name"]
            }
        ),
        Tool(
            name="running_apps",
            description="List currently running applications",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="open_with",
            description="Open a file with a specific application",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file"},
                    "app_name": {"type": "string", "description": "Application to open with"}
                },
                "required": ["file_path", "app_name"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "launch_app":
            app_name = arguments["app_name"].lower()
            args = arguments.get("arguments", [])

            # Check registry
            if app_name in APP_REGISTRY:
                command = APP_REGISTRY[app_name]["command"]
            else:
                # Try direct command
                command = app_name

            # Launch application
            cmd = [command] + args
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            return [TextContent(
                type="text",
                text=f"Launched {app_name} (PID: {process.pid})"
            )]

        elif name == "list_apps":
            category = arguments.get("category")

            if category:
                apps = {k: v for k, v in APP_REGISTRY.items()
                        if v["category"] == category}
            else:
                apps = APP_REGISTRY

            result = "Available applications:\n"
            for name, info in apps.items():
                result += f"  - {name} [{info['category']}]\n"

            return [TextContent(type="text", text=result)]

        elif name == "close_app":
            app_name = arguments["app_name"].lower()

            if app_name in APP_REGISTRY:
                command = APP_REGISTRY[app_name]["command"]
            else:
                command = app_name

            # Use pkill to close
            subprocess.run(["pkill", "-f", command], capture_output=True)

            return [TextContent(type="text", text=f"Closed {app_name}")]

        elif name == "running_apps":
            # Get running GUI applications
            result = subprocess.run(
                ["wmctrl", "-l"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return [TextContent(
                    type="text",
                    text=f"Running applications:\n{result.stdout}"
                )]
            else:
                # Fallback to ps
                result = subprocess.run(
                    ["ps", "aux", "--sort=-%mem"],
                    capture_output=True,
                    text=True
                )
                return [TextContent(
                    type="text",
                    text=f"Running processes:\n{result.stdout[:2000]}"
                )]

        elif name == "open_with":
            file_path = arguments["file_path"]
            app_name = arguments["app_name"].lower()

            if app_name in APP_REGISTRY:
                command = APP_REGISTRY[app_name]["command"]
            else:
                command = app_name

            subprocess.Popen(
                [command, file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            return [TextContent(
                type="text",
                text=f"Opened {file_path} with {app_name}"
            )]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. Server Discovery and Configuration

### 6.1 Server Configuration File

```yaml
# /etc/llm-os/mcp-config.yaml

# Global settings
global:
  auto_start: true
  log_level: info
  timeout: 30s

# Server definitions
servers:
  filesystem:
    command: python3
    args: ["/usr/lib/llm-os/mcp-servers/filesystem.py"]
    env:
      ALLOWED_PATHS: "/home,/tmp"
    auto_start: true

  applications:
    command: python3
    args: ["/usr/lib/llm-os/mcp-servers/applications.py"]
    auto_start: true

  browser:
    command: node
    args: ["/usr/lib/llm-os/mcp-servers/browser/index.js"]
    auto_start: false  # Start on demand

  git:
    command: python3
    args: ["/usr/lib/llm-os/mcp-servers/git.py"]
    auto_start: true

  # External MCP servers (community)
  slack:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-slack"]
    env:
      SLACK_TOKEN: "${SLACK_TOKEN}"
    auto_start: false

  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
    auto_start: false
```

### 6.2 User Custom Servers

```yaml
# ~/.config/llm-os/custom-servers.yaml

servers:
  my-custom-tool:
    command: python3
    args: ["/home/user/mcp-servers/my-tool.py"]
    description: "My custom MCP server"
    auto_start: true
```

### 6.3 Server Discovery Process

```python
async def discover_servers() -> list[ServerConfig]:
    """Discover all available MCP servers"""
    servers = []

    # 1. System servers
    system_config = Path("/etc/llm-os/mcp-config.yaml")
    if system_config.exists():
        servers.extend(load_config(system_config))

    # 2. User servers
    user_config = Path.home() / ".config/llm-os/custom-servers.yaml"
    if user_config.exists():
        servers.extend(load_config(user_config))

    # 3. Auto-discover from mcp-servers directories
    for path in [Path("/usr/lib/llm-os/mcp-servers"),
                 Path.home() / ".local/lib/llm-os/mcp-servers"]:
        if path.exists():
            for server_dir in path.iterdir():
                if (server_dir / "manifest.yaml").exists():
                    servers.append(load_server_manifest(server_dir))

    return servers
```

---

## 7. Security Considerations

### 7.1 Permission Levels

| Level | Description | Example Operations |
|-------|-------------|-------------------|
| **READ** | Read-only access | List files, read content, view status |
| **WRITE** | Modify user data | Write files, edit documents |
| **EXECUTE** | Run programs | Launch apps, run scripts |
| **SYSTEM** | System changes | Install packages, modify config |
| **DANGEROUS** | Irreversible actions | Delete files, format drives |

### 7.2 Confirmation Requirements

```python
REQUIRES_CONFIRMATION = {
    "delete": "This will delete files permanently. Continue?",
    "format": "This will format the disk. Are you absolutely sure?",
    "uninstall": "This will remove the application. Continue?",
    "shutdown": "This will shut down the system. Proceed?",
    "send_email": "Send this email? You cannot undo this.",
}
```

### 7.3 Sandboxing Strategy

```bash
# Use firejail for untrusted servers
firejail --private --net=none python3 /path/to/untrusted-server.py
```

---

## 8. Integration with LLM

### 8.1 Tool Selection Prompt

```
You are an AI assistant operating within LLM-OS. You have access to the following tools:

{tools_list}

When the user makes a request:
1. Determine which tool(s) are needed
2. Call tools with appropriate arguments
3. Report results clearly to the user

Important guidelines:
- Always confirm before destructive operations (delete, format, etc.)
- Explain what you're doing before executing
- Handle errors gracefully
- Ask for clarification if the request is ambiguous
```

### 8.2 Tool Calling Format

```python
# System prompt includes tool definitions
tools = orchestrator.get_all_tools()

# LLM response might include tool calls
response = llm.complete(
    messages=conversation_history,
    tools=tools,
    tool_choice="auto"
)

# Process tool calls
if response.tool_calls:
    for tool_call in response.tool_calls:
        result = await orchestrator.execute_tool(
            tool_call.name,
            tool_call.arguments
        )
        # Add result to conversation
        conversation_history.append(tool_result_message(result))
```

---

## 9. Testing Strategy

### 9.1 Unit Tests for MCP Servers

```python
import pytest
from mcp_servers.filesystem import call_tool

@pytest.mark.asyncio
async def test_read_file():
    result = await call_tool("read_file", {"path": "/tmp/test.txt"})
    assert "content" in result[0].text

@pytest.mark.asyncio
async def test_access_denied():
    result = await call_tool("read_file", {"path": "/etc/shadow"})
    assert "denied" in result[0].text.lower()
```

### 9.2 Integration Tests

```python
@pytest.mark.asyncio
async def test_tool_routing():
    orchestrator = MCPOrchestrator()
    await orchestrator.initialize()

    # Test that filesystem tools route correctly
    result = await orchestrator.execute_tool(
        "list_directory",
        {"path": "/tmp"}
    )
    assert result.success
```

---

## 10. Next Steps

1. **Implement core MCP servers** (filesystem, applications)
2. **Build MCP orchestrator** with server management
3. **Integrate with LLM** layer
4. **Add security** layer with confirmations
5. **Test end-to-end** workflow
6. **Document API** for custom server development

---

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Anthropic MCP Introduction](https://www.anthropic.com/news/model-context-protocol)
- [MCP Server Registry](https://github.com/modelcontextprotocol/servers)

---

*Document Version: 1.0*
*Last Updated: January 2026*
