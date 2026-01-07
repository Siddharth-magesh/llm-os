# LLM-OS: Natural Language Operating System

Control your computer entirely through natural language. LLM-OS integrates Large Language Models with system-level capabilities using the Model Context Protocol (MCP).

## ✨ Features

- **Natural Language Interface** - Control your system using plain English
- **Multiple LLM Providers** - Ollama (local), Anthropic Claude, OpenAI GPT
- **MCP Architecture** - 61 built-in tools via Model Context Protocol
- **Security-First** - Confirmation prompts for destructive operations
- **Beautiful TUI** - Textual-based interface with streaming responses
- **Local-First** - Run with local Ollama models, no API costs required

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- [Ollama](https://ollama.ai/) (for local LLM) - recommended

### Installation

```bash
# Clone repository
git clone https://github.com/Siddharth-magesh/llm-os.git
cd llm-os/llm_os

# Install package
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Setup Local LLM (Ollama)

```bash
# Install Ollama from https://ollama.ai/

# Pull a model with tool calling support
ollama pull qwen2.5:7b
```

### Run

```bash
# On Windows
run-llm-os.bat

# On Linux/Mac
llm-os
```

## 🎯 Usage

### Example Commands

```
"list files in the current directory"
"show system information"
"what's the git status?"
"find all python files"
"show me the last 5 commits"
```

### Keyboard Shortcuts

- `Ctrl+C` / `Ctrl+D` - Quit
- `Ctrl+L` - Clear chat
- `F1` - Help
- `F2` - Status

### Slash Commands

- `/help` - Show help
- `/clear` - Clear conversation
- `/status` - Show system status
- `/quit` - Exit

## 📁 Project Structure

```
llm-os/
├── llm_os/              # Main Python package
│   ├── config/          # Configuration files
│   └── src/llm_os/      # Source code
│       ├── cli.py       # Command-line interface
│       ├── core.py      # Core orchestration
│       ├── llm/         # LLM providers and routing
│       ├── mcp/         # MCP servers and orchestration
│       └── ui/          # Terminal UI (Textual)
├── docs/                # Documentation
│   ├── code/            # Code documentation
│   └── planning/        # Architecture & design
├── README.md            # This file
└── run-llm-os.bat       # Windows launcher
```

## 📚 Documentation

- **Code Documentation**: [docs/code/](docs/code/) - Architecture, API, development
- **Planning Docs**: [docs/planning/](docs/planning/) - Design, tech stack, MCP architecture
- **Installation Guide**: [docs/code/02_INSTALLATION.md](docs/code/02_INSTALLATION.md)
- **Architecture**: [docs/code/03_ARCHITECTURE.md](docs/code/03_ARCHITECTURE.md)

## 🏗️ Architecture

LLM-OS uses a layered architecture:

1. **UI Layer** - Textual-based terminal interface
2. **Core Orchestration** - LLMOS class coordinating components
3. **LLM Layer** - Provider routing, task classification, context management
4. **MCP Orchestration** - Tool execution, security, server management
5. **MCP Servers** - 61 tools across 5 internal Python servers

See [docs/code/03_ARCHITECTURE.md](docs/code/03_ARCHITECTURE.md) for details.

## ⚙️ Configuration

Configure in `llm_os/config/default.yaml`:

- Default LLM provider and model
- MCP servers to auto-start
- Security settings
- UI preferences

## 🧪 Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run in development mode
python -m llm_os

# Format code
black llm_os/
```

See [docs/code/09_DEVELOPMENT.md](docs/code/09_DEVELOPMENT.md) for the development guide.

## 📋 System Requirements

- **Python**: 3.11+
- **OS**: Linux (recommended), Windows (development/testing), macOS
- **Optional**: Ollama for local LLM
- **Optional**: Anthropic/OpenAI API keys for cloud LLMs

## 🤝 Contributing

Contributions are welcome! See [docs/code/09_DEVELOPMENT.md](docs/code/09_DEVELOPMENT.md) for guidelines.

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🔗 Links

- **Repository**: https://github.com/Siddharth-magesh/llm-os
- **Ollama**: https://ollama.ai/
- **Model Context Protocol**: https://modelcontextprotocol.io/

---

**Built with**: Python, Textual, Ollama, Model Context Protocol (MCP)
