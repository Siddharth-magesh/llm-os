# MCP Layer Documentation

## Overview

The MCP (Model Context Protocol) layer provides a structured way to expose system capabilities as tools that the LLM can invoke.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Orchestrator                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Server    │  │    Tool     │  │     Security        │  │
│  │   Manager   │  │    Router   │  │     Manager         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       MCP Servers                            │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │Filesystem │ │   Apps    │ │  Process  │ │  System   │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
│  ┌───────────┐                                              │
│  │    Git    │                                              │
│  └───────────┘                                              │
└─────────────────────────────────────────────────────────────┘
```

## MCP Orchestrator

### Usage

```python
from llm_os.mcp import MCPOrchestrator
from llm_os.mcp.orchestrator import OrchestratorConfig

config = OrchestratorConfig(
    auto_start_servers=True,
    health_check_interval=30.0,
)

orchestrator = MCPOrchestrator(config=config)
orchestrator.register_builtin_servers()
await orchestrator.initialize()

# Get all tools
tools = orchestrator.get_tools_for_llm()

# Execute a tool
result = await orchestrator.call_tool("read_file", path="/etc/hostname")
print(result.get_text())
```

### Components

#### Server Manager

Manages server lifecycle:
- Registration and discovery
- Initialization and shutdown
- Health monitoring
- Auto-restart on failure

```python
from llm_os.mcp.orchestrator import ServerManager

manager = ServerManager(
    health_check_interval=30.0,
    auto_restart=True,
)

manager.register_server(FilesystemServer())
await manager.initialize_all()

# Check status
status = manager.get_status_summary()
```

#### Tool Router

Routes tool calls to appropriate servers:

```python
from llm_os.mcp.orchestrator import ToolRouter

router = ToolRouter(server_manager=manager)

# Execute single tool
result = await router.execute_by_name("list_directory", path="~")

# Execute multiple tools in parallel
results = await router.execute_tool_calls(tool_calls, parallel=True)
```

#### Security Manager

Enforces security policies:

```python
from llm_os.mcp.orchestrator import SecurityManager, SecurityPolicy

policy = SecurityPolicy(
    require_confirmation_for_write=True,
    sandbox_enabled=True,
    blocked_paths=["/etc/shadow", "/root"],
)

security = SecurityManager(policy=policy)

# Check permission
result = security.check_tool_permission(tool, arguments)
if result.action == SecurityAction.DENY:
    print(f"Denied: {result.reason}")
```

## MCP Servers

### Base Server

All servers extend `BaseMCPServer`:

```python
from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types.tools import ToolResult

class MyServer(BaseMCPServer):
    server_id = "my_server"
    server_name = "My Custom Server"

    def __init__(self):
        super().__init__()
        self._register_tools()

    def _register_tools(self):
        self.register_tool(
            name="my_tool",
            description="Does something useful",
            handler=self._my_tool,
            parameters=[
                self.string_param("input", "The input string"),
                self.boolean_param("flag", "Optional flag", required=False),
            ],
            permission_level="read",
        )

    async def _my_tool(self, input: str, flag: bool = False) -> ToolResult:
        result = process(input, flag)
        return ToolResult.success_result(result)
```

### Filesystem Server

File and directory operations.

**Tools:**

| Tool | Description | Permission |
|------|-------------|------------|
| `read_file` | Read file contents | read |
| `write_file` | Write to file | write |
| `list_directory` | List directory contents | read |
| `file_info` | Get file metadata | read |
| `search_files` | Search by pattern | read |
| `search_content` | Search file contents | read |
| `create_directory` | Create directory | write |
| `delete` | Delete file/directory | write |
| `copy` | Copy file/directory | write |
| `move` | Move/rename | write |
| `exists` | Check if path exists | read |

**Examples:**

```python
# Read file
result = await orchestrator.call_tool("read_file", path="~/config.yaml")

# List directory
result = await orchestrator.call_tool("list_directory",
    path="~",
    show_hidden=True,
    detailed=True
)

# Search files
result = await orchestrator.call_tool("search_files",
    pattern="**/*.py",
    path="~/projects"
)
```

### Applications Server

Application management.

**Tools:**

| Tool | Description | Permission |
|------|-------------|------------|
| `launch_app` | Launch application | execute |
| `close_app` | Close application | execute |
| `list_apps` | List installed apps | read |
| `app_installed` | Check if installed | read |
| `app_info` | Get app information | read |
| `running_apps` | List running apps | read |
| `open_with_default` | Open file with default app | execute |
| `open_url` | Open URL in browser | execute |

**Examples:**

```python
# Launch app
result = await orchestrator.call_tool("launch_app", name="firefox")

# List apps by category
result = await orchestrator.call_tool("list_apps", category="browser")

# Open URL
result = await orchestrator.call_tool("open_url",
    url="https://google.com",
    browser="firefox"
)
```

### Process Server

Process and shell operations.

**Tools:**

| Tool | Description | Permission |
|------|-------------|------------|
| `run_command` | Execute shell command | execute |
| `run_background` | Run command in background | execute |
| `check_background` | Check background process | read |
| `list_processes` | List running processes | read |
| `process_info` | Get process details | read |
| `kill_process` | Terminate process | system |
| `get_env` | Get environment variable | read |
| `set_env` | Set environment variable | write |
| `list_env` | List environment variables | read |
| `which` | Find command location | read |

**Examples:**

```python
# Run command
result = await orchestrator.call_tool("run_command",
    command="ls -la",
    timeout=30.0
)

# List processes
result = await orchestrator.call_tool("list_processes",
    filter="python",
    sort_by="cpu"
)

# Run in background
result = await orchestrator.call_tool("run_background",
    command="python server.py",
    name="my_server"
)
```

### System Server

System information and control.

**Tools:**

| Tool | Description | Permission |
|------|-------------|------------|
| `system_info` | Comprehensive system info | read |
| `cpu_info` | CPU details and usage | read |
| `memory_info` | Memory usage | read |
| `disk_info` | Disk space | read |
| `network_info` | Network interfaces | read |
| `get_datetime` | Current date/time | read |
| `uptime` | System uptime | read |
| `user_info` | Current user info | read |
| `logged_users` | Logged in users | read |
| `set_volume` | Set audio volume | write |
| `get_volume` | Get audio volume | read |
| `set_brightness` | Set display brightness | write |
| `battery_info` | Battery status | read |
| `power_control` | Shutdown/reboot/suspend | dangerous |
| `list_packages` | List installed packages | read |
| `system_logs` | View system logs | read |

**Examples:**

```python
# System info
result = await orchestrator.call_tool("system_info")

# Memory usage
result = await orchestrator.call_tool("memory_info")

# Set volume
result = await orchestrator.call_tool("set_volume", level=50)
```

### Git Server

Git version control operations.

**Tools:**

| Tool | Description | Permission |
|------|-------------|------------|
| `git_status` | Repository status | read |
| `git_log` | Commit history | read |
| `git_diff` | Show changes | read |
| `git_add` | Stage files | write |
| `git_commit` | Commit changes | write |
| `git_branch` | Branch operations | write |
| `git_checkout` | Switch branch/file | write |
| `git_pull` | Pull from remote | write |
| `git_push` | Push to remote | write |
| `git_stash` | Stash changes | write |
| `git_reset` | Reset HEAD | write |
| `git_clone` | Clone repository | write |
| `git_remote` | Manage remotes | write |
| `git_init` | Initialize repository | write |

**Examples:**

```python
# Git status
result = await orchestrator.call_tool("git_status", path="~/project")

# Commit
result = await orchestrator.call_tool("git_commit",
    message="Add new feature",
    all=True
)

# Push
result = await orchestrator.call_tool("git_push",
    remote="origin",
    branch="main"
)
```

## Security Model

### Permission Levels

```python
class PermissionLevel(str, Enum):
    READ = "read"        # No confirmation needed
    WRITE = "write"      # Optional confirmation
    EXECUTE = "execute"  # Confirmation by default
    SYSTEM = "system"    # Always requires confirmation
    DANGEROUS = "dangerous"  # Always requires confirmation + admin
```

### Path Sandboxing

```python
policy = SecurityPolicy(
    sandbox_enabled=True,
    sandbox_allowed_paths=[
        str(Path.home()),
        "/tmp",
    ],
    sandbox_blocked_paths=[
        "/etc/passwd",
        "/etc/shadow",
        "/root",
        "/boot",
    ],
)
```

### Blocked Commands

```python
BLOCKED_COMMANDS = {
    "rm -rf /",
    "dd if=/dev/zero",
    "mkfs.",
    ":(){ :|:& };:",  # Fork bomb
    "chmod -R 777 /",
}
```

## Creating Custom Servers

```python
from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types.tools import ToolResult

class WeatherServer(BaseMCPServer):
    server_id = "weather"
    server_name = "Weather Server"
    server_description = "Get weather information"

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self._register_tools()

    def _register_tools(self):
        self.register_tool(
            name="get_weather",
            description="Get current weather for a location",
            handler=self._get_weather,
            parameters=[
                self.string_param("location", "City name or coordinates"),
                self.string_param("units", "Temperature units",
                    required=False, enum=["celsius", "fahrenheit"]),
            ],
            permission_level="read",
        )

    async def _get_weather(
        self,
        location: str,
        units: str = "celsius"
    ) -> ToolResult:
        # Fetch weather from API
        weather = await self._fetch_weather(location, units)
        return ToolResult.success_result(
            f"Weather in {location}: {weather['temp']}°, {weather['condition']}",
            **weather
        )

# Register with orchestrator
orchestrator.register_server(WeatherServer(api_key="..."))
```
