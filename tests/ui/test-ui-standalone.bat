@echo off
REM OSSARTH UI Test - Launch with dummy backend
echo Starting OSSARTH UI Test...
echo.

C:\Users\Siddharth\miniconda3\envs\llm-os\python.exe "%~dp0test_ui_standalone.py"

if errorlevel 1 (
    echo.
    echo Error: UI failed to start
    pause
)
