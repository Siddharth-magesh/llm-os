# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                         │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                      NLShellApp (Textual)                       │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │ │
│  │  │MessageDisplay│ │ InputPrompt  │ │      StatusBar           │ │ │
│  │  └──────────────┘ └──────────────┘ └──────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Core Layer (LLMOS)                          │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                         LLMOS Class                              │ │
│  │  - process_message()    - Initialize components                 │ │
│  │  - stream_message()     - Coordinate LLM and MCP                │ │
│  │  - Tool execution       - Context management                    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
              │                                      │
              ▼                                      ▼
┌─────────────────────────────┐    ┌─────────────────────────────────┐
│       LLM Layer             │    │          MCP Layer              │
│  ┌───────────────────────┐  │    │  ┌───────────────────────────┐  │
│  │      LLM Router       │  │    │  │    MCP Orchestrator       │  │
│  │  - Provider selection │  │    │  │  - Server management      │  │
│  │  - Fallback chains    │  │    │  │  - Tool routing           │  │
│  │  - Task classification│  │    │  │  - Security enforcement   │  │
│  └───────────────────────┘  │    │  └───────────────────────────┘  │
│           │                 │    │              │                  │
│           ▼                 │    │              ▼                  │
│  ┌───────────────────────┐  │    │  ┌───────────────────────────┐  │
│  │     Providers         │  │    │  │      MCP Servers          │  │
│  │  ┌─────────────────┐  │  │    │  │  ┌─────────────────────┐  │  │
│  │  │ OllamaProvider  │  │  │    │  │  │ FilesystemServer    │  │  │
│  │  │ AnthropicProvider│ │  │    │  │  │ ApplicationsServer  │  │  │
│  │  │ OpenAIProvider  │  │  │    │  │  │ ProcessServer       │  │  │
│  │  └─────────────────┘  │  │    │  │  │ SystemServer        │  │  │
│  └───────────────────────┘  │    │  │  │ GitServer           │  │  │
│           │                 │    │  │  └─────────────────────┘  │  │
│           ▼                 │    │  └───────────────────────────┘  │
│  ┌───────────────────────┐  │    └─────────────────────────────────┘
│  │   Context Manager     │  │
│  │  - Message history    │  │
│  │  - Reference resolve  │  │
│  │  - Token management   │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

## Component Descriptions

### 1. User Interface Layer

**NLShellApp** (`ui/app.py`)
- Main Textual application
- Handles user input and display
- Manages keyboard shortcuts
- Coordinates with core layer

**Widgets** (`ui/widgets.py`)
- `MessageDisplay` - Scrollable chat history
- `InputPrompt` - User input field
- `StatusBar` - Provider/model status
- `ToolProgress` - Tool execution indicator
- `ChatMessage` - Individual message rendering

### 2. Core Layer

**LLMOS** (`core.py`)
- Main orchestration class
- Integrates LLM and MCP layers
- Processes user messages
- Handles tool execution loops
- Manages conversation context

**Config** (`config.py`)
- Configuration loading/saving
- Environment variable handling
- Provider settings
- Security settings

### 3. LLM Layer

**LLMRouter** (`llm/router.py`)
- Routes requests to providers
- Implements fallback chains
- Task-based model selection
- Usage tracking

**Providers** (`llm/providers/`)
- `OllamaProvider` - Local Ollama models
- `AnthropicProvider` - Claude API
- `OpenAIProvider` - OpenAI API

**TaskClassifier** (`llm/classifier.py`)
- Classifies user requests
- Determines complexity level
- Routes to appropriate model tier

**ContextManager** (`llm/context.py`)
- Manages conversation history
- Token counting and trimming
- Reference resolution ("it", "that")
- Persistence support

### 4. MCP Layer

**MCPOrchestrator** (`mcp/orchestrator/orchestrator.py`)
- Coordinates all MCP servers
- Provides unified tool interface
- Handles initialization/shutdown

**ServerManager** (`mcp/orchestrator/server_manager.py`)
- Server lifecycle management
- Health monitoring
- Auto-restart on failure

**ToolRouter** (`mcp/orchestrator/tool_router.py`)
- Routes tool calls to servers
- Parallel execution support
- Result caching

**SecurityManager** (`mcp/orchestrator/security.py`)
- Permission checking
- Path sandboxing
- Command filtering
- Confirmation handling

### 5. MCP Servers

**BaseMCPServer** (`mcp/servers/base.py`)
- Abstract base class
- Tool registration helpers
- Common functionality

**FilesystemServer** (`mcp/servers/filesystem.py`)
- read_file, write_file
- list_directory, search_files
- copy, move, delete

**ApplicationsServer** (`mcp/servers/applications.py`)
- launch_app, close_app
- list_apps, app_info
- open_url, open_with_default

**ProcessServer** (`mcp/servers/process.py`)
- run_command
- list_processes, kill_process
- Environment management

**SystemServer** (`mcp/servers/system.py`)
- system_info, cpu_info, memory_info
- disk_info, network_info
- Volume/brightness control

**GitServer** (`mcp/servers/git.py`)
- git_status, git_log, git_diff
- git_add, git_commit
- git_push, git_pull

## Data Flow

### User Message Processing

```
1. User types message in InputPrompt
2. NLShellApp receives submission
3. LLMOS.process_message() called
4. ContextManager adds user message
5. TaskClassifier classifies request
6. LLMRouter selects provider/model
7. LLM generates response (may include tool calls)
8. If tool calls present:
   a. ToolRouter finds appropriate server
   b. SecurityManager checks permissions
   c. Server executes tool
   d. Result added to context
   e. LLM generates follow-up
9. Final response returned to UI
10. MessageDisplay shows response
```

### Tool Execution Flow

```
1. LLM returns tool_calls in response
2. LLMOS iterates over tool calls
3. For each tool:
   a. MCPOrchestrator.execute_tool()
   b. ToolRouter finds server
   c. SecurityManager checks:
      - Permission level
      - Path sandboxing
      - Blocked commands
   d. If confirmation needed:
      - UI shows confirmation dialog
      - User approves/denies
   e. Server.call_tool() executes
   f. Result returned
4. All results added to context
5. LLM summarizes results for user
```

## Security Model

```
Permission Levels:
├── read      - Read-only operations (no confirmation)
├── write     - File modifications (confirmation optional)
├── execute   - Run commands (confirmation by default)
├── system    - System operations (confirmation required)
└── dangerous - Destructive operations (always confirm)

Sandboxing:
├── Allowed paths (configurable)
├── Blocked paths (/etc/shadow, /boot, etc.)
└── Blocked commands (rm -rf /, dd, etc.)
```
