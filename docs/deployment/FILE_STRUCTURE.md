# LLM-OS File Structure and Deployment Guide

## Overview

This document outlines the proper file structure and deployment strategy for LLM-OS. The system is designed with a clear separation between:

1. **Core System** - The LLM-OS installation (read-only, system-level)
2. **User Workspace** - Where user commands execute (read-write, user-level)
3. **User Data** - Configuration, history, and user-specific data

## Directory Structure Philosophy

### Current Development Structure
```
/home/siddharth/llm-os/          # Development directory
├── src/llm_os/                   # Core LLM-OS code
├── config/                       # Configuration system
├── tests/                        # Test suite
├── docs/                         # Documentation
├── launch.sh                     # Launcher script
└── pyproject.toml                # Package definition
```

### Production Deployment Structure

For production deployment on Linux systems, LLM-OS should follow the Linux Filesystem Hierarchy Standard (FHS):

```
# System-level Installation (Protected)
/opt/llm-os/                      # Core system installation
├── lib/                          # Core Python packages
│   └── llm_os/                   # Main package
│       ├── __init__.py
│       ├── core.py               # System orchestration
│       ├── cli.py                # CLI interface
│       ├── llm/                  # LLM providers
│       ├── mcp/                  # MCP servers & tools
│       └── ui/                   # UI components
├── config/                       # System configuration
│   ├── __init__.py
│   ├── providers/                # LLM provider configs
│   └── defaults.yaml             # Default settings
├── bin/                          # Executable scripts
│   └── llm-os                    # Main launcher
└── share/                        # Shared resources
    ├── docs/                     # Documentation
    └── examples/                 # Example configs

# User-level Data (Per User)
/home/{username}/.llm-os/         # User configuration directory
├── config.yaml                   # User settings override
├── history.json                  # Command history
├── logs/                         # User-specific logs
│   ├── llm-os.log
│   └── mcp-servers.log
└── cache/                        # Cache directory
    └── context/                  # Context cache

# User Workspace (Command Execution)
/home/{username}/                 # User's home directory
└── [user files and folders]      # User commands execute here
```

## Security and Permission Model

### Core System Protection

The core LLM-OS installation should be:
- **Read-only** for regular users
- **Owned by root** (or system administrator)
- **Protected from modification** by user processes

```bash
# Installation permissions
/opt/llm-os/                      # root:root, 755
├── lib/                          # root:root, 755
├── config/                       # root:root, 755
└── bin/                          # root:root, 755
    └── llm-os                    # root:root, 755 (executable)
```

### User Data Protection

User-specific data should be:
- **Owned by the user**
- **Private to the user** (not readable by other users)
- **Stored in user's home directory**

```bash
# User data permissions
/home/{username}/.llm-os/         # user:user, 700
├── config.yaml                   # user:user, 600
├── history.json                  # user:user, 600
└── logs/                         # user:user, 700
```

## Working Directory Separation

### Core System Working Directory

The LLM-OS core should:
- Be installed in `/opt/llm-os/`
- Run from the system installation directory
- Never modify its own code directory
- Load configuration from both system and user locations

### User Command Working Directory

User commands should:
- Execute from the user's current directory (typically `~/`)
- Have access to user's files and folders
- Never access or modify the core system
- Use relative paths from the user's working directory

## Installation Methods

### Method 1: System-Wide Installation (Recommended for Production)

```bash
# Install as root/sudo
sudo pip install llm-os --target /opt/llm-os/lib
sudo mkdir -p /opt/llm-os/{bin,share,config}

# Create launcher script
sudo cat > /opt/llm-os/bin/llm-os << 'EOF'
#!/bin/bash
export PYTHONPATH="/opt/llm-os/lib:$PYTHONPATH"
export LLM_OS_HOME="/opt/llm-os"
export LLM_OS_USER_DIR="$HOME/.llm-os"

# Create user config directory if it doesn't exist
mkdir -p "$LLM_OS_USER_DIR/logs"

# Run from user's working directory, not system directory
exec python3 -m llm_os "$@"
EOF

sudo chmod +x /opt/llm-os/bin/llm-os

# Create symlink for global access
sudo ln -sf /opt/llm-os/bin/llm-os /usr/local/bin/llm-os

# Set proper permissions
sudo chown -R root:root /opt/llm-os
sudo chmod -R 755 /opt/llm-os
```

### Method 2: Development Installation (Current)

```bash
# Development mode - install in user space
cd ~/llm-os
pip install -e .

# Run from development directory
./launch.sh
```

### Method 3: User-Level Installation (Single User)

```bash
# Install for current user only
pip install --user llm-os

# Create user launcher
mkdir -p ~/.local/bin
cat > ~/.local/bin/llm-os << 'EOF'
#!/bin/bash
export LLM_OS_USER_DIR="$HOME/.llm-os"
mkdir -p "$LLM_OS_USER_DIR/logs"
exec python3 -m llm_os "$@"
EOF

chmod +x ~/.local/bin/llm-os
```

## Environment Variables

### System-Level Variables

- `LLM_OS_HOME` - Installation directory (e.g., `/opt/llm-os`)
- `LLM_OS_SYSTEM_CONFIG` - System config directory (e.g., `/opt/llm-os/config`)

### User-Level Variables

- `LLM_OS_USER_DIR` - User data directory (default: `~/.llm-os`)
- `LLM_OS_CONFIG` - User config file (default: `~/.llm-os/config.yaml`)
- `LLM_OS_HISTORY` - History file (default: `~/.llm-os/history.json`)
- `LLM_OS_LOG_DIR` - Log directory (default: `~/.llm-os/logs`)

### Runtime Variables

- `LLM_OS_WORKING_DIR` - Current working directory (user's PWD)
- `GROQ_API_KEY` - Groq API key
- `OPENAI_API_KEY` - OpenAI API key
- Other provider-specific keys

## Configuration Hierarchy

LLM-OS uses a hierarchical configuration system:

1. **System Defaults** - Built-in defaults in code
2. **System Config** - `/opt/llm-os/config/defaults.yaml`
3. **User Config** - `~/.llm-os/config.yaml`
4. **Environment Variables** - Runtime overrides
5. **CLI Arguments** - Command-line flags

Later sources override earlier ones.

## File Operations Security

### Principles

1. **User commands execute in user context**
   - Working directory: User's current directory
   - Permissions: User's permissions
   - Scope: Limited to user's accessible files

2. **Core system is protected**
   - Read-only for users
   - No user process can modify system files
   - System updates require admin privileges

3. **Sandboxing for safety**
   - MCP servers run with user permissions
   - File operations restricted to user-accessible paths
   - No access to system directories without explicit permission

### Path Resolution

```python
# Example path resolution logic
import os
from pathlib import Path

def get_system_dir() -> Path:
    """Get core system installation directory."""
    return Path(os.environ.get('LLM_OS_HOME', '/opt/llm-os'))

def get_user_dir() -> Path:
    """Get user configuration directory."""
    return Path(os.environ.get('LLM_OS_USER_DIR', Path.home() / '.llm-os'))

def get_working_dir() -> Path:
    """Get user's working directory for command execution."""
    return Path.cwd()

# Never change cwd to system directory
# Always execute user commands from user's working directory
```

## Migration from Development to Production

### Step 1: Test in Development

```bash
cd ~/llm-os
./launch.sh
# Test functionality
```

### Step 2: Package for Production

```bash
# Build distribution package
cd ~/llm-os
python -m build

# This creates dist/llm_os-*.whl
```

### Step 3: Deploy to Production System

```bash
# On production Ubuntu system
sudo pip install /path/to/llm_os-*.whl --target /opt/llm-os/lib

# Set up as described in Installation Method 1
```

### Step 4: Verify Separation

```bash
# Run as regular user
llm-os

# Verify running from correct directories
# Core: /opt/llm-os/lib/llm_os/
# Working: /home/username/
# Config: /home/username/.llm-os/
```

## Ubuntu Integration Testing Checklist

Before deploying to Ubuntu for evaluation:

- [ ] Core system installed in `/opt/llm-os/`
- [ ] Launcher script in `/usr/local/bin/llm-os`
- [ ] System permissions correct (root:root, 755)
- [ ] User config directory created (`~/.llm-os/`)
- [ ] User permissions correct (user:user, 700)
- [ ] Commands execute from user's working directory
- [ ] File operations work in user space
- [ ] Core system files are read-only for users
- [ ] Configuration hierarchy works (system → user → env → cli)
- [ ] Multiple users can use system independently
- [ ] No conflicts between users
- [ ] Logs go to user-specific directories
- [ ] History is per-user
- [ ] API keys are per-user or in user config

## Code Changes Required

To support this structure, the following code changes are needed:

### 1. Path Resolution Module

Create `src/llm_os/paths.py`:

```python
"""Path resolution for LLM-OS."""
import os
from pathlib import Path
from typing import Optional

def get_system_dir() -> Path:
    """Get system installation directory."""
    return Path(os.environ.get('LLM_OS_HOME', '/opt/llm-os'))

def get_user_dir() -> Path:
    """Get user data directory."""
    default = Path.home() / '.llm-os'
    return Path(os.environ.get('LLM_OS_USER_DIR', default))

def get_working_dir() -> Path:
    """Get current working directory (for user commands)."""
    return Path.cwd()

def ensure_user_dirs() -> None:
    """Ensure user directories exist."""
    user_dir = get_user_dir()
    (user_dir / 'logs').mkdir(parents=True, exist_ok=True)
    (user_dir / 'cache').mkdir(parents=True, exist_ok=True)
```

### 2. Configuration Updates

Update `config/__init__.py` to load from multiple locations:

```python
def load_config() -> Config:
    """Load configuration from hierarchy."""
    # 1. Start with defaults
    config = Config()

    # 2. Load system config
    system_config = get_system_dir() / 'config' / 'defaults.yaml'
    if system_config.exists():
        config.update_from_file(system_config)

    # 3. Load user config
    user_config = get_user_dir() / 'config.yaml'
    if user_config.exists():
        config.update_from_file(user_config)

    # 4. Apply environment variables
    config.update_from_env()

    return config
```

### 3. CLI Updates

Update `src/llm_os/cli.py` to initialize paths:

```python
def main() -> int:
    """Main CLI entry point."""
    from llm_os.paths import ensure_user_dirs, get_working_dir

    # Ensure user directories exist
    ensure_user_dirs()

    # Verify we're running from user space
    working_dir = get_working_dir()
    logger.info(f"Working directory: {working_dir}")

    # Rest of CLI logic...
```

### 4. Logging Updates

Update logging to use user-specific directories:

```python
from llm_os.paths import get_user_dir

def setup_logging():
    """Configure logging to user directory."""
    log_dir = get_user_dir() / 'logs'
    log_file = log_dir / 'llm-os.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
```

## Testing the Deployment

### Test 1: Multi-User Isolation

```bash
# As user1
user1@ubuntu:~$ llm-os
> list files in my home directory
[Should list user1's files]

# As user2
user2@ubuntu:~$ llm-os
> list files in my home directory
[Should list user2's files, not user1's]
```

### Test 2: System Protection

```bash
# As regular user
user@ubuntu:~$ llm-os
> modify the core system files
[Should fail - no write permission]

> read /opt/llm-os/lib/llm_os/core.py
[Should succeed - read access OK]
```

### Test 3: Working Directory

```bash
user@ubuntu:~/projects/myapp$ llm-os
> what is my current directory
[Should report: /home/user/projects/myapp]

> list files here
[Should list files in /home/user/projects/myapp, not /opt/llm-os]
```

## Summary

The proper deployment structure ensures:

1. **Security** - Core system protected from user modifications
2. **Multi-user** - Multiple users can use the system independently
3. **Isolation** - User data and configs are separate per user
4. **Safety** - User commands execute in user context, not system context
5. **Maintainability** - System updates don't affect user data
6. **Standards Compliance** - Follows Linux FHS and best practices

This structure prepares LLM-OS for production deployment on Ubuntu and other Linux distributions.
