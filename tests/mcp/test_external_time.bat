@echo off
REM Test External Time MCP Server

echo.
echo ======================================
echo Testing External Time MCP Server
echo ======================================
echo.
echo Checking Node.js installation...

where node >nul 2>&1
if errorlevel 1 (
    echo ✗ Node.js not found!
    echo.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

where npx >nul 2>&1
if errorlevel 1 (
    echo ✗ npx not found!
    echo.
    echo Please ensure Node.js is properly installed
    pause
    exit /b 1
)

echo ✓ Node.js found
echo ✓ npx found
echo.

cd /d "%~dp0"
C:\Users\Siddharth\miniconda3\envs\llm-os\python.exe test_external_time.py

pause
