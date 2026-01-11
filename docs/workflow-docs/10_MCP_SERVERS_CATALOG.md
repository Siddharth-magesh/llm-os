# LLM-OS: MCP Servers Catalog

## Overview

This document catalogs all MCP servers planned for LLM-OS, including built-in servers, community servers to integrate, and custom servers to develop. Each server is documented with its tools, priority, and implementation notes.

---

## 1. Server Categories

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MCP Server Categories                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  🔵 Core System (P0)    Essential for basic functionality                   │
│  🟢 Applications (P0)   App launching and management                        │
│  🟡 Development (P1)    Developer-focused tools                             │
│  🟠 Productivity (P1)   User productivity features                          │
│  🟣 Media (P2)          Audio, video, image handling                        │
│  🔴 Advanced (P2)       Advanced/optional features                          │
│  ⚪ Community (P2)      Third-party/community servers                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core System Servers (P0)

### 2.1 Filesystem Server

**Priority**: P0 - Critical
**Language**: Python
**Status**: To Develop

| Tool | Description | Parameters |
|------|-------------|------------|
| `read_file` | Read contents of a file | `path: string` |
| `write_file` | Write content to a file | `path: string, content: string` |
| `list_directory` | List directory contents | `path: string, show_hidden?: boolean` |
| `create_directory` | Create a new directory | `path: string` |
| `move` | Move file or directory | `source: string, destination: string` |
| `copy` | Copy file or directory | `source: string, destination: string` |
| `delete` | Delete file or directory | `path: string, recursive?: boolean` |
| `file_info` | Get file metadata | `path: string` |
| `search_files` | Search for files | `directory: string, pattern: string` |
| `get_size` | Get file or directory size | `path: string` |

**Security Considerations**:
- Restrict to user home and allowed directories
- Require confirmation for delete operations
- No access to system files without elevation

---

### 2.2 Process Server

**Priority**: P0 - Critical
**Language**: Python
**Status**: To Develop

| Tool | Description | Parameters |
|------|-------------|------------|
| `run_command` | Execute a shell command | `command: string, timeout?: number` |
| `list_processes` | List running processes | `sort_by?: string` |
| `get_process_info` | Get info about a process | `pid: number` |
| `kill_process` | Terminate a process | `pid: number, signal?: string` |
| `get_output` | Get command output | `pid: number` |

**Security Considerations**:
- Sanitize command input
- Prevent shell injection
- Limit dangerous commands

---

### 2.3 System Server

**Priority**: P0 - Critical
**Language**: Python
**Status**: To Develop

| Tool | Description | Parameters |
|------|-------------|------------|
| `system_info` | Get system information | - |
| `disk_usage` | Get disk usage stats | `path?: string` |
| `memory_usage` | Get memory statistics | - |
| `cpu_usage` | Get CPU usage | - |
| `uptime` | Get system uptime | - |
| `hostname` | Get/set hostname | `new_name?: string` |
| `users` | List logged-in users | - |
| `environment` | Get environment variables | `name?: string` |
| `shutdown` | Shutdown system | `mode: string` |
| `reboot` | Reboot system | - |

**Security Considerations**:
- Shutdown/reboot require confirmation
- Some operations require sudo

---

## 3. Application Servers (P0)

### 3.1 Applications Server

**Priority**: P0 - Critical
**Language**: Python
**Status**: To Develop

| Tool | Description | Parameters |
|------|-------------|------------|
| `launch_app` | Launch an application | `app_name: string, args?: string[]` |
| `close_app` | Close an application | `app_name: string` |
| `list_installed` | List installed applications | `category?: string` |
| `list_running` | List running applications | - |
| `focus_window` | Focus a window | `app_name: string` |
| `minimize_window` | Minimize a window | `app_name: string` |
| `maximize_window` | Maximize a window | `app_name: string` |
| `get_app_info` | Get application info | `app_name: string` |

**Supported Applications** (initial):

| App Name | Command | Category |
|----------|---------|----------|
| firefox | firefox | browser |
| chrome | google-chrome | browser |
| chromium | chromium-browser | browser |
| vscode | code | development |
| terminal | gnome-terminal | utility |
| files | nautilus | utility |
| calculator | gnome-calculator | utility |
| settings | gnome-control-center | utility |
| vlc | vlc | media |
| gimp | gimp | graphics |
| libreoffice-writer | libreoffice --writer | office |
| libreoffice-calc | libreoffice --calc | office |
| libreoffice-impress | libreoffice --impress | office |

---

### 3.2 Browser Server

**Priority**: P0 - Critical
**Language**: TypeScript (Puppeteer)
**Status**: To Develop

| Tool | Description | Parameters |
|------|-------------|------------|
| `open_browser` | Open browser to URL | `url: string` |
| `navigate` | Navigate to URL | `url: string` |
| `search` | Perform web search | `query: string, engine?: string` |
| `get_page_content` | Get page text content | - |
| `get_page_title` | Get page title | - |
| `click_element` | Click an element | `selector: string` |
| `type_text` | Type into an element | `selector: string, text: string` |
| `screenshot` | Take page screenshot | `path?: string` |
| `scroll` | Scroll the page | `direction: string, amount?: number` |
| `close_tab` | Close current tab | - |
| `list_tabs` | List open tabs | - |

**Implementation Notes**:
- Use Puppeteer for automation
- Fall back to xdotool for basic operations
- Consider privacy: don't capture passwords

---

## 4. Development Servers (P1)

### 4.1 Git Server

**Priority**: P1 - High
**Language**: Python
**Status**: To Develop

| Tool | Description | Parameters |
|------|-------------|------------|
| `git_status` | Get repository status | `path?: string` |
| `git_clone` | Clone a repository | `url: string, path?: string` |
| `git_pull` | Pull from remote | `path?: string` |
| `git_push` | Push to remote | `path?: string` |
| `git_commit` | Create a commit | `message: string, path?: string` |
| `git_add` | Stage files | `files: string[], path?: string` |
| `git_log` | Show commit history | `n?: number, path?: string` |
| `git_diff` | Show changes | `path?: string` |
| `git_branch` | List/create branches | `name?: string, path?: string` |
| `git_checkout` | Switch branches | `branch: string, path?: string` |
| `git_stash` | Stash changes | `action?: string, path?: string` |

---

### 4.2 Docker Server

**Priority**: P1 - High
**Language**: Python
**Status**: To Develop

| Tool | Description | Parameters |
|------|-------------|------------|
| `docker_ps` | List containers | `all?: boolean` |
| `docker_run` | Run a container | `image: string, name?: string, ...` |
| `docker_stop` | Stop a container | `container: string` |
| `docker_rm` | Remove a container | `container: string` |
| `docker_logs` | Get container logs | `container: string, tail?: number` |
| `docker_images` | List images | - |
| `docker_pull` | Pull an image | `image: string` |
| `docker_build` | Build an image | `path: string, tag?: string` |
| `docker_compose_up` | Start compose stack | `path?: string` |
| `docker_compose_down` | Stop compose stack | `path?: string` |

---

### 4.3 Python Server

**Priority**: P1 - Medium
**Language**: Python
**Status**: To Develop

| Tool | Description | Parameters |
|------|-------------|------------|
| `python_run` | Run Python script | `script: string` |
| `python_repl` | Execute Python code | `code: string` |
| `pip_install` | Install package | `package: string` |
| `pip_list` | List installed packages | - |
| `venv_create` | Create virtual environment | `path: string` |
| `venv_activate` | Get activation command | `path: string` |

---

### 4.4 Database Server

**Priority**: P2 - Medium
**Language**: Python
**Status**: Future

| Tool | Description | Parameters |
|------|-------------|------------|
| `db_connect` | Connect to database | `type: string, connection_string: string` |
| `db_query` | Execute SQL query | `query: string` |
| `db_tables` | List tables | - |
| `db_schema` | Show table schema | `table: string` |
| `db_insert` | Insert data | `table: string, data: object` |

**Supported Databases**:
- SQLite (built-in)
- PostgreSQL
- MySQL

---

## 5. Productivity Servers (P1)

### 5.1 Clipboard Server

**Priority**: P1 - High
**Language**: Python
**Status**: To Develop

| Tool | Description | Parameters |
|------|-------------|------------|
| `copy_text` | Copy text to clipboard | `text: string` |
| `paste_text` | Get clipboard content | - |
| `copy_file` | Copy file to clipboard | `path: string` |
| `paste_file` | Paste file from clipboard | `destination: string` |
| `clear` | Clear clipboard | - |
| `history` | Get clipboard history | `n?: number` |

---

### 5.2 Screenshot Server

**Priority**: P1 - High
**Language**: Python
**Status**: To Develop

| Tool | Description | Parameters |
|------|-------------|------------|
| `capture_screen` | Capture full screen | `output?: string` |
| `capture_window` | Capture specific window | `window?: string, output?: string` |
| `capture_region` | Capture screen region | `x, y, width, height, output?: string` |
| `list_windows` | List available windows | - |

**Implementation Notes**:
- Use scrot or gnome-screenshot
- Support multiple formats (PNG, JPG)

---

### 5.3 Notifications Server

**Priority**: P2 - Medium
**Language**: Python
**Status**: Future

| Tool | Description | Parameters |
|------|-------------|------------|
| `send_notification` | Send desktop notification | `title: string, body: string, icon?: string` |
| `schedule_reminder` | Schedule a reminder | `message: string, time: string` |
| `list_reminders` | List scheduled reminders | - |
| `cancel_reminder` | Cancel a reminder | `id: string` |

---

### 5.4 Calendar Server

**Priority**: P2 - Low
**Language**: Python
**Status**: Future

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_events` | Get calendar events | `date?: string, range?: number` |
| `create_event` | Create calendar event | `title, start, end, ...` |
| `delete_event` | Delete event | `id: string` |
| `today` | Get today's events | - |

**Integration**: GNOME Calendar, Google Calendar API

---

## 6. Media Servers (P2)

### 6.1 Audio Server

**Priority**: P2 - Medium
**Language**: Python
**Status**: Future

| Tool | Description | Parameters |
|------|-------------|------------|
| `play_audio` | Play audio file | `path: string` |
| `pause` | Pause playback | - |
| `resume` | Resume playback | - |
| `stop` | Stop playback | - |
| `set_volume` | Set system volume | `level: number` |
| `get_volume` | Get current volume | - |
| `mute` | Mute audio | - |
| `unmute` | Unmute audio | - |
| `list_devices` | List audio devices | - |

---

### 6.2 Media Info Server

**Priority**: P2 - Low
**Language**: Python
**Status**: Future

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_media_info` | Get media file info | `path: string` |
| `get_duration` | Get media duration | `path: string` |
| `get_thumbnail` | Get video thumbnail | `path: string, time?: number` |
| `convert` | Convert media format | `input: string, output: string` |

---

## 7. Network Servers (P1)

### 7.1 Network Server

**Priority**: P1 - Medium
**Language**: Python
**Status**: To Develop

| Tool | Description | Parameters |
|------|-------------|------------|
| `ping` | Ping a host | `host: string, count?: number` |
| `network_status` | Get network status | - |
| `list_connections` | List active connections | - |
| `get_ip` | Get IP address | `interface?: string` |
| `dns_lookup` | DNS lookup | `domain: string` |
| `traceroute` | Trace route to host | `host: string` |
| `wifi_list` | List WiFi networks | - |
| `wifi_connect` | Connect to WiFi | `ssid: string, password: string` |

---

### 7.2 Download Server

**Priority**: P1 - Medium
**Language**: Python
**Status**: To Develop

| Tool | Description | Parameters |
|------|-------------|------------|
| `download_file` | Download a file | `url: string, destination?: string` |
| `download_status` | Check download progress | `id: string` |
| `cancel_download` | Cancel a download | `id: string` |
| `list_downloads` | List active downloads | - |

---

## 8. Community MCP Servers

These are existing MCP servers from the community that can be integrated:

### 8.1 Official Anthropic Servers

| Server | Description | Source |
|--------|-------------|--------|
| `@modelcontextprotocol/server-filesystem` | File system access | npm |
| `@modelcontextprotocol/server-github` | GitHub integration | npm |
| `@modelcontextprotocol/server-gitlab` | GitLab integration | npm |
| `@modelcontextprotocol/server-google-drive` | Google Drive access | npm |
| `@modelcontextprotocol/server-slack` | Slack integration | npm |
| `@modelcontextprotocol/server-postgres` | PostgreSQL database | npm |
| `@modelcontextprotocol/server-sqlite` | SQLite database | npm |
| `@modelcontextprotocol/server-puppeteer` | Browser automation | npm |
| `@modelcontextprotocol/server-brave-search` | Web search | npm |
| `@modelcontextprotocol/server-fetch` | HTTP requests | npm |
| `@modelcontextprotocol/server-memory` | Persistent memory | npm |

### 8.2 Community Servers

| Server | Description | Source |
|--------|-------------|--------|
| `mcp-server-youtube` | YouTube interactions | Community |
| `mcp-server-spotify` | Spotify control | Community |
| `mcp-server-notion` | Notion integration | Community |
| `mcp-server-todoist` | Todoist integration | Community |
| `mcp-server-discord` | Discord integration | Community |
| `mcp-server-aws` | AWS services | Community |

### 8.3 Integration Priority

| Server | Priority | Notes |
|--------|----------|-------|
| server-filesystem | Skip | Build custom for better control |
| server-puppeteer | P1 | Use for browser automation |
| server-github | P2 | For GitHub integration |
| server-sqlite | P2 | For local database |
| server-brave-search | P2 | For web search |
| server-memory | P2 | For persistent AI memory |

---

## 9. Server Configuration Format

### 9.1 Built-in Server Configuration

```yaml
# /etc/llm-os/mcp-servers/filesystem/config.yaml
name: filesystem
version: 1.0.0
description: File system operations
author: LLM-OS Team

execution:
  command: python3
  args: ["/usr/lib/llm-os/mcp-servers/filesystem/server.py"]
  transport: stdio

security:
  permission_level: write
  requires_confirmation:
    - delete
    - move
  allowed_paths:
    - "${HOME}"
    - "/tmp"

auto_start: true
```

### 9.2 User Custom Server Configuration

```yaml
# ~/.config/llm-os/mcp-servers/my-server/config.yaml
name: my-custom-server
version: 1.0.0
description: My custom tools

execution:
  command: python3
  args: ["./server.py"]
  transport: stdio
  working_directory: "${SERVER_DIR}"

security:
  permission_level: execute
  sandbox: true  # Run in firejail

auto_start: false
```

---

## 10. Creating Custom MCP Servers

### 10.1 Server Template

```python
#!/usr/bin/env python3
"""
Custom MCP Server Template for LLM-OS
"""

import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent

# Server metadata
SERVER_NAME = "my-custom-server"
SERVER_VERSION = "1.0.0"

# Create server instance
server = Server(SERVER_NAME)

# Define your tools
@server.list_tools()
async def list_tools():
    """Return list of available tools"""
    return [
        Tool(
            name="my_tool",
            description="Description of what this tool does",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "First parameter"
                    },
                    "param2": {
                        "type": "number",
                        "description": "Second parameter (optional)"
                    }
                },
                "required": ["param1"]
            }
        ),
        # Add more tools here
    ]

# Implement tools
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    try:
        if name == "my_tool":
            param1 = arguments["param1"]
            param2 = arguments.get("param2", 0)

            # Your implementation here
            result = f"Processed {param1} with value {param2}"

            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

# Main entry point
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

### 10.2 Installation Steps

1. Create server directory:
   ```bash
   mkdir -p ~/.config/llm-os/mcp-servers/my-server
   ```

2. Add server.py with your implementation

3. Create config.yaml:
   ```yaml
   name: my-server
   version: 1.0.0
   description: My custom server
   execution:
     command: python3
     args: ["server.py"]
   auto_start: true
   ```

4. Restart LLM-OS or reload servers:
   ```
   > reload mcp servers
   ✓ Discovered my-server
   ✓ Started my-server
   ```

---

## 11. Server Development Guidelines

### 11.1 Best Practices

1. **Clear Tool Names**: Use verb_noun format (e.g., `read_file`, `list_processes`)
2. **Helpful Descriptions**: Include what, why, and how in descriptions
3. **Proper Schemas**: Define all parameters with types and descriptions
4. **Error Handling**: Return meaningful error messages
5. **Security First**: Validate inputs, check permissions
6. **Idempotency**: Tools should be safe to retry

### 11.2 Schema Best Practices

```json
{
  "name": "example_tool",
  "description": "Performs X action on Y. Use this when you need to Z.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "required_param": {
        "type": "string",
        "description": "What this parameter does and valid values"
      },
      "optional_param": {
        "type": "number",
        "description": "Optional: What this does. Default: 10",
        "default": 10,
        "minimum": 1,
        "maximum": 100
      },
      "enum_param": {
        "type": "string",
        "description": "Choose operation type",
        "enum": ["option1", "option2", "option3"]
      }
    },
    "required": ["required_param"]
  }
}
```

### 11.3 Testing Servers

```python
# test_my_server.py
import pytest
from my_server import call_tool

@pytest.mark.asyncio
async def test_my_tool():
    result = await call_tool("my_tool", {"param1": "test"})
    assert "Processed test" in result[0].text

@pytest.mark.asyncio
async def test_my_tool_error():
    result = await call_tool("my_tool", {})  # Missing required param
    assert "Error" in result[0].text
```

---

## 12. Server Catalog Summary

### By Priority

| Priority | Count | Servers |
|----------|-------|---------|
| **P0** | 4 | filesystem, process, system, applications |
| **P1** | 7 | browser, git, docker, clipboard, screenshot, network, download |
| **P2** | 6+ | python, database, notifications, calendar, audio, media |

### By Status

| Status | Count |
|--------|-------|
| To Develop | 11 |
| Future | 5 |
| Community Integration | 6+ |

### Total Tools (Estimated)

| Category | Tool Count |
|----------|------------|
| Core System | 30 |
| Applications | 15 |
| Development | 35 |
| Productivity | 20 |
| Media | 15 |
| Network | 15 |
| **Total** | **~130 tools** |

---

## References

- [MCP Server Examples](https://github.com/modelcontextprotocol/servers)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [MCP Specification](https://spec.modelcontextprotocol.io/)

---

*Document Version: 1.0*
*Last Updated: January 2026*
