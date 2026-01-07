# Development Guide

## Setting Up Development Environment

### Prerequisites

- Python 3.11+
- pip and venv
- Git
- Ollama (optional, for local testing)

### Initial Setup

```bash
# Clone repository
git clone <repository> llm-os
cd llm-os

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Verify installation
python -c "import llm_os; print(llm_os.__version__)"
```

### Development Dependencies

```bash
pip install -e ".[dev]"

# This installs:
# - pytest (testing)
# - pytest-asyncio (async tests)
# - pytest-cov (coverage)
# - black (formatting)
# - ruff (linting)
# - mypy (type checking)
```

## Project Structure

```
llm_os/
├── src/llm_os/          # Main source code
│   ├── llm/             # LLM providers and routing
│   ├── mcp/             # MCP servers and orchestration
│   └── ui/              # Terminal UI
├── tests/               # Test files
├── docs/                # Documentation
└── config/              # Configuration templates
```

## Code Style

### Formatting

```bash
# Format code
black src/

# Check formatting
black --check src/
```

### Linting

```bash
# Run linter
ruff check src/

# Fix auto-fixable issues
ruff check --fix src/
```

### Type Checking

```bash
# Run type checker
mypy src/llm_os/
```

### Pre-commit (Optional)

```bash
pip install pre-commit
pre-commit install

# Now formatting/linting runs on every commit
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=llm_os --cov-report=html

# Run specific test file
pytest tests/test_router.py

# Run specific test
pytest tests/test_router.py::test_fallback_chain

# Verbose output
pytest -v
```

### Writing Tests

```python
# tests/test_example.py
import pytest
from llm_os.llm.classifier import TaskClassifier, TaskType

@pytest.fixture
def classifier():
    return TaskClassifier()

def test_simple_task_classification(classifier):
    result = classifier.classify("hello")
    assert result.task_type == TaskType.SIMPLE

@pytest.mark.asyncio
async def test_async_operation():
    from llm_os.mcp.servers.filesystem import FilesystemServer

    server = FilesystemServer()
    await server.initialize()

    result = await server.call_tool("exists", {"path": "/"})
    assert result.success

    await server.shutdown()
```

### Test Configuration

```ini
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"
```

## Adding New Features

### Adding a New LLM Provider

1. Create provider file:

```python
# src/llm_os/llm/providers/my_provider.py
from llm_os.llm.base import BaseLLMProvider, LLMResponse, Message

class MyProvider(BaseLLMProvider):
    provider_name = "my_provider"

    def __init__(self, api_key: str, base_url: str = "..."):
        self.api_key = api_key
        self.base_url = base_url
        self._client = None

    async def check_health(self) -> bool:
        # Check if provider is available
        ...

    async def complete(self, messages, tools, model, max_tokens, temperature, stream) -> LLMResponse:
        # Generate completion
        ...

    async def stream(self, messages, tools, model, max_tokens, temperature):
        # Stream completion
        ...
```

2. Register in router:

```python
# In llm/router.py
from llm_os.llm.providers.my_provider import MyProvider

# In initialize()
if os.environ.get("MY_PROVIDER_API_KEY"):
    self._providers["my_provider"] = MyProvider(...)
```

### Adding a New MCP Server

1. Create server file:

```python
# src/llm_os/mcp/servers/my_server.py
from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types.tools import ToolResult

class MyServer(BaseMCPServer):
    server_id = "my_server"
    server_name = "My Server"
    server_description = "Does something useful"

    def __init__(self):
        super().__init__()
        self._register_tools()

    def _register_tools(self):
        self.register_tool(
            name="my_tool",
            description="Does something",
            handler=self._my_tool,
            parameters=[
                self.string_param("input", "Input value"),
            ],
            permission_level="read",
        )

    async def _my_tool(self, input: str) -> ToolResult:
        result = process_input(input)
        return ToolResult.success_result(result)
```

2. Register in servers/__init__.py:

```python
from llm_os.mcp.servers.my_server import MyServer

BUILTIN_SERVERS["my_server"] = MyServer
```

3. Register in orchestrator:

```python
# In orchestrator.py register_builtin_servers()
from llm_os.mcp.servers.my_server import MyServer

builtin_servers.append(MyServer)
```

### Adding UI Widgets

```python
# src/llm_os/ui/widgets.py
from textual.widget import Widget
from textual.reactive import reactive

class MyWidget(Widget):
    DEFAULT_CSS = """
    MyWidget {
        padding: 1;
        border: solid $primary;
    }
    """

    value = reactive("")

    def render(self):
        return f"My Widget: {self.value}"

    def update_value(self, new_value: str):
        self.value = new_value
```

## Debugging

### Enable Debug Logging

```bash
# Via CLI
llm-os -vv

# Via environment
export LLM_OS_LOG_LEVEL=DEBUG
llm-os
```

### Debug Specific Components

```python
import logging

# Enable debug for specific module
logging.getLogger("llm_os.llm.router").setLevel(logging.DEBUG)
logging.getLogger("llm_os.mcp.orchestrator").setLevel(logging.DEBUG)
```

### Interactive Debugging

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()
```

## Building and Distribution

### Build Package

```bash
# Install build tool
pip install build

# Build package
python -m build

# Output in dist/
# - llm_os-0.1.0.tar.gz
# - llm_os-0.1.0-py3-none-any.whl
```

### Install from Build

```bash
pip install dist/llm_os-0.1.0-py3-none-any.whl
```

### Publish to PyPI (Future)

```bash
pip install twine
twine upload dist/*
```

## Common Development Tasks

### Update Dependencies

```bash
# Add new dependency
# Edit pyproject.toml, then:
pip install -e ".[dev]"
```

### Run Type Checks

```bash
mypy src/llm_os/ --ignore-missing-imports
```

### Generate Coverage Report

```bash
pytest --cov=llm_os --cov-report=html
open htmlcov/index.html
```

### Profile Performance

```python
import cProfile
import pstats

with cProfile.Profile() as pr:
    # Code to profile
    ...

stats = pstats.Stats(pr)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

## Contributing Guidelines

1. **Fork and Branch**: Create a feature branch
2. **Write Tests**: Add tests for new features
3. **Follow Style**: Run black and ruff
4. **Type Hints**: Add type annotations
5. **Documentation**: Update docs for API changes
6. **Commit Messages**: Use descriptive messages
7. **Pull Request**: Submit PR with description
