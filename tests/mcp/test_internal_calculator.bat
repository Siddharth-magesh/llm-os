@echo off
REM Test Internal Calculator MCP Server

echo.
echo ========================================
echo Testing Internal Calculator MCP Server
echo ========================================
echo.

cd /d "%~dp0"
C:\Users\Siddharth\miniconda3\envs\llm-os\python.exe test_internal_calculator.py

if errorlevel 1 (
    echo.
    echo ✗ Test FAILED
) else (
    echo.
    echo ✓ Test PASSED
)

pause
