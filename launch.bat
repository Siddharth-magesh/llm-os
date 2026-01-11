@echo off
REM LLM-OS Launcher Script for Windows

echo.
echo ====================================
echo   LLM-OS - Natural Language Shell
echo ====================================
echo.

REM Set Groq API Key
set GROQ_API_KEY=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

REM Check if we're in the right directory
if not exist "src\llm_os" (
    echo ERROR: Cannot find src\llm_os directory
    echo Please run this script from the llm-os project root
    pause
    exit /b 1
)

REM Initialize conda for this shell session
if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
    call "%USERPROFILE%\miniconda3\Scripts\activate.bat"
) else if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
    call "%USERPROFILE%\anaconda3\Scripts\activate.bat"
) else if exist "C:\ProgramData\miniconda3\Scripts\activate.bat" (
    call "C:\ProgramData\miniconda3\Scripts\activate.bat"
) else (
    echo ERROR: Cannot find conda installation
    echo Please ensure conda/miniconda is installed
    pause
    exit /b 1
)

REM Activate the llm-os environment
echo Activating conda environment: llm-os
call conda activate llm-os
if errorlevel 1 (
    echo ERROR: Failed to activate conda environment 'llm-os'
    echo Please ensure it exists: conda create -n llm-os python=3.11
    pause
    exit /b 1
)

REM Launch LLM-OS
echo Starting LLM-OS...
echo.
python -m llm_os

REM Pause on exit to see any errors
if errorlevel 1 (
    echo.
    echo ERROR: LLM-OS exited with an error
    pause
)
