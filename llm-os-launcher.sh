#!/bin/bash
# LLM-OS Production Launcher
# This script is designed to be installed in /usr/local/bin/llm-os

# Set environment variables for proper path resolution
export LLM_OS_HOME="${LLM_OS_HOME:-/opt/llm-os}"
export LLM_OS_USER_DIR="${LLM_OS_USER_DIR:-$HOME/.llm-os}"

# If installed in /opt, add to Python path
if [ -d "/opt/llm-os/lib" ]; then
    export PYTHONPATH="/opt/llm-os/lib:${PYTHONPATH}"
fi

# Create user config directory if it doesn't exist
mkdir -p "$LLM_OS_USER_DIR/logs"
mkdir -p "$LLM_OS_USER_DIR/cache"

# Find Python 3
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python 3 not found in PATH"
    exit 1
fi

# Run LLM-OS from the user's current working directory
# DO NOT change directory to the installation directory
exec "$PYTHON" -m llm_os "$@"
