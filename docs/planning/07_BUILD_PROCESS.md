# LLM-OS: Build Process and ISO Creation

## Overview

This document provides step-by-step instructions for building the LLM-OS custom Linux distribution, from setting up the build environment to creating a bootable ISO image.

---

## 1. Build Environment Setup

### 1.1 Requirements

| Requirement | Specification |
|-------------|---------------|
| **Host OS** | Ubuntu 22.04+ or Debian 11+ |
| **RAM** | 16GB minimum, 32GB recommended |
| **Disk Space** | 100GB+ free |
| **Internet** | Required for package downloads |
| **Time** | 2-4 hours for full build |

### 1.2 Option A: Build on Linux Host

If you have a Linux machine or dual-boot:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install build dependencies
sudo apt install -y \
    cubic \
    squashfs-tools \
    xorriso \
    isolinux \
    syslinux-utils \
    python3 python3-pip python3-venv \
    git curl wget \
    qemu-system-x86 qemu-utils

# Install Cubic (Custom Ubuntu ISO Creator)
sudo apt-add-repository ppa:cubic-wizard/release
sudo apt update
sudo apt install cubic
```

### 1.3 Option B: Build in VMware/VirtualBox

If building from Windows:

1. **Create Ubuntu VM for Building**
   - Download Ubuntu 24.04 LTS Desktop ISO
   - Create VM with 8GB+ RAM, 100GB disk
   - Install Ubuntu
   - Proceed with Linux host setup above

### 1.4 Option C: Use Docker (Advanced)

```bash
# Create build container
docker run -it --name llm-os-builder \
    -v /path/to/output:/output \
    ubuntu:24.04 /bin/bash

# Inside container, install dependencies
apt update && apt install -y cubic squashfs-tools xorriso
```

---

## 2. Preparing the Base ISO

### 2.1 Download Ubuntu 24.04 LTS

```bash
# Create working directory
mkdir -p ~/llm-os-build
cd ~/llm-os-build

# Download Ubuntu 24.04.1 LTS Desktop
wget https://releases.ubuntu.com/24.04.1/ubuntu-24.04.1-desktop-amd64.iso

# Verify checksum
sha256sum ubuntu-24.04.1-desktop-amd64.iso
# Compare with official checksum from ubuntu.com
```

### 2.2 Create Project Directory

```bash
# Create Cubic project directory
mkdir -p ~/llm-os-build/cubic-project

# This directory will contain:
# - custom-disk/     (extracted ISO contents)
# - custom-root/     (modified root filesystem)
# - llm-os.iso       (output ISO)
```

---

## 3. Using Cubic for ISO Customization

### 3.1 Launch Cubic

```bash
# Launch Cubic
cubic

# Or from applications menu: "Cubic"
```

### 3.2 Initial Setup

1. **Project Directory**: Select `~/llm-os-build/cubic-project`
2. **Original ISO**: Select downloaded Ubuntu ISO
3. **Custom ISO Filename**: `llm-os-0.1.0-amd64.iso`
4. **Custom ISO Volume ID**: `LLM-OS 0.1.0`

Cubic will extract the ISO and prepare the chroot environment.

### 3.3 Chroot Environment

You'll be dropped into a terminal inside the ISO's filesystem. All changes here become part of the custom ISO.

---

## 4. Customization Steps

### 4.1 System Updates

```bash
# Inside Cubic chroot terminal

# Update package lists
apt update

# Upgrade existing packages
apt upgrade -y
```

### 4.2 Remove Unnecessary Packages

```bash
# Remove games
apt purge -y \
    aisleriot \
    gnome-mahjongg \
    gnome-mines \
    gnome-sudoku

# Remove unnecessary apps (optional)
apt purge -y \
    rhythmbox \
    shotwell \
    totem

# Clean up
apt autoremove -y
apt clean
```

### 4.3 Install Core Dependencies

```bash
# Essential tools
apt install -y \
    build-essential \
    git \
    curl \
    wget \
    jq \
    htop \
    tmux \
    neovim \
    tree \
    ncdu \
    unzip \
    p7zip-full

# Python
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev

# Node.js (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Terminal and fonts
apt install -y \
    alacritty \
    fonts-firacode \
    fonts-noto
```

### 4.4 Install LLM Infrastructure

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Enable Ollama service (will start on boot)
systemctl enable ollama

# Pre-pull models (optional - increases ISO size significantly)
# ollama pull llama3.2:3b

# Install Python LLM libraries
pip3 install --break-system-packages \
    textual \
    rich \
    httpx \
    pydantic \
    typer \
    anthropic \
    openai \
    ollama \
    mcp

# Install development libraries
pip3 install --break-system-packages \
    pytest \
    pytest-asyncio \
    black \
    ruff
```

### 4.5 Install Applications

```bash
# Development tools
apt install -y \
    git \
    docker.io \
    docker-compose

# Add VS Code repository
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list
apt update
apt install -y code

# Browsers
apt install -y firefox chromium-browser

# Office/Productivity
apt install -y libreoffice

# Media
apt install -y vlc gimp

# Utilities
apt install -y nautilus gnome-calculator
```

### 4.6 Create LLM-OS Directory Structure

```bash
# Create system directories
mkdir -p /etc/llm-os
mkdir -p /usr/lib/llm-os/mcp-servers
mkdir -p /usr/share/llm-os/prompts
mkdir -p /var/log/llm-os
mkdir -p /var/lib/llm-os/cache

# Set permissions
chmod 755 /etc/llm-os
chmod 755 /usr/lib/llm-os
```

### 4.7 Add LLM-OS Configuration Files

```bash
# Create main config
cat > /etc/llm-os/config.yaml << 'EOF'
# LLM-OS Configuration
version: "0.1.0"

# LLM Settings
llm:
  default_provider: "ollama"
  fallback_provider: "claude"
  local_first: true

# MCP Settings
mcp:
  servers_dir: "/usr/lib/llm-os/mcp-servers"
  user_servers_dir: "~/.config/llm-os/mcp-servers"
  auto_discover: true

# UI Settings
ui:
  theme: "dark"
  show_status_bar: true
  stream_responses: true

# Security Settings
security:
  confirm_destructive: true
  sandbox_untrusted: true
EOF
```

### 4.8 Add System Prompt

```bash
cat > /usr/share/llm-os/prompts/system.txt << 'EOF'
You are the AI core of LLM-OS, a natural language operating system.

Your role is to translate natural language commands into system operations using the available tools.

Guidelines:
1. Be proactive - execute obvious intents without unnecessary questions
2. Be clear - explain what you're doing before and after
3. Be safe - confirm before destructive operations
4. Be helpful - suggest alternatives when something fails

Available tool categories:
- Filesystem: file operations
- Applications: launch and manage apps
- Browser: web browsing
- Git: version control
- System: system information and management
EOF
```

### 4.9 Create MCP Server Stubs

```bash
# Create filesystem server placeholder
mkdir -p /usr/lib/llm-os/mcp-servers/filesystem
cat > /usr/lib/llm-os/mcp-servers/filesystem/server.py << 'EOF'
#!/usr/bin/env python3
"""Filesystem MCP Server - Placeholder"""
# Full implementation to be added
print("Filesystem MCP Server placeholder")
EOF
chmod +x /usr/lib/llm-os/mcp-servers/filesystem/server.py
```

### 4.10 Create Startup Script

```bash
# Create main executable
cat > /usr/bin/llm-os << 'EOF'
#!/bin/bash
# LLM-OS Launcher

echo "Starting LLM-OS..."

# Check if Ollama is running
if ! systemctl is-active --quiet ollama; then
    echo "Starting Ollama service..."
    sudo systemctl start ollama
    sleep 2
fi

# Launch NL-Shell (placeholder)
echo ""
echo "============================================"
echo "  Welcome to LLM-OS"
echo "  Type commands in natural language"
echo "============================================"
echo ""
echo "NL-Shell starting..."
echo "(Full implementation in development)"
echo ""

# For now, drop to bash with custom prompt
export PS1="\[\e[36m\]llm-os>\[\e[0m\] "
exec bash --norc
EOF
chmod +x /usr/bin/llm-os
```

### 4.11 Configure Auto-Login (Optional)

For development/testing, enable auto-login:

```bash
# Edit GDM config
mkdir -p /etc/gdm3
cat > /etc/gdm3/custom.conf << 'EOF'
[daemon]
AutomaticLoginEnable=true
AutomaticLogin=llmos

[security]

[xdmcp]

[chooser]

[debug]
EOF
```

### 4.12 Create Default User

```bash
# Create llmos user
useradd -m -s /bin/bash -G sudo,docker llmos
echo "llmos:llmos" | chpasswd

# Add to groups
usermod -aG audio,video,plugdev llmos
```

### 4.13 Set Desktop Wallpaper and Branding

```bash
# Create simple branding
mkdir -p /usr/share/backgrounds/llm-os

# Create a placeholder background (solid color)
# In production, add actual image file

# Set default background in dconf (GNOME)
mkdir -p /etc/dconf/db/local.d
cat > /etc/dconf/db/local.d/01-background << 'EOF'
[org/gnome/desktop/background]
picture-uri='file:///usr/share/backgrounds/llm-os/wallpaper.png'
picture-uri-dark='file:///usr/share/backgrounds/llm-os/wallpaper.png'
EOF
```

### 4.14 Final Cleanup

```bash
# Clean package cache
apt clean
apt autoremove -y

# Clear temporary files
rm -rf /tmp/*
rm -rf /var/tmp/*

# Clear bash history
history -c

# Clear logs (optional - for smaller ISO)
find /var/log -type f -name "*.log" -delete
```

---

## 5. Finalizing in Cubic

### 5.1 Exit Chroot

Type `exit` or press Ctrl+D to exit the chroot environment.

### 5.2 Package Selection

Cubic will show installed packages. You can:
- Review the list
- Remove additional packages
- Keep defaults

### 5.3 Kernel Selection

Select which kernel to include (typically keep the latest).

### 5.4 Boot Configuration

Cubic allows modifying boot parameters:
- Keep defaults for standard use
- Add `quiet splash` for clean boot
- Optionally add `llm-os.autostart=1`

### 5.5 Compression Options

| Option | Size | Speed |
|--------|------|-------|
| `gzip` | Larger | Fast |
| `lz4` | Larger | Fastest |
| `xz` | Smallest | Slowest |

For development, use `gzip`. For distribution, use `xz`.

### 5.6 Generate ISO

Click "Generate" to create the ISO. This takes 10-30 minutes.

Output: `~/llm-os-build/cubic-project/llm-os-0.1.0-amd64.iso`

---

## 6. Testing the ISO

### 6.1 Test with QEMU (Quick)

```bash
# Test boot
qemu-system-x86_64 \
    -cdrom ~/llm-os-build/cubic-project/llm-os-0.1.0-amd64.iso \
    -m 4G \
    -enable-kvm \
    -boot d

# With more resources
qemu-system-x86_64 \
    -cdrom ~/llm-os-build/cubic-project/llm-os-0.1.0-amd64.iso \
    -m 8G \
    -smp 4 \
    -enable-kvm \
    -boot d \
    -vga virtio
```

### 6.2 Test with VMware/VirtualBox

1. Create new VM
2. Select ISO as boot media
3. Configure: 8GB RAM, 4 cores, 50GB disk
4. Boot and test

### 6.3 Testing Checklist

```markdown
## Boot Test
- [ ] ISO boots successfully
- [ ] GRUB menu appears
- [ ] System reaches desktop/login

## Core Functionality
- [ ] User can login
- [ ] Terminal opens
- [ ] `llm-os` command runs
- [ ] Ollama service starts
- [ ] Internet connectivity works

## Applications
- [ ] Firefox launches
- [ ] VS Code launches
- [ ] File manager works

## LLM-OS Specific
- [ ] /etc/llm-os/config.yaml exists
- [ ] /usr/lib/llm-os/mcp-servers/ exists
- [ ] Python packages installed (textual, rich, etc.)
- [ ] Node.js installed
```

---

## 7. Alternative: live-build (Advanced)

For more control, use Debian's live-build:

### 7.1 Setup

```bash
# Install live-build
sudo apt install live-build

# Create project directory
mkdir -p ~/llm-os-livebuild
cd ~/llm-os-livebuild
```

### 7.2 Configuration

```bash
# Initialize live-build config
lb config \
    --distribution noble \
    --archive-areas "main restricted universe multiverse" \
    --apt-recommends false \
    --binary-images iso-hybrid \
    --bootappend-live "boot=live components quiet splash" \
    --linux-packages "linux-generic" \
    --memtest none \
    --debian-installer none
```

### 7.3 Package Lists

```bash
# Create package list
mkdir -p config/package-lists

cat > config/package-lists/llm-os.list.chroot << 'EOF'
# Core utilities
build-essential
git
curl
wget
htop
tmux
neovim

# Python
python3
python3-pip
python3-venv

# LLM infrastructure
# (Ollama installed via hook)

# Applications
firefox
code
vlc
EOF
```

### 7.4 Hooks

```bash
# Create hooks directory
mkdir -p config/hooks/live

# Create setup hook
cat > config/hooks/live/0100-setup-llm-os.hook.chroot << 'EOF'
#!/bin/bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Install Python packages
pip3 install textual rich httpx pydantic typer anthropic openai ollama mcp

# Create directories
mkdir -p /etc/llm-os
mkdir -p /usr/lib/llm-os/mcp-servers
EOF
chmod +x config/hooks/live/0100-setup-llm-os.hook.chroot
```

### 7.5 Build

```bash
# Build the ISO
sudo lb build

# Output: live-image-amd64.hybrid.iso
```

---

## 8. Continuous Integration Build

### 8.1 GitHub Actions Workflow

```yaml
# .github/workflows/build-iso.yml
name: Build LLM-OS ISO

on:
  push:
    branches: [main]
    tags: ['v*']
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            squashfs-tools \
            xorriso \
            isolinux \
            syslinux-utils

      - name: Build ISO
        run: |
          ./scripts/build-iso.sh

      - name: Upload ISO
        uses: actions/upload-artifact@v4
        with:
          name: llm-os-iso
          path: build/*.iso

      - name: Create Release
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v1
        with:
          files: build/*.iso
```

### 8.2 Build Script

```bash
#!/bin/bash
# scripts/build-iso.sh

set -e

echo "Building LLM-OS ISO..."

# Configuration
ISO_NAME="llm-os"
VERSION="${VERSION:-0.1.0}"
BUILD_DIR="build"
OUTPUT_ISO="${BUILD_DIR}/${ISO_NAME}-${VERSION}-amd64.iso"

# Create build directory
mkdir -p ${BUILD_DIR}

# Download base ISO if not present
if [ ! -f "${BUILD_DIR}/ubuntu-base.iso" ]; then
    echo "Downloading Ubuntu base ISO..."
    wget -O "${BUILD_DIR}/ubuntu-base.iso" \
        "https://releases.ubuntu.com/24.04.1/ubuntu-24.04.1-desktop-amd64.iso"
fi

# Extract ISO
echo "Extracting ISO..."
# ... extraction steps ...

# Apply customizations
echo "Applying customizations..."
# ... customization steps ...

# Build new ISO
echo "Building custom ISO..."
# ... build steps ...

echo "Build complete: ${OUTPUT_ISO}"
```

---

## 9. Creating Bootable USB

### 9.1 Using dd (Linux)

```bash
# CAUTION: Double-check device name!
# Find your USB device
lsblk

# Write ISO to USB (replace sdX with your device)
sudo dd if=llm-os-0.1.0-amd64.iso of=/dev/sdX bs=4M status=progress conv=fsync
```

### 9.2 Using Balena Etcher (Cross-platform)

1. Download [Balena Etcher](https://www.balena.io/etcher/)
2. Select the ISO
3. Select target USB drive
4. Flash

### 9.3 Using Rufus (Windows)

1. Download [Rufus](https://rufus.ie/)
2. Select ISO
3. Select target USB
4. Select "DD Image mode" when prompted
5. Start

---

## 10. Troubleshooting Build Issues

### Common Issues

| Issue | Solution |
|-------|----------|
| Cubic hangs | Increase VM resources, check disk space |
| Package installation fails | Check internet, try different mirror |
| ISO too large | Remove unnecessary packages, use xz compression |
| Boot fails | Check UEFI/Legacy settings, verify ISO integrity |
| No display | Add `nomodeset` to boot parameters |

### Build Logs

```bash
# Cubic logs
~/.cubic/cubic.log

# live-build logs
build.log

# Check for errors
grep -i error build.log
```

---

## 11. Version Release Checklist

```markdown
## Pre-Release
- [ ] All features tested in VM
- [ ] Documentation updated
- [ ] Changelog written
- [ ] Version number updated in config files

## Build
- [ ] Clean build from fresh environment
- [ ] ISO generates without errors
- [ ] SHA256 checksum generated

## Testing
- [ ] Boot test in QEMU
- [ ] Boot test in VMware/VirtualBox
- [ ] Test on physical hardware (if possible)
- [ ] All checklist items pass

## Release
- [ ] Upload ISO to release server
- [ ] Update download links
- [ ] Announce release
```

---

## References

- [Cubic GitHub](https://github.com/PJ-Singh-001/Cubic)
- [Ubuntu Live Manual](https://help.ubuntu.com/community/LiveCDCustomization)
- [Debian live-build Manual](https://live-team.pages.debian.net/live-manual/)
- [QEMU Documentation](https://www.qemu.org/documentation/)

---

*Document Version: 1.0*
*Last Updated: January 2026*
