#!/bin/bash
# Test Internal Calculator MCP Server

echo ""
echo "========================================"
echo "Testing Internal Calculator MCP Server"
echo "========================================"
echo ""

cd "$(dirname "$0")"
python test_internal_calculator.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Test PASSED"
else
    echo ""
    echo "✗ Test FAILED"
fi

read -p "Press enter to continue..."
