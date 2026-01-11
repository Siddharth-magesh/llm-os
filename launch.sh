#!/bin/bash
# LLM-OS Launcher Script for Linux/Mac
# This script sets up the environment and launches LLM-OS

echo ""
echo "===================================="
echo "  LLM-OS - Natural Language Shell"
echo "===================================="
echo ""

# Set Groq API Key
export GROQ_API_KEY="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"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.10+ and try again"
    exit 1
fi

# Check if we're in the right directory
if [ ! -d "src/llm_os" ]; then
    echo "ERROR: Cannot find src/llm_os directory"
    echo "Please run this script from the llm-os project root"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Installing dependencies..."
    python3 -m pip install -e . > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "Warning: Installation may have failed"
    fi
fi

# Launch LLM-OS
echo "Starting LLM-OS..."
echo ""
python3 -m llm_os

# Check exit status
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: LLM-OS exited with an error"
    exit 1
fi
