# LLM-OS Setup and Deployment Guide

## Quick Start

Choose the installation method that fits your needs:

1. **Development Mode** - For development and testing
2. **User Installation** - For single user, no root access required
3. **System Installation** - For production, multi-user systems

---

## 1. Development Mode (Current Setup)

This is what you're currently using. Best for development and testing.

### Location
```
/home/siddharth/llm-os/
```

### How to Run
```bash
cd ~/llm-os
./launch.sh
```

### Characteristics
- Code is in your home directory
- Changes take effect immediately
- Single user
- Working directory: Current directory when launched
- User data: `~/.llm-os/`

---

## 2. User Installation

Install LLM-OS for your user account only, without root access.

### Installation Steps

```bash
# Navigate to the project directory
cd ~/llm-os

# Install for current user
pip install --user -e .

# Verify installation
which llm-os  # Should show: ~/.local/bin/llm-os
```

### Configuration

The launcher will be at: `~/.local/bin/llm-os`

Make sure `~/.local/bin` is in your PATH:
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
```

### How to Run
```bash
llm-os
```

### Characteristics
- Installed in `~/.local/`
- No root required
- Single user
- Working directory: Current directory when launched
- User data: `~/.llm-os/`

---

## 3. System Installation (Production)

Install LLM-OS system-wide for all users. Requires root access.

### Installation Steps

```bash
# Navigate to the project directory
cd ~/llm-os

# Run installation script as root
sudo ./docs/deployment/INSTALL.sh
```

### Manual Installation (Alternative)

```bash
# Create installation directory
sudo mkdir -p /opt/llm-os/{lib,bin,share,config}

# Install Python package
sudo pip3 install . --target /opt/llm-os/lib

# Copy configuration
sudo cp -r config /opt/llm-os/

# Copy documentation
sudo cp -r docs /opt/llm-os/share/

# Install launcher
sudo cp llm-os-launcher.sh /usr/local/bin/llm-os
sudo chmod +x /usr/local/bin/llm-os

# Set permissions
sudo chown -R root:root /opt/llm-os
sudo chmod -R 755 /opt/llm-os
```

### How to Run
```bash
llm-os
```

### Characteristics
- System-wide installation at `/opt/llm-os/`
- Available to all users
- Root-owned, read-only for users
- Working directory: User's current directory
- User data: `~/.llm-os/` (per user)
- Multi-user safe

---

## Directory Structure Comparison

### Development Mode
```
~/llm-os/                        # Your working copy
├── src/llm_os/                  # Source code
├── config/                      # Configuration
└── launch.sh                    # Launcher

~/.llm-os/                       # User data
├── config.yaml                  # User settings
├── history.json                 # Command history
└── logs/                        # Log files
```

### User Installation
```
~/.local/lib/python3.x/site-packages/llm_os/   # Installed package
~/.local/bin/llm-os                             # Launcher

~/.llm-os/                       # User data
├── config.yaml
├── history.json
└── logs/
```

### System Installation
```
/opt/llm-os/                     # System installation (read-only)
├── lib/llm_os/                  # Core package
├── config/                      # System config
├── bin/                         # Launcher scripts
└── share/docs/                  # Documentation

/usr/local/bin/llm-os            # Global launcher

~/.llm-os/                       # User data (per user)
├── config.yaml                  # User overrides
├── history.json                 # User history
└── logs/                        # User logs
```

---

## Testing the Deployment

### Test 1: Verify Paths

```bash
llm-os -v
# Check logs for path configuration:
# - System Directory: /opt/llm-os (or ~/.local)
# - User Directory: ~/.llm-os
# - Working Directory: /home/user/... (your current directory)
```

### Test 2: Working Directory

```bash
# Create a test directory
mkdir -p ~/test-workspace
cd ~/test-workspace
echo "Hello World" > test.txt

# Launch LLM-OS
llm-os

# Inside LLM-OS, ask:
> what is my current directory
# Should show: /home/siddharth/test-workspace

> list files here
# Should list: test.txt

> read test.txt
# Should show: Hello World
```

### Test 3: Multi-User (System Installation Only)

```bash
# As user1
user1@system:~$ llm-os
> list my files
[Shows user1's files]

# As user2
user2@system:~$ llm-os
> list my files
[Shows user2's files, not user1's]
```

### Test 4: System Protection

```bash
llm-os
> show me the core system files
[Can read /opt/llm-os files]

> modify /opt/llm-os/lib/llm_os/core.py
[Should fail - permission denied]
```

---

## Configuration

### System Configuration

For system-wide installation, edit:
```
/opt/llm-os/config/defaults.yaml
```

This affects all users.

### User Configuration

Each user can override settings:
```
~/.llm-os/config.yaml
```

### Environment Variables

```bash
# Override installation directory
export LLM_OS_HOME="/opt/llm-os"

# Override user data directory
export LLM_OS_USER_DIR="$HOME/.llm-os"

# API Keys
export GROQ_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
```

---

## Upgrading

### Development Mode
```bash
cd ~/llm-os
git pull
pip install -e .
```

### User Installation
```bash
cd ~/llm-os
git pull
pip install --user -e . --upgrade
```

### System Installation
```bash
cd ~/llm-os
git pull
sudo ./docs/deployment/INSTALL.sh
```

---

## Uninstallation

### Development Mode
```bash
# Remove user data only (keep source code)
rm -rf ~/.llm-os
```

### User Installation
```bash
pip uninstall llm-os
rm -rf ~/.llm-os
```

### System Installation
```bash
sudo rm -rf /opt/llm-os
sudo rm /usr/local/bin/llm-os
rm -rf ~/.llm-os  # Per user
```

---

## Troubleshooting

### Issue: Commands execute in wrong directory

**Problem**: LLM-OS operates on system files instead of user files

**Solution**: Check that `get_working_dir()` returns the user's current directory, not the installation directory.

```bash
# Verify with:
llm-os -v
# Look for "Working directory" in the logs
```

### Issue: Permission denied when accessing files

**Problem**: Running with wrong permissions

**Solution**:
- User files: Should work with user permissions
- System files: Only root can modify

### Issue: History not persisting

**Problem**: History file not writable

**Solution**: Check permissions on `~/.llm-os/`
```bash
chmod 700 ~/.llm-os
chmod 600 ~/.llm-os/history.json
```

### Issue: Multiple users seeing each other's data

**Problem**: Shared user data directory

**Solution**: Each user should have their own `~/.llm-os/` directory. Never share this between users.

---

## Next Steps

1. **Test in Development Mode**
   ```bash
   cd ~/llm-os
   ./launch.sh
   # Test all features
   ```

2. **Install for Your User** (if working well)
   ```bash
   pip install --user -e .
   ```

3. **Deploy to Ubuntu** (for evaluation)
   ```bash
   # On Ubuntu system:
   sudo ./docs/deployment/INSTALL.sh

   # Test as different users
   su - user1
   llm-os
   # ... test ...

   su - user2
   llm-os
   # ... test ...
   ```

4. **Evaluate Multi-User Setup**
   - Test that users can't see each other's data
   - Test that users can't modify system files
   - Test that all features work correctly
   - Test concurrent usage

---

## Summary

| Feature | Development | User Install | System Install |
|---------|-------------|--------------|----------------|
| Root Required | No | No | Yes |
| Multi-User | No | No | Yes |
| System Protected | No | Partially | Yes |
| Easy Updates | Yes | Yes | No |
| Production Ready | No | No | Yes |

**Recommendation**:
- Development: Use **Development Mode**
- Testing: Use **User Installation**
- Production: Use **System Installation**

For Ubuntu integration and evaluation, use **System Installation** to ensure proper separation and security.
