@echo off
setlocal

set GROQ_API_KEY=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

call "%USERPROFILE%\miniconda3\Scripts\activate.bat" >nul 2>&1
call conda activate llm-os >nul 2>&1

echo ====================================
echo   Running LLM-OS Tests
echo ====================================
echo.

echo Test 1: Groq Provider
python tests\integration\test_groq.py
if errorlevel 1 (
    echo FAILED
    pause
    exit /b 1
)

echo.
echo Test 2: Provider Configuration
python tests\integration\test_providers.py
if errorlevel 1 (
    echo FAILED
    pause
    exit /b 1
)

echo.
echo Test 3: Integration
python tests\integration\test_integration.py
if errorlevel 1 (
    echo FAILED
    pause
    exit /b 1
)

echo.
echo Test 4: CLI Bypass
python tests\cli\test_bypass.py
if errorlevel 1 (
    echo FAILED
    pause
    exit /b 1
)

echo.
echo Test 5: Dynamic Configuration
python tests\config\test_dynamic_config.py
if errorlevel 1 (
    echo FAILED
    pause
    exit /b 1
)

echo.
echo ====================================
echo ALL TESTS PASSED (5/5)
echo ====================================
pause

endlocal
