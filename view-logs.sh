#!/bin/bash
# LLM-OS Log Viewer
# Convenient script for viewing logs

# Change to llm-os directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate conda environment if available
if command -v conda &> /dev/null; then
    source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || true
    conda activate llm-os 2>/dev/null || true
fi

# Run log viewer
python -m llm_os.utils.log_viewer "$@"
