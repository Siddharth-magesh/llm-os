# LLM-OS: Natural Language Operating System

A production-ready natural language interface for system control and automation, built on the Model Context Protocol (MCP). LLM-OS provides a unified framework for controlling computer systems through conversational AI, integrating multiple LLM providers with extensible tool capabilities.

## Overview

LLM-OS is an operating system abstraction layer that translates natural language commands into system operations. By leveraging the Model Context Protocol, it provides a standardized interface between Large Language Models and system-level tools, enabling users to control their computing environment through conversational interaction.

The system supports both local and cloud-based LLM providers, with a focus on privacy, security, and extensibility. All potentially destructive operations require explicit user confirmation, and the architecture is designed for production deployment.

## Core Capabilities

**Multi-Provider LLM Support**
- Local inference via Ollama (recommended for privacy and cost)
- Cloud APIs: Anthropic Claude, OpenAI GPT
- Provider routing based on task classification
- Streaming response support

**Model Context Protocol Integration**
- 40+ built-in tools across 5 internal Python servers
- External server support via JSON-RPC 2.0 (verified: Memory, Sequential Thinking)
- Extensible architecture for custom tool development
- Server lifecycle management and health monitoring

**Security Architecture**
- Confirmation prompts for file modifications, process termination, and system changes
- Read-only operations execute without interruption
- Sandboxed tool execution
- API key management via environment variables

**Terminal User Interface**
- Built with Textual framework for rich terminal rendering
- Real-time response streaming
- Multi-panel layout with chat history and status information
- Keyboard shortcuts and slash commands for power users

## Technical Architecture

### System Layers

```
┌─────────────────────────────────────────────┐
│          Terminal UI (Textual)              │
├─────────────────────────────────────────────┤
│      Core Orchestration (LLMOS Class)       │
├─────────────────────────────────────────────┤
│   LLM Layer (Provider Routing & Context)    │
├─────────────────────────────────────────────┤
│    MCP Orchestration (Tool Execution)       │
├─────────────────────────────────────────────┤
│  MCP Servers (Internal Python + External)   │
└─────────────────────────────────────────────┘
```

### MCP Server Infrastructure

**Internal Servers (Python)**
- System Server: Hardware info, environment variables, system metrics
- Filesystem Server: Directory operations, file search, content management
- Process Server: Process listing, management, monitoring
- Git Server: Version control operations, commit history, branch management
- Applications Server: Application launching and control

**External Servers (Node.js via stdio)**
- Memory Server: Knowledge graph for entity and relationship management
- Sequential Thinking: Multi-step reasoning with thought revision
- 100+ additional servers available via MCP ecosystem

All external servers communicate via JSON-RPC 2.0 protocol over stdio. The system includes a production-ready client implementation with timeout handling, error recovery, and request correlation.

## Installation

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ (for external MCP servers)
- Ollama (optional, for local LLM inference)

### Setup

```bash
# Clone repository
git clone https://github.com/Siddharth-magesh/llm-os.git
cd llm-os

# Install package
cd llm_os
pip install -e .

# For development
pip install -e ".[dev]"
```

### LLM Provider Configuration

**Local (Ollama - Recommended)**
```bash
# Install Ollama from https://ollama.ai/
# Pull a model with function calling support
ollama pull qwen2.5:7b
```

**Cloud Providers**
```bash
# Anthropic Claude
export ANTHROPIC_API_KEY="your-api-key"

# OpenAI GPT
export OPENAI_API_KEY="your-api-key"
```

### Launch

```bash
# Windows
run-llm-os.bat

# Linux/macOS
llm-os
```

## Usage

### Natural Language Commands

The system interprets natural language requests and executes appropriate system operations:

```
"list all Python files in the current directory"
"show system resource usage"
"display the last 10 git commits"
"find files containing 'TODO' in src/"
"what processes are using the most CPU?"
```

### Interface Controls

**Keyboard Shortcuts**
- `Ctrl+C` / `Ctrl+D` - Exit application
- `Ctrl+L` - Clear conversation history
- `F1` - Display help information
- `F2` - Show system status

**Slash Commands**
- `/help` - Command reference
- `/clear` - Reset conversation
- `/status` - System diagnostics
- `/quit` - Terminate session

## Configuration

System configuration is managed via `llm_os/config/default.yaml`:

```yaml
llm:
  provider: ollama          # ollama, anthropic, openai
  model: qwen2.5:7b         # Provider-specific model identifier

mcp:
  servers:
    internal:               # Python-based servers
      system:
        enabled: true
      filesystem:
        enabled: true
      # ... additional servers

    external:               # Node.js/external servers
      memory:
        enabled: true
        package: "@modelcontextprotocol/server-memory"
      # ... additional servers

security:
  require_confirmation:
    file_operations: true
    process_operations: true
    system_operations: true
```

## Development

### Project Structure

```
llm-os/
├── llm_os/
│   ├── config/             # YAML configuration
│   └── src/llm_os/
│       ├── cli.py          # Command-line entry point
│       ├── core.py         # Core orchestration logic
│       ├── llm/            # LLM provider implementations
│       ├── mcp/            # MCP client and server infrastructure
│       └── ui/             # Textual-based terminal interface
├── tests/
│   └── mcp/                # MCP server tests and documentation
├── docs/                   # Technical documentation
└── README.md
```

### Testing

MCP server infrastructure has been thoroughly tested with comprehensive test suites:

```bash
# Test internal servers
cd tests/mcp
python test_internal_calculator.py

# Test external servers
python mcp_client_simple.py
python test_sequential_thinking.py

# Test combined operation
python test_combined_servers.py
```

See `tests/mcp/START_HERE.md` for detailed testing documentation.

### Adding Custom MCP Servers

**Internal Server (Python)**

Create a new server by inheriting from `BaseMCPServer`:

```python
from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types import ToolParameter, ToolResult, ParameterType

class CustomServer(BaseMCPServer):
    server_id = "custom"
    server_name = "Custom Server"

    def _register_tools(self) -> None:
        self.register_tool(
            name="custom_operation",
            description="Performs custom operation",
            handler=self._handle_operation,
            parameters=[
                ToolParameter(
                    name="input",
                    type=ParameterType.STRING,
                    description="Input parameter",
                    required=True
                )
            ]
        )

    async def _handle_operation(self, input: str) -> ToolResult:
        result = f"Processed: {input}"
        return ToolResult.success_result(text=result)
```

**External Server (Node.js)**

Add to configuration and the system will manage lifecycle automatically:

```yaml
mcp:
  servers:
    external:
      myserver:
        enabled: true
        package: "@scope/package-name"
```

Refer to `tests/mcp/MCP_SERVERS_GUIDE.md` and `tests/mcp/EXTERNAL_SERVERS_GUIDE.md` for complete implementation guides.

## System Requirements

**Minimum**
- Python 3.11+
- 4GB RAM
- Windows 10/11, Linux (kernel 4.x+), or macOS 10.15+

**Recommended**
- Python 3.11+
- 8GB RAM
- Node.js 18+ (for external MCP servers)
- SSD storage
- Ollama with 7B+ parameter model

**Network**
- Not required for local Ollama operation
- Internet connection required for cloud LLM providers
- Outbound HTTPS for external MCP servers (optional)

## Documentation

- **Installation Guide**: `docs/code/02_INSTALLATION.md`
- **Architecture Overview**: `docs/code/03_ARCHITECTURE.md`
- **Development Guide**: `docs/code/09_DEVELOPMENT.md`
- **MCP Server Testing**: `tests/mcp/START_HERE.md`
- **External Servers**: `tests/mcp/EXTERNAL_SERVERS_GUIDE.md`
- **Custom Servers**: `tests/mcp/MCP_SERVERS_GUIDE.md`

## Current Status

**Verified Components**
- Core orchestration and LLM routing: Operational
- Internal MCP servers (5): Fully tested
- External MCP server communication: Verified (Memory, Sequential Thinking)
- JSON-RPC 2.0 client implementation: Production-ready
- Terminal UI with streaming: Operational
- Multi-provider LLM support: Implemented

**Integration Status**
- Phase 1: MCP infrastructure testing - Complete
- Phase 2: External server manager - Planned
- Phase 3: Server ecosystem expansion - Ongoing

## Security Considerations

**API Key Management**
- Never commit API keys to version control
- Use environment variables for sensitive credentials
- Support for .env files (not tracked by git)

**Tool Execution**
- Confirmation required for destructive operations
- Process isolation for external servers
- Input validation on all tool parameters
- Timeout enforcement to prevent hung operations

**Network**
- External servers run as separate processes
- No direct file system access from external servers
- API calls to cloud providers use HTTPS
- Local-first operation mode available (Ollama)

## Contributing

Contributions are welcome. Please ensure:

1. Code follows existing architectural patterns
2. New MCP servers include test coverage
3. Documentation is updated for new features
4. Commit messages are descriptive

See `docs/code/09_DEVELOPMENT.md` for detailed contribution guidelines.

## License

MIT License. See LICENSE file for details.

## References

- **Repository**: https://github.com/Siddharth-magesh/llm-os
- **Model Context Protocol**: https://modelcontextprotocol.io/
- **MCP Server Directory**: https://mcpservers.org/
- **Ollama**: https://ollama.ai/
- **Textual Framework**: https://textual.textualize.io/

---

**Technology Stack**: Python 3.11+, Textual, Ollama, Model Context Protocol, JSON-RPC 2.0, YAML, asyncio
