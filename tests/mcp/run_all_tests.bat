@echo off
REM Run All MCP Server Tests

echo.
echo ========================================
echo OSSARTH - MCP Server Test Suite
echo ========================================
echo.

cd /d "%~dp0"

echo.
echo [1/3] Testing Existing Internal Servers...
echo ----------------------------------------
C:\Users\Siddharth\miniconda3\envs\llm-os\python.exe test_existing_servers.py
if errorlevel 1 (
    echo ✗ Existing servers test FAILED
) else (
    echo ✓ Existing servers test PASSED
)

echo.
echo.
echo [2/3] Testing Custom Calculator Server...
echo ----------------------------------------
C:\Users\Siddharth\miniconda3\envs\llm-os\python.exe test_internal_calculator.py
if errorlevel 1 (
    echo ✗ Calculator test FAILED
) else (
    echo ✓ Calculator test PASSED
)

echo.
echo.
echo [3/3] Testing External Time Server...
echo ----------------------------------------
where npx >nul 2>&1
if errorlevel 1 (
    echo ✗ npx not found - skipping external server tests
    echo   Install Node.js from https://nodejs.org/
) else (
    C:\Users\Siddharth\miniconda3\envs\llm-os\python.exe test_external_time.py
    if errorlevel 1 (
        echo ✗ Time server test FAILED
    ) else (
        echo ✓ Time server test PASSED
    )
)

echo.
echo ========================================
echo All Tests Completed
echo ========================================
echo.

pause
