#!/bin/bash
# Run All MCP Server Tests

echo ""
echo "========================================"
echo "OSSARTH - MCP Server Test Suite"
echo "========================================"
echo ""

cd "$(dirname "$0")"

echo ""
echo "[1/3] Testing Existing Internal Servers..."
echo "----------------------------------------"
python test_existing_servers.py
if [ $? -eq 0 ]; then
    echo "✓ Existing servers test PASSED"
else
    echo "✗ Existing servers test FAILED"
fi

echo ""
echo ""
echo "[2/3] Testing Custom Calculator Server..."
echo "----------------------------------------"
python test_internal_calculator.py
if [ $? -eq 0 ]; then
    echo "✓ Calculator test PASSED"
else
    echo "✗ Calculator test FAILED"
fi

echo ""
echo ""
echo "[3/3] Testing External Time Server..."
echo "----------------------------------------"
if ! command -v npx &> /dev/null; then
    echo "✗ npx not found - skipping external server tests"
    echo "  Install Node.js from https://nodejs.org/"
else
    python test_external_time.py
    if [ $? -eq 0 ]; then
        echo "✓ Time server test PASSED"
    else
        echo "✗ Time server test FAILED"
    fi
fi

echo ""
echo "========================================"
echo "All Tests Completed"
echo "========================================"
echo ""

read -p "Press enter to continue..."
