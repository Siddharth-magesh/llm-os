# LLM-OS Overview

## What is LLM-OS?

LLM-OS is a Natural Language Operating System interface that allows users to interact with their Linux computer using plain English commands. Instead of memorizing terminal commands, users can simply describe what they want to do.

## Key Features

### Natural Language Interface
- Type commands in plain English
- Context-aware conversations
- Reference resolution ("open it", "delete that file")

### Multi-Provider LLM Support
- **Ollama** - Local models (llama3.2, deepseek-r1)
- **Anthropic** - Claude models (claude-3.5-haiku, claude-sonnet-4)
- **OpenAI** - GPT models (gpt-4o-mini, gpt-4o)
- Automatic fallback between providers
- Task-based model selection

### MCP-Based Tool System
- File operations (read, write, search, move, copy)
- Application management (launch, close, list apps)
- Process control (run commands, kill processes)
- System information (CPU, memory, disk, network)
- Git operations (status, commit, push, pull)

### Terminal User Interface
- Built with Textual framework
- Chat-style conversation display
- Tool execution progress
- Status bar with system info

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    NL-Shell UI                          │
│              (Textual Terminal Interface)               │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                      LLMOS Core                         │
│            (Orchestration & Integration)                │
└─────────────────────────────────────────────────────────┘
           │                               │
           ▼                               ▼
┌─────────────────────┐     ┌─────────────────────────────┐
│     LLM Router      │     │      MCP Orchestrator       │
│  ┌───────────────┐  │     │  ┌───────────────────────┐  │
│  │    Ollama     │  │     │  │   Filesystem Server   │  │
│  │   Anthropic   │  │     │  │  Applications Server  │  │
│  │    OpenAI     │  │     │  │    Process Server     │  │
│  └───────────────┘  │     │  │    System Server      │  │
└─────────────────────┘     │  │      Git Server       │  │
                            │  └───────────────────────┘  │
                            └─────────────────────────────┘
```

## Example Usage

```
❯ list files in my home directory

I'll list the files in your home directory.

Contents of /home/user:
  Documents/
  Downloads/
  Pictures/
  .config/
  .bashrc
  ...

❯ open firefox

Launching Firefox...
Launched Firefox (PID: 12345)

❯ show system memory

Memory Information:
  Total: 32.0 GB
  Used: 8.5 GB (26.6%)
  Available: 23.5 GB

❯ create a folder called projects and go there

Created directory: /home/user/projects
Changed directory to: /home/user/projects
```

## Design Principles

1. **Local-First** - Prefer local models when available
2. **Security-Conscious** - Confirm dangerous operations
3. **Context-Aware** - Understand conversation history
4. **Extensible** - Easy to add new MCP servers
5. **Resilient** - Fallback chains for reliability
