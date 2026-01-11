@echo off
REM Quick verification that everything works

setlocal

set GROQ_API_KEY=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

call "%USERPROFILE%\miniconda3\Scripts\activate.bat" >nul 2>&1
call conda activate llm-os >nul 2>&1

echo ====================================
echo   LLM-OS Verification Test
echo ====================================
echo.
echo Test 1: CLI version
python -m llm_os --version
echo.
echo Test 2: Groq LLM
python -m llm_os -c "Reply with just OK" --no-ui --provider groq
echo.
echo Test 3: File operations (MCP tools)
echo Testing if LLM can list files...
python -m llm_os -c "List all files in the current directory" --no-ui --provider groq
echo.
echo ====================================
echo All tests completed!
echo.
echo If you see a file list above,
echo everything is working correctly!
echo.
echo Launch: launch.bat
echo ====================================
pause

endlocal
