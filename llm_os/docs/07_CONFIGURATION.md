# Configuration Guide

## Configuration Files

LLM-OS looks for configuration in these locations (in order):

1. `/etc/llm-os/config.yaml` - System-wide
2. `~/.config/llm-os/config.yaml` - User config (XDG)
3. `~/.llm-os/config.yaml` - User config (simple)
4. `./config.yaml` - Local directory

## Environment Variables

Environment variables override config file settings:

```bash
# API Keys
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."

# Ollama settings
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.2:3b"

# LLM-OS settings
export LLM_OS_PROVIDER="ollama"  # Default provider
```

## Full Configuration Reference

```yaml
# ~/.llm-os/config.yaml

# ============================================
# LLM Provider Settings
# ============================================

# Default provider to use
default_provider: ollama  # ollama, anthropic, openai

# Prefer local models when available
local_first: true

# Route simple tasks to cheaper/faster models
cost_optimization: true

# Ollama (Local Models)
ollama:
  enabled: true
  base_url: http://localhost:11434
  default_model: llama3.2:3b
  timeout: 120.0
  models:
    fast: llama3.2:1b
    default: llama3.2:3b
    best: llama3.2:3b
    reasoning: deepseek-r1:1.5b

# Anthropic (Claude)
anthropic:
  enabled: true
  api_key: ${ANTHROPIC_API_KEY}  # From environment
  default_model: claude-3-5-haiku-latest
  timeout: 60.0
  models:
    fast: claude-3-5-haiku-latest
    default: claude-3-5-haiku-latest
    best: claude-sonnet-4-20250514
    reasoning: claude-sonnet-4-20250514

# OpenAI (GPT)
openai:
  enabled: true
  api_key: ${OPENAI_API_KEY}
  default_model: gpt-4o-mini
  timeout: 60.0
  models:
    fast: gpt-4o-mini
    default: gpt-4o-mini
    best: gpt-4o
    reasoning: o1-mini

# ============================================
# MCP Server Settings
# ============================================

mcp:
  # Auto-start servers on initialization
  auto_start: true

  # Health check interval (seconds)
  health_check_interval: 30.0

  # Auto-restart failed servers
  auto_restart: true

  # Maximum restart attempts
  max_restart_attempts: 3

  # Enabled servers
  enabled_servers:
    - filesystem
    - applications
    - process
    - system
    - git

# ============================================
# Security Settings
# ============================================

security:
  # Confirmation requirements by permission level
  require_confirmation_write: true
  require_confirmation_execute: true
  require_confirmation_system: true
  require_confirmation_dangerous: true

  # Path sandboxing
  sandbox_enabled: true

  # Allowed paths (if empty, allows home directory)
  allowed_paths:
    - ~/
    - /tmp

  # Blocked paths (always blocked)
  blocked_paths:
    - /etc/passwd
    - /etc/shadow
    - /etc/sudoers
    - /root
    - /boot
    - /sys
    - /proc/kcore

  # Blocked command patterns
  blocked_commands:
    - "rm -rf /"
    - "dd if=/dev/zero"
    - "mkfs."
    - ":(){:|:&};:"

  # Blocked file extensions
  blocked_extensions:
    - .exe
    - .dll
    - .bat

  # Rate limiting
  max_operations_per_minute: 60
  max_file_operations_per_minute: 30

# ============================================
# UI Settings
# ============================================

ui:
  # Color theme
  theme: default  # default, dark, light

  # Show timestamps on messages
  show_timestamps: true

  # Show tool calls in output
  show_tool_calls: true

  # Stream responses as they arrive
  stream_responses: true

  # History size (number of messages)
  history_size: 1000

# ============================================
# Path Settings
# ============================================

# Data directory
data_dir: ~/.llm-os

# Log directory
log_dir: ~/.llm-os/logs
```

## Configuration Classes

### Loading Configuration

```python
from llm_os.config import load_config, get_config, save_config

# Load from default locations
config = load_config()

# Load from specific file
config = load_config("/path/to/config.yaml")

# Get global singleton
config = get_config()

# Save configuration
save_config(config, "~/.llm-os/config.yaml")
```

### Config Class

```python
from llm_os.config import Config

config = Config()

# Access provider configs
print(config.ollama.base_url)
print(config.anthropic.default_model)

# Access security settings
print(config.security.sandbox_enabled)

# Access UI settings
print(config.ui.stream_responses)

# Convert to dict
data = config.to_dict()

# Create from dict
config = Config.from_dict(data)
```

### Provider Configs

```python
from llm_os.config import OllamaConfig, AnthropicConfig, OpenAIConfig

# Ollama config
ollama = OllamaConfig(
    enabled=True,
    base_url="http://localhost:11434",
    default_model="llama3.2:3b",
    models={
        "fast": "llama3.2:1b",
        "default": "llama3.2:3b",
    }
)

# Anthropic config
anthropic = AnthropicConfig(
    enabled=True,
    api_key="sk-ant-...",
    default_model="claude-3-5-haiku-latest",
)
```

## CLI Configuration Options

```bash
# Use specific provider
llm-os --provider anthropic

# Use specific model
llm-os --model llama3.2:1b

# Local models only
llm-os --local-only

# Use specific config file
llm-os --config /path/to/config.yaml

# Disable streaming
llm-os --no-stream

# Verbose logging
llm-os -v      # INFO level
llm-os -vv     # DEBUG level

# Log to file
llm-os --log-file ~/.llm-os/logs/session.log
```

## Configuration Precedence

1. CLI arguments (highest)
2. Environment variables
3. User config file
4. System config file
5. Default values (lowest)

## Example Configurations

### Minimal Local-Only

```yaml
default_provider: ollama
local_first: true

ollama:
  enabled: true
  default_model: llama3.2:3b

anthropic:
  enabled: false

openai:
  enabled: false
```

### Cloud-Primary with Local Fallback

```yaml
default_provider: anthropic
local_first: false

anthropic:
  enabled: true
  api_key: ${ANTHROPIC_API_KEY}

ollama:
  enabled: true  # Fallback

openai:
  enabled: false
```

### High Security

```yaml
security:
  require_confirmation_write: true
  require_confirmation_execute: true
  require_confirmation_system: true
  require_confirmation_dangerous: true
  sandbox_enabled: true
  allowed_paths:
    - ~/Documents
    - ~/Projects
  max_operations_per_minute: 30
```

### Development Mode

```yaml
# Less restrictions for development
security:
  require_confirmation_write: false
  require_confirmation_execute: false
  sandbox_enabled: false

ui:
  show_tool_calls: true
  stream_responses: true
```
