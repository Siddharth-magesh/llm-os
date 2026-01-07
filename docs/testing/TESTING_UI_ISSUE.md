# Testing UI Black Screen Issue

**Date:** January 7, 2026

---

## 🔍 Problem Description

When running `llm-os.exe`, the system shows:
1. ✅ Initial batch script output
2. ✅ "Starting LLM-OS TUI..." message
3. ❌ Black screen appears when TUI tries to launch
4. ❌ Application seems to hang or not display properly

---

## 🧪 Diagnostic Testing Procedure

Run these tests **IN ORDER** to isolate the problem:

### **Test 1: Minimal Textual Test** (Most Basic)

**Purpose:** Verify Textual TUI library works on your system

**Run:**
```
test-ui-minimal.bat
```

**What to expect:**
- A TUI should open with a green box
- Text should say "✅ Textual UI is Working!"
- Press 'q' to exit

**If this FAILS:**
- ❌ Textual library has an issue on your system
- Possible solutions:
  - Reinstall Textual: `pip install --force-reinstall textual`
  - Check terminal compatibility
  - Try a different terminal (PowerShell vs CMD vs Windows Terminal)

**If this WORKS:**
- ✅ Textual is fine, issue is in LLM-OS code
- Proceed to Test 2

---

### **Test 2: Standalone UI Test** (No MCP)

**Purpose:** Test LLM-OS UI components without MCP or LLM initialization

**Run:**
```
test-ui-standalone.bat
```

**What to expect:**
- LLM-OS TUI opens with welcome banner
- Status bar shows "TEST MODE | Mock Handler | 0 tools"
- You can type messages and get mock responses
- Streaming works (word-by-word display)
- Press Ctrl+D to exit

**If this FAILS:**
- ❌ Issue is in the UI code (app.py or widgets.py)
- Check the error message
- Possible issues:
  - Import errors in ui/app.py
  - Widget rendering issues
  - Async event loop problems

**If this WORKS:**
- ✅ UI code is fine, issue is in MCP/LLM initialization
- Proceed to Test 3

---

### **Test 3: Initialization Diagnostic**

**Purpose:** Test each initialization step to find where it hangs

**Run:**
```
test-init-diagnostic.bat
```

**What to expect:**
You should see 4 tests run:
1. ✅ Imports - All imports load successfully
2. ✅ LLMOS Creation - Instance created
3. ✅ LLMOS Initialization - MCP servers register (THIS IS WHERE IT MIGHT HANG)
4. ✅ Simple Query - Test query works

**Watch for:**
- Which test fails or hangs?
- Any error messages?
- Does it timeout?

**If Test 3 HANGS:**
- ❌ MCP initialization is blocking
- Possible causes:
  - External MCP servers trying to start (should be disabled now)
  - Network timeout waiting for Ollama
  - Deadlock in async initialization

**If Test 3 PASSES:**
- ✅ Everything works in CLI mode
- ❌ Issue is specifically with TUI event loop integration
- Problem is in `cli.py` `run_tui()` function

---

## 🔧 Common Issues and Solutions

### Issue 1: External MCP Server Errors
**Symptoms:** Errors about "Failed to start MCP server: [WinError 2]"

**Solution:**
✅ Already fixed! Check that `core.py` line 116 has:
```python
use_external_servers: bool = False
```

---

### Issue 2: Ollama Not Running
**Symptoms:** Timeout errors, "Connection refused"

**Check:**
```bash
ollama ps
```

**Solution:**
Start Ollama if it's not running

---

### Issue 3: Textual Library Issue
**Symptoms:** Test 1 (minimal) fails with black screen

**Solution:**
```bash
# Reinstall Textual
pip install --force-reinstall textual

# Try updating
pip install --upgrade textual
```

---

### Issue 4: Terminal Compatibility
**Symptoms:** Renders weirdly or not at all

**Try different terminals:**
- Windows Terminal (recommended)
- PowerShell
- CMD
- Git Bash

---

### Issue 5: Async Event Loop Conflict
**Symptoms:** Hangs when TUI tries to start, but diagnostic passes

**Location:** `cli.py` line 226-271 in `run_tui()` function

**Check:**
- Is `await app.run_async()` being called? (line 270)
- Is initialization happening before TUI starts?
- Any blocking calls before TUI launch?

---

## 📊 Test Results Template

Fill this out as you run tests:

```
Test 1 - Minimal Textual:     [ ] PASS  [ ] FAIL
  - Green box appeared:        [ ] YES   [ ] NO
  - Could exit with 'q':       [ ] YES   [ ] NO
  - Error message: ___________________________________________

Test 2 - Standalone UI:       [ ] PASS  [ ] FAIL
  - TUI opened:                [ ] YES   [ ] NO
  - Could type messages:       [ ] YES   [ ] NO
  - Streaming worked:          [ ] YES   [ ] NO
  - Error message: ___________________________________________

Test 3 - Initialization:      [ ] PASS  [ ] FAIL
  - Imports OK:                [ ] YES   [ ] NO
  - LLMOS Creation OK:         [ ] YES   [ ] NO
  - LLMOS Init OK:             [ ] YES   [ ] NO
  - Simple Query OK:           [ ] YES   [ ] NO
  - Hung at step: _____________
  - Error message: ___________________________________________

Full llm-os.exe:              [ ] PASS  [ ] FAIL
  - TUI opened:                [ ] YES   [ ] NO
  - Black screen appeared:     [ ] YES   [ ] NO
  - Error message: ___________________________________________
```

---

## 🎯 Next Steps Based on Results

### Scenario A: Test 1 Fails
**Problem:** Textual library or terminal issue
**Action:** Reinstall Textual, try different terminal

### Scenario B: Test 1 Pass, Test 2 Fails
**Problem:** UI code issue (app.py or widgets.py)
**Action:** Check error message, review UI code changes

### Scenario C: Test 1 & 2 Pass, Test 3 Hangs at Init
**Problem:** MCP initialization blocking
**Action:** Check MCP orchestrator, verify external servers disabled

### Scenario D: All Tests Pass, Only Full App Fails
**Problem:** TUI event loop integration in cli.py
**Action:** Review `run_tui()` function, check async flow

---

## 🐛 Detailed Debugging

If tests don't identify the issue, run with maximum verbosity:

```bash
C:\Users\Siddharth\miniconda3\envs\llm-os\Scripts\llm-os.exe -vv > debug.log 2>&1
```

Then check `debug.log` for:
- Where does logging stop?
- Last successful operation?
- Any error messages?
- Timeout indicators?

---

## 📝 Files Created for Testing

1. **test_ui_minimal.py** - Bare bones Textual test
2. **test_ui_standalone.py** - UI test without MCP
3. **test_init_diagnostic.py** - Step-by-step initialization test
4. **test-ui-minimal.bat** - Run minimal test
5. **test-ui-standalone.bat** - Run standalone UI test
6. **test-init-diagnostic.bat** - Run diagnostic test

---

## 🚀 Running Tests

**Easy Mode - Double-click these files:**
1. `test-ui-minimal.bat` (Test 1)
2. `test-ui-standalone.bat` (Test 2)
3. `test-init-diagnostic.bat` (Test 3)

**Command Line:**
```bash
# Test 1
python D:\llm-os\test_ui_minimal.py

# Test 2
python D:\llm-os\test_ui_standalone.py

# Test 3
python D:\llm-os\test_init_diagnostic.py
```

---

## 💡 Tips

1. **Run tests in order** - Don't skip steps
2. **Note exact error messages** - They're important for debugging
3. **Try different terminals** - Sometimes it's just terminal compatibility
4. **Check Ollama is running** - `ollama ps` should show output
5. **Be patient** - Initialization can take a few seconds

---

## 📞 Reporting Results

When reporting back, please include:
- Which test failed (1, 2, or 3)
- Exact error message
- Where it hung (if applicable)
- Terminal you're using
- Test results template filled out

This will help identify the exact issue quickly!

---

*Testing guide created January 7, 2026*
