# LLM-OS Project Structure

**Organized:** January 7, 2026

---

## 📁 Directory Structure

```
D:\llm-os/
├── llm_os/                    # Main source code
│   ├── config/                # Configuration files
│   │   └── default.yaml       # Default configuration
│   ├── docs/                  # Code documentation
│   ├── src/llm_os/           # Python package
│   │   ├── __init__.py
│   │   ├── __main__.py       # Entry point
│   │   ├── cli.py            # CLI interface
│   │   ├── core.py           # Core LLMOS orchestration
│   │   ├── config.py         # Configuration management
│   │   ├── llm/              # LLM providers & routing
│   │   │   ├── router.py
│   │   │   ├── classifier.py
│   │   │   ├── context.py
│   │   │   └── providers/
│   │   │       ├── ollama.py
│   │   │       ├── anthropic.py
│   │   │       └── openai.py
│   │   ├── mcp/              # Model Context Protocol
│   │   │   ├── orchestrator/
│   │   │   ├── servers/      # Internal Python MCP servers
│   │   │   ├── client/       # External server client
│   │   │   └── types/
│   │   └── ui/               # Textual TUI
│   │       ├── app.py
│   │       └── widgets.py
│   ├── README.md
│   └── TESTING_GUIDE.md
│
├── tests/                     # All tests organized here
│   ├── ui/                    # UI-specific tests
│   │   ├── test_ui_minimal.py         # Minimal Textual test
│   │   ├── test_ui_standalone.py      # UI without MCP/LLM
│   │   └── README.md
│   ├── integration/           # Integration tests
│   │   └── test_init_diagnostic.py    # Initialization diagnostic
│   └── unit/                  # Unit tests (future)
│
├── scripts/                   # Utility scripts
│   ├── run-llm-os.bat        # Main LLM-OS launcher
│   ├── run-llm-os.ps1        # PowerShell launcher
│   └── run-tests-ui.bat      # UI test runner
│
├── docs/                      # Documentation
│   ├── SETUP_COMPLETE.md     # Setup guide
│   ├── UI_FIXES_COMPLETE.md  # UI fixes documentation
│   ├── PATH_FIX_COMPLETE.md  # Path fix guide
│   └── TESTING_UI_ISSUE.md   # UI issue testing guide
│
├── workflow-docs/             # Planning & workflow documentation
│
├── .github/                   # GitHub specific files
│   └── copilot-instructions.md
│
├── run-llm-os.bat            # Quick launcher (menu)
├── README.md                  # Main project README
└── test-config.yaml          # Test configuration
```

---

## 🚀 Quick Start

### Running LLM-OS

**Easy Way:**
```bash
# Double-click
run-llm-os.bat
```

**Direct Way:**
```bash
# Run the TUI
scripts\run-llm-os.bat
```

---

### Running Tests

**UI Tests:**
```bash
# From root
scripts\run-tests-ui.bat

# Or individual tests
C:\Users\Siddharth\miniconda3\envs\llm-os\python.exe tests\ui\test_ui_minimal.py
C:\Users\Siddharth\miniconda3\envs\llm-os\python.exe tests\ui\test_ui_standalone.py
```

**Integration Tests:**
```bash
C:\Users\Siddharth\miniconda3\envs\llm-os\python.exe tests\integration\test_init_diagnostic.py
```

---

## 📂 Key Files

### Configuration
- `llm_os/config/default.yaml` - Main configuration
- `test-config.yaml` - Test configuration (Windows)

### Entry Points
- `llm_os/src/llm_os/__main__.py` - Python module entry
- `llm_os/src/llm_os/cli.py` - CLI interface

### Documentation
- `README.md` - Main project documentation
- `docs/SETUP_COMPLETE.md` - Setup instructions
- `llm_os/docs/` - Code-specific documentation
- `workflow-docs/` - Development workflow docs

### Scripts
- `run-llm-os.bat` - Quick launcher menu
- `scripts/run-llm-os.bat` - Direct TUI launcher
- `scripts/run-tests-ui.bat` - UI test runner

---

## 🧪 Testing

### Test Categories

**UI Tests** (`tests/ui/`)
- Test Textual TUI components
- Verify UI rendering
- Test without MCP/LLM dependencies

**Integration Tests** (`tests/integration/`)
- Test full system initialization
- Test component integration
- Diagnose initialization issues

**Unit Tests** (`tests/unit/`)
- Future: Component-specific unit tests

---

## 📚 Documentation Locations

| Type | Location |
|------|----------|
| Setup guides | `docs/` |
| Code documentation | `llm_os/docs/` |
| Planning docs | `workflow-docs/` |
| Test guides | `tests/*/README.md` |

---

## 🔧 Development

### Adding Tests
1. **UI tests** → `tests/ui/`
2. **Integration tests** → `tests/integration/`
3. **Unit tests** → `tests/unit/`

### Adding Scripts
- Utility scripts → `scripts/`
- Update `run-llm-os.bat` menu if needed

### Adding Documentation
- Setup/user docs → `docs/`
- Code docs → `llm_os/docs/`
- Planning docs → `workflow-docs/`

---

## 🎯 What Goes Where?

### ✅ Root Directory (Keep Clean!)
- `README.md` - Main project readme
- `run-llm-os.bat` - Quick launcher only
- `test-config.yaml` - Test configuration
- `.gitignore`, `.github/` - Git files

### ✅ scripts/
- All batch files (.bat)
- PowerShell scripts (.ps1)
- Utility runners

### ✅ tests/
- All test files (.py)
- Organized by category (ui/, integration/, unit/)
- Each category has its own README

### ✅ docs/
- User documentation (.md)
- Setup guides
- Troubleshooting guides

### ✅ llm_os/
- All source code
- Configuration files
- Code-specific documentation

---

## 🧹 Cleanup Complete

### Removed from Root:
- ❌ `test-ui-minimal.bat`
- ❌ `test-ui-standalone.bat`
- ❌ `test-init-diagnostic.bat`
- ❌ `quick-test.bat`
- ❌ Test Python files

### Moved to Proper Locations:
- ✅ Test batch files → Replaced by `scripts/run-tests-ui.bat`
- ✅ Test Python files → `tests/ui/` and `tests/integration/`
- ✅ Documentation → `docs/`
- ✅ Scripts → `scripts/`

---

## 📋 File Count by Directory

```
llm_os/src/llm_os/    ~30 Python files (source code)
tests/                 3 test files
scripts/               3 script files
docs/                  4 documentation files
Root:                  4 essential files only
```

---

## 🎨 Principles

1. **Clean Root** - Only essential files in root
2. **Organized Tests** - All tests in `tests/` by category
3. **Centralized Scripts** - All runners in `scripts/`
4. **Clear Documentation** - Docs in `docs/` and subdirectories
5. **Easy Navigation** - Clear folder structure
6. **Single Entry Point** - `run-llm-os.bat` menu for everything

---

*Project reorganized January 7, 2026*
