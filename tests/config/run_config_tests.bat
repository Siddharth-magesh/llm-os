@echo off
setlocal

set GROQ_API_KEY=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

call "%USERPROFILE%\miniconda3\Scripts\activate.bat" >nul 2>&1
call conda activate llm-os >nul 2>&1

echo ====================================
echo   Configuration Tests
echo ====================================
echo.

echo Test: Dynamic Configuration
python tests\config\test_dynamic_config.py
if errorlevel 1 (
    echo FAILED
    pause
    exit /b 1
)

echo.
echo ====================================
echo CONFIG TESTS PASSED
echo ====================================
pause

endlocal
