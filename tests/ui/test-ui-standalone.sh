#!/bin/bash
# OSSARTH UI Test - Launch with dummy backend

echo "Starting OSSARTH UI Test..."
echo

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate conda environment and run the test
source ~/miniconda3/etc/profile.d/conda.sh
conda activate llm-os
python "$SCRIPT_DIR/test_ui_standalone.py"

# Check exit status
if [ $? -ne 0 ]; then
    echo
    echo "Error: UI failed to start"
    read -p "Press Enter to continue..."
fi
