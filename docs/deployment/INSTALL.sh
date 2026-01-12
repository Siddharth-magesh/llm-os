#!/bin/bash
# LLM-OS System-Wide Installation Script
# This script installs LLM-OS to /opt/llm-os for production use

set -e  # Exit on error

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

echo "======================================"
echo "  LLM-OS System Installation"
echo "======================================"
echo ""

# Configuration
INSTALL_DIR="/opt/llm-os"
BIN_DIR="/usr/local/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Installation directory: $INSTALL_DIR"
echo "Launcher directory: $BIN_DIR"
echo "Source directory: $SCRIPT_DIR"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    echo "Install Python 3.10+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python $PYTHON_VERSION"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed"
    echo "Install pip and try again"
    exit 1
fi

# Create installation directory
echo "Creating installation directory..."
mkdir -p "$INSTALL_DIR"/{lib,bin,share,config}

# Install Python package
echo "Installing LLM-OS package..."
cd "$SCRIPT_DIR"

# Option 1: Install from source in development mode
if [ -f "pyproject.toml" ]; then
    echo "Installing from source..."
    pip3 install -e "$SCRIPT_DIR" --target "$INSTALL_DIR/lib"
else
    echo "Error: Cannot find pyproject.toml"
    echo "Please run this script from the llm-os project root"
    exit 1
fi

# Copy configuration files
echo "Copying configuration files..."
if [ -d "$SCRIPT_DIR/config" ]; then
    cp -r "$SCRIPT_DIR/config" "$INSTALL_DIR/"
fi

# Copy documentation
echo "Copying documentation..."
if [ -d "$SCRIPT_DIR/docs" ]; then
    cp -r "$SCRIPT_DIR/docs" "$INSTALL_DIR/share/"
fi

# Install launcher script
echo "Installing launcher script..."
cat > "$BIN_DIR/llm-os" << 'EOF'
#!/bin/bash
# LLM-OS Production Launcher

# Set environment variables
export LLM_OS_HOME="/opt/llm-os"
export LLM_OS_USER_DIR="${LLM_OS_USER_DIR:-$HOME/.llm-os}"
export PYTHONPATH="/opt/llm-os/lib:${PYTHONPATH}"

# Create user directories
mkdir -p "$LLM_OS_USER_DIR/logs"
mkdir -p "$LLM_OS_USER_DIR/cache"

# Find Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python 3 not found"
    exit 1
fi

# Run LLM-OS from user's working directory
exec "$PYTHON" -m llm_os "$@"
EOF

chmod +x "$BIN_DIR/llm-os"

# Set proper permissions
echo "Setting permissions..."
chown -R root:root "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"

# Verify installation
echo ""
echo "======================================"
echo "  Installation Complete!"
echo "======================================"
echo ""
echo "Installation directory: $INSTALL_DIR"
echo "Launcher: $BIN_DIR/llm-os"
echo ""
echo "To use LLM-OS, run: llm-os"
echo ""
echo "User configuration will be stored in: ~/.llm-os/"
echo ""

# Test the installation
if command -v llm-os &> /dev/null; then
    echo "Testing installation..."
    llm-os --version || echo "Warning: Could not verify installation"
else
    echo "Warning: llm-os command not found in PATH"
    echo "Make sure $BIN_DIR is in your PATH"
fi

echo ""
echo "Installation complete!"
