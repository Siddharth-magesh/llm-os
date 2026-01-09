#!/bin/bash
# Test Existing Internal MCP Servers

echo ""
echo "========================================"
echo "Testing Existing Internal MCP Servers"
echo "========================================"
echo ""

cd "$(dirname "$0")"
python test_existing_servers.py

read -p "Press enter to continue..."
