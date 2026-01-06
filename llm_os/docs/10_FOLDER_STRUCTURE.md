# Complete Folder Structure

## Project Root

```
llm_os/
├── pyproject.toml              # Project configuration and dependencies
├── requirements.txt            # Core dependencies list
├── requirements-dev.txt        # Development dependencies
├── README.md                   # Project readme
├── LICENSE                     # License file
│
├── config/                     # Configuration templates
│   └── default.yaml           # Default configuration file
│
├── docs/                       # Documentation
│   ├── README.md              # Documentation index
│   ├── 01_OVERVIEW.md         # Project overview
│   ├── 02_INSTALLATION.md     # Installation guide
│   ├── 03_ARCHITECTURE.md     # System architecture
│   ├── 04_LLM_LAYER.md        # LLM layer documentation
│   ├── 05_MCP_LAYER.md        # MCP layer documentation
│   ├── 06_UI_LAYER.md         # UI layer documentation
│   ├── 07_CONFIGURATION.md    # Configuration guide
│   ├── 08_API_REFERENCE.md    # API documentation
│   ├── 09_DEVELOPMENT.md      # Development guide
│   └── 10_FOLDER_STRUCTURE.md # This file
│
├── tests/                      # Test files (to be created)
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   ├── test_llm/
│   ├── test_mcp/
│   └── test_ui/
│
└── src/                        # Source code
    └── llm_os/                 # Main package
        ├── __init__.py         # Package initialization
        ├── __main__.py         # Module entry point (python -m llm_os)
        ├── cli.py              # Command-line interface
        ├── config.py           # Configuration management
        ├── core.py             # Main LLMOS orchestration class
        │
        ├── llm/                # LLM Layer
        │   ├── __init__.py
        │   ├── base.py         # Base types and protocols
        │   ├── classifier.py   # Task classification
        │   ├── context.py      # Context management
        │   ├── router.py       # LLM provider routing
        │   │
        │   └── providers/      # LLM Providers
        │       ├── __init__.py
        │       ├── ollama.py   # Ollama (local models)
        │       ├── anthropic.py # Claude API
        │       └── openai.py   # OpenAI/Groq/Together
        │
        ├── mcp/                # MCP Layer
        │   ├── __init__.py
        │   │
        │   ├── types/          # Type definitions
        │   │   ├── __init__.py
        │   │   ├── tools.py    # Tool, ToolResult, ToolParameter
        │   │   └── server.py   # ServerConfig, ServerStatus
        │   │
        │   ├── orchestrator/   # Orchestration components
        │   │   ├── __init__.py
        │   │   ├── orchestrator.py    # Main MCPOrchestrator
        │   │   ├── server_manager.py  # Server lifecycle management
        │   │   ├── tool_router.py     # Tool call routing
        │   │   └── security.py        # Security and permissions
        │   │
        │   └── servers/        # MCP Servers
        │       ├── __init__.py
        │       ├── base.py           # BaseMCPServer abstract class
        │       ├── filesystem.py     # File operations
        │       ├── applications.py   # Application management
        │       ├── process.py        # Shell/process control
        │       ├── system.py         # System information
        │       └── git.py            # Git operations
        │
        └── ui/                 # UI Layer
            ├── __init__.py
            ├── app.py          # Main NLShellApp (Textual)
            └── widgets.py      # Custom UI widgets
```

## File Descriptions

### Root Files

| File | Description |
|------|-------------|
| `pyproject.toml` | Modern Python project configuration with dependencies, build settings, tool configs |
| `requirements.txt` | Pip-compatible dependencies list |
| `requirements-dev.txt` | Development-only dependencies |

### Source Code (`src/llm_os/`)

#### Core Files

| File | Description | Key Classes/Functions |
|------|-------------|----------------------|
| `__init__.py` | Package init, exports | `LLMOS`, `Config`, `__version__` |
| `__main__.py` | Module entry point | Enables `python -m llm_os` |
| `cli.py` | CLI implementation | `main()`, argument parsing |
| `config.py` | Configuration management | `Config`, `load_config()`, `get_config()` |
| `core.py` | Main orchestration | `LLMOS`, `LLMOSConfig`, `create_llmos()` |

#### LLM Layer (`llm/`)

| File | Description | Key Classes |
|------|-------------|-------------|
| `base.py` | Base types and protocols | `Message`, `LLMResponse`, `BaseLLMProvider`, `ToolCall` |
| `classifier.py` | Task classification | `TaskClassifier`, `TaskType`, `ClassificationResult` |
| `context.py` | Conversation context | `ContextManager`, `ContextReference`, `ContextState` |
| `router.py` | Provider routing | `LLMRouter`, `RouterConfig`, `UsageStats` |
| `providers/ollama.py` | Ollama provider | `OllamaProvider` |
| `providers/anthropic.py` | Claude provider | `AnthropicProvider` |
| `providers/openai.py` | OpenAI provider | `OpenAIProvider`, `GroqProvider`, `TogetherProvider` |

#### MCP Layer (`mcp/`)

| File | Description | Key Classes |
|------|-------------|-------------|
| `types/tools.py` | Tool types | `Tool`, `ToolResult`, `ToolParameter`, `ToolCall`, `ToolContent` |
| `types/server.py` | Server types | `ServerConfig`, `ServerStatus`, `ServerState`, `PermissionLevel` |
| `orchestrator/orchestrator.py` | Main orchestrator | `MCPOrchestrator`, `OrchestratorConfig` |
| `orchestrator/server_manager.py` | Server lifecycle | `ServerManager`, `ServerRegistry`, `ManagedServer` |
| `orchestrator/tool_router.py` | Tool routing | `ToolRouter`, `ToolDispatcher`, `RouterConfig` |
| `orchestrator/security.py` | Security | `SecurityManager`, `SecurityPolicy`, `PathSandbox` |
| `servers/base.py` | Base server class | `BaseMCPServer`, `RegisteredTool` |
| `servers/filesystem.py` | File operations | `FilesystemServer` (15 tools) |
| `servers/applications.py` | App management | `ApplicationsServer` (8 tools) |
| `servers/process.py` | Process control | `ProcessServer` (10 tools) |
| `servers/system.py` | System info | `SystemServer` (16 tools) |
| `servers/git.py` | Git operations | `GitServer` (14 tools) |

#### UI Layer (`ui/`)

| File | Description | Key Classes |
|------|-------------|-------------|
| `app.py` | Main application | `NLShellApp`, `MainScreen`, `run_app()` |
| `widgets.py` | Custom widgets | `MessageDisplay`, `InputPrompt`, `StatusBar`, `ToolProgress`, `ChatMessage`, etc. |

## Tool Count Summary

| Server | Tools |
|--------|-------|
| Filesystem | 15 |
| Applications | 8 |
| Process | 10 |
| System | 16 |
| Git | 14 |
| **Total** | **63** |

## Lines of Code (Approximate)

| Component | Lines |
|-----------|-------|
| LLM Layer | ~1,500 |
| MCP Layer | ~3,500 |
| UI Layer | ~800 |
| Core/Config/CLI | ~700 |
| **Total** | **~6,500** |

## Import Hierarchy

```
llm_os
├── config (standalone)
├── core (depends on: config, llm, mcp)
├── cli (depends on: config, core, ui)
│
├── llm
│   ├── base (standalone)
│   ├── classifier (standalone)
│   ├── context (depends on: base)
│   ├── router (depends on: base, classifier, providers/*)
│   └── providers/* (depends on: base)
│
├── mcp
│   ├── types/* (standalone)
│   ├── servers/base (depends on: types)
│   ├── servers/* (depends on: base, types)
│   └── orchestrator/* (depends on: servers, types)
│
└── ui
    ├── widgets (standalone - Textual widgets)
    └── app (depends on: widgets)
```

## Entry Points

```bash
# CLI entry points (from pyproject.toml)
llm-os   → llm_os.cli:main
llmos    → llm_os.cli:main

# Module execution
python -m llm_os → llm_os.__main__

# Python import
from llm_os import LLMOS, Config
```
