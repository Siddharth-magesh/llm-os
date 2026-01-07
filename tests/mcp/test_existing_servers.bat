@echo off
REM Test Existing Internal MCP Servers

echo.
echo ========================================
echo Testing Existing Internal MCP Servers
echo ========================================
echo.

cd /d "%~dp0"
C:\Users\Siddharth\miniconda3\envs\llm-os\python.exe test_existing_servers.py

pause
