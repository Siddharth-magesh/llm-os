#!/bin/bash
# Test External Time MCP Server

echo ""
echo "======================================"
echo "Testing External Time MCP Server"
echo "======================================"
echo ""
echo "Checking Node.js installation..."

if ! command -v node &> /dev/null; then
    echo "✗ Node.js not found!"
    echo ""
    echo "Please install Node.js from https://nodejs.org/"
    read -p "Press enter to continue..."
    exit 1
fi

if ! command -v npx &> /dev/null; then
    echo "✗ npx not found!"
    echo ""
    echo "Please ensure Node.js is properly installed"
    read -p "Press enter to continue..."
    exit 1
fi

echo "✓ Node.js found"
echo "✓ npx found"
echo ""

cd "$(dirname "$0")"
python test_external_time.py

read -p "Press enter to continue..."
