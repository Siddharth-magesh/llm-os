#!/bin/bash
# LLM-OS Launcher Script for Linux/Mac

echo ""
echo "===================================="
echo "  LLM-OS - Natural Language Shell"
echo "===================================="
echo ""

# Set Groq API Key
export GROQ_API_KEY="your_groq_api_key_here"

# Check if we're in the right directory
if [ ! -d "src/llm_os" ]; then
    echo "ERROR: Cannot find src/llm_os directory"
    echo "Please run this script from the llm-os project root"
    exit 1
fi

# Find and initialize conda
CONDA_FOUND=false
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    CONDA_FOUND=true
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
    CONDA_FOUND=true
elif [ -f "/opt/miniconda3/etc/profile.d/conda.sh" ]; then
    source "/opt/miniconda3/etc/profile.d/conda.sh"
    CONDA_FOUND=true
elif [ -f "/usr/local/miniconda3/etc/profile.d/conda.sh" ]; then
    source "/usr/local/miniconda3/etc/profile.d/conda.sh"
    CONDA_FOUND=true
fi

if [ "$CONDA_FOUND" = false ]; then
    echo "ERROR: Cannot find conda installation"
    echo "Please ensure conda/miniconda is installed"
    exit 1
fi

# Activate the llm-os environment
echo "Activating conda environment: llm-os"
conda activate llm-os
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate conda environment 'llm-os'"
    echo "Please ensure it exists: conda create -n llm-os python=3.11"
    exit 1
fi

# Launch LLM-OS
echo "Starting LLM-OS..."
echo ""
python -m llm_os

# Check exit status
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: LLM-OS exited with an error"
    exit 1
fi
