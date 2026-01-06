# LLM Layer Documentation

## Overview

The LLM Layer provides multi-provider language model support with intelligent routing, fallback chains, and context management.

## Components

### LLM Router (`llm/router.py`)

The router manages multiple LLM providers and intelligently selects the best one for each request.

```python
from llm_os.llm.router import LLMRouter, RouterConfig

# Create router with config
config = RouterConfig(
    default_provider="ollama",
    fallback_chain=["ollama", "anthropic", "openai"],
    local_first=True,
    cost_optimization=True,
)

router = LLMRouter(config=config)
await router.initialize()

# Make a request
response = await router.complete(
    messages=[Message.user("Hello!")],
    tools=tools,
    task_type=TaskType.SIMPLE,
)
```

**Features:**
- Automatic provider selection based on task complexity
- Fallback to next provider on failure
- Rate limit handling with retry
- Usage tracking and statistics

### Task Classifier (`llm/classifier.py`)

Classifies user requests to route them to appropriate models.

```python
from llm_os.llm.classifier import TaskClassifier, TaskType

classifier = TaskClassifier()
result = classifier.classify("Write a Python function to sort a list")

print(result.task_type)      # TaskType.MODERATE
print(result.confidence)     # 0.85
print(result.suggested_tier) # "default"
```

**Task Types:**

| Type | Description | Model Tier |
|------|-------------|------------|
| SIMPLE | Basic queries, greetings | fast |
| MODERATE | Standard tasks | default |
| COMPLEX | Multi-step, code generation | best |
| REASONING | Logic, math, analysis | reasoning |
| CREATIVE | Writing, brainstorming | default |

### Providers (`llm/providers/`)

#### OllamaProvider

Local LLM support via Ollama.

```python
from llm_os.llm.providers.ollama import OllamaProvider

provider = OllamaProvider(
    base_url="http://localhost:11434",
    default_model="llama3.2:3b",
)

# Check health
is_healthy = await provider.check_health()

# Complete
response = await provider.complete(
    messages=messages,
    model="llama3.2:3b",
)

# Stream
async for chunk in provider.stream(messages=messages):
    print(chunk.content, end="")
```

**Model Tiers:**
- `fast`: llama3.2:1b
- `default`: llama3.2:3b
- `best`: llama3.2:3b
- `reasoning`: deepseek-r1:1.5b

#### AnthropicProvider

Claude API support.

```python
from llm_os.llm.providers.anthropic import AnthropicProvider

provider = AnthropicProvider(
    api_key=os.environ["ANTHROPIC_API_KEY"],
)

response = await provider.complete(
    messages=messages,
    tools=tools,  # Tool calling supported
    model="claude-3-5-haiku-latest",
)
```

**Model Tiers:**
- `fast`: claude-3-5-haiku-latest
- `default`: claude-3-5-haiku-latest
- `best`: claude-sonnet-4-20250514
- `reasoning`: claude-sonnet-4-20250514

#### OpenAIProvider

OpenAI API support (also works with Groq, Together AI).

```python
from llm_os.llm.providers.openai import OpenAIProvider

provider = OpenAIProvider(
    api_key=os.environ["OPENAI_API_KEY"],
)

response = await provider.complete(
    messages=messages,
    tools=tools,
    model="gpt-4o-mini",
)
```

**Model Tiers:**
- `fast`: gpt-4o-mini
- `default`: gpt-4o-mini
- `best`: gpt-4o
- `reasoning`: o1-mini

### Context Manager (`llm/context.py`)

Manages conversation history and context.

```python
from llm_os.llm.context import ContextManager

context = ContextManager(
    max_tokens=8000,
    max_messages=100,
    system_prompt="You are a helpful assistant.",
    persist_path=Path("~/.llm-os/history.json"),
)

# Add messages
context.add_user_message("Open firefox")
context.add_assistant_message("Launching Firefox...")
context.add_tool_result("tool_123", "Firefox launched", "launch_app")

# Get messages for LLM
messages = context.get_messages_for_llm()

# Reference resolution
resolved = context.resolve_references("delete it")
# "delete it" -> "delete firefox"
```

**Features:**
- Automatic token trimming
- Reference resolution ("it", "that", "the file")
- Working directory tracking
- History persistence
- Efficient message deque

### Base Types (`llm/base.py`)

Core type definitions.

```python
from llm_os.llm.base import (
    Message,
    MessageRole,
    ToolCall,
    ToolDefinition,
    LLMResponse,
    StreamChunk,
)

# Create messages
user_msg = Message.user("Hello")
assistant_msg = Message.assistant("Hi there!")
system_msg = Message.system("You are helpful.")
tool_msg = Message.tool_result("id", "result", "tool_name")

# Response structure
response = LLMResponse(
    content="Here's the answer...",
    tool_calls=[ToolCall(id="1", name="read_file", arguments={"path": "test.txt"})],
    model="llama3.2:3b",
    provider="ollama",
    input_tokens=100,
    output_tokens=50,
)
```

## Routing Logic

### Provider Selection

```python
def _select_provider(self, task_type: TaskType) -> str:
    # Local first preference
    if self.config.local_first and "ollama" in self._providers:
        # Complex tasks -> prefer cloud
        if task_type in (TaskType.COMPLEX, TaskType.REASONING):
            if "anthropic" in self._providers:
                return "anthropic"
        return "ollama"

    # Cost optimization
    if self.config.cost_optimization:
        if task_type == TaskType.SIMPLE:
            if "ollama" in self._providers:
                return "ollama"

    return self.config.default_provider
```

### Fallback Chain

```
Request → Provider 1 → Success ✓
              ↓ (failure)
         Provider 2 → Success ✓
              ↓ (failure)
         Provider 3 → Success ✓
              ↓ (failure)
         Error: All providers failed
```

## Configuration

```yaml
# config.yaml
default_provider: ollama
local_first: true
cost_optimization: true

ollama:
  enabled: true
  base_url: http://localhost:11434
  default_model: llama3.2:3b

anthropic:
  enabled: true
  api_key: ${ANTHROPIC_API_KEY}
  default_model: claude-3-5-haiku-latest

openai:
  enabled: true
  api_key: ${OPENAI_API_KEY}
  default_model: gpt-4o-mini
```
