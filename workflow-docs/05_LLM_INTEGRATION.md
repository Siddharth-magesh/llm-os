# LLM-OS: LLM Integration Guide

## Overview

This document covers the integration of Large Language Models (LLMs) into LLM-OS, including local model deployment, cloud API integration, model selection strategies, and the LLM router architecture.

---

## 1. LLM Integration Architecture

### 1.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LLM Router Layer                             │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Model        │  │ Request      │  │ Response                 │  │
│  │ Selector     │  │ Formatter    │  │ Handler                  │  │
│  │              │  │              │  │                          │  │
│  │ - Cost       │  │ - System     │  │ - Parse tool calls       │  │
│  │ - Speed      │  │   prompt     │  │ - Handle streaming       │  │
│  │ - Capability │  │ - Context    │  │ - Error recovery         │  │
│  │ - Fallback   │  │ - Tools      │  │                          │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│         │                 │                     │                   │
│         ▼                 ▼                     ▼                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     Provider Adapters                         │  │
│  │                                                               │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │  │
│  │  │ Ollama  │  │ Claude  │  │ OpenAI  │  │ Other Providers │ │  │
│  │  │ (Local) │  │  API    │  │   API   │  │ (Groq, etc.)    │ │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────────────┘ │  │
│  │                                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

1. **Provider Agnostic**: Same interface for all LLM providers
2. **Fallback Support**: Automatic failover to backup models
3. **Cost Optimization**: Route based on task complexity
4. **Local First**: Prefer local models when suitable
5. **Streaming**: Real-time response display

---

## 2. Local LLM Integration

### 2.1 Ollama (Primary Local Provider)

#### Installation

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service (usually auto-starts)
sudo systemctl enable ollama
sudo systemctl start ollama

# Verify installation
ollama --version
```

#### Model Selection for RTX 3050 (4GB VRAM)

| Model | Size | VRAM Usage | Speed | Capability | Recommended |
|-------|------|------------|-------|------------|-------------|
| `llama3.2:1b` | 1.3GB | 2GB | ⭐⭐⭐⭐⭐ | ⭐⭐ | Quick tasks |
| `llama3.2:3b` | 2.0GB | 3GB | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ Default |
| `qwen2.5:3b` | 1.9GB | 2.5GB | ⭐⭐⭐⭐ | ⭐⭐⭐ | Alternative |
| `phi3:mini` | 2.3GB | 3GB | ⭐⭐⭐⭐ | ⭐⭐⭐ | Reasoning |
| `deepseek-r1:1.5b` | 1.1GB | 1.5GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Reasoning |
| `mistral:7b` | 4.1GB | 5GB* | ⭐⭐⭐ | ⭐⭐⭐⭐ | CPU offload |

*Requires CPU offloading with 4GB VRAM

#### Pull Recommended Models

```bash
# Essential models
ollama pull llama3.2:3b     # Default model
ollama pull llama3.2:1b     # Fast fallback
ollama pull deepseek-r1:1.5b  # For reasoning tasks

# Optional (if you have more VRAM)
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
```

#### Ollama API Integration

```python
import ollama
from typing import Generator

class OllamaProvider:
    """Ollama local LLM provider"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.default_model = "llama3.2:3b"

    async def complete(
        self,
        messages: list[dict],
        model: str | None = None,
        tools: list[dict] | None = None,
        stream: bool = True
    ) -> dict | Generator:
        """Generate completion from Ollama"""
        model = model or self.default_model

        response = ollama.chat(
            model=model,
            messages=messages,
            tools=tools,
            stream=stream
        )

        if stream:
            return self._stream_response(response)
        return response

    def _stream_response(self, response) -> Generator:
        """Stream response chunks"""
        for chunk in response:
            if 'message' in chunk:
                yield chunk['message'].get('content', '')

    async def list_models(self) -> list[str]:
        """List available models"""
        models = ollama.list()
        return [m['name'] for m in models.get('models', [])]

    async def check_health(self) -> bool:
        """Check if Ollama is running"""
        try:
            ollama.list()
            return True
        except Exception:
            return False
```

### 2.2 llama.cpp (Alternative - Maximum Performance)

For users wanting maximum control:

```bash
# Clone and build
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make LLAMA_CUDA=1  # For NVIDIA GPU

# Download a model (GGUF format)
# Example: from huggingface.co

# Run server
./llama-server -m models/llama-3.2-3b.gguf --port 8080
```

#### llama.cpp Integration

```python
import httpx

class LlamaCppProvider:
    """llama.cpp server provider"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    async def complete(
        self,
        messages: list[dict],
        stream: bool = True
    ) -> dict:
        """Generate completion"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "messages": messages,
                    "stream": stream
                }
            )
            return response.json()
```

### 2.3 vLLM (Production - High Performance)

For production with better GPU (8GB+ VRAM):

```bash
pip install vllm

# Start server
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.2-3B-Instruct \
    --port 8000
```

---

## 3. Cloud LLM Integration

### 3.1 Anthropic Claude

#### Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY="your-api-key"
```

#### Integration

```python
from anthropic import Anthropic, AsyncAnthropic

class ClaudeProvider:
    """Anthropic Claude API provider"""

    def __init__(self, api_key: str | None = None):
        self.client = AsyncAnthropic(api_key=api_key)
        self.default_model = "claude-3-5-haiku-latest"

    async def complete(
        self,
        messages: list[dict],
        model: str | None = None,
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        stream: bool = True
    ) -> dict:
        """Generate completion from Claude"""
        model = model or self.default_model

        # Convert tools to Claude format
        claude_tools = self._convert_tools(tools) if tools else None

        if stream:
            return await self._stream_complete(
                messages, model, claude_tools, max_tokens
            )

        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            tools=claude_tools
        )
        return self._parse_response(response)

    async def _stream_complete(
        self,
        messages: list[dict],
        model: str,
        tools: list[dict] | None,
        max_tokens: int
    ):
        """Stream completion"""
        async with self.client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            tools=tools
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert MCP tools to Claude format"""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["inputSchema"]
            }
            for tool in tools
        ]

    def _parse_response(self, response) -> dict:
        """Parse Claude response"""
        result = {
            "content": "",
            "tool_calls": []
        }

        for block in response.content:
            if block.type == "text":
                result["content"] += block.text
            elif block.type == "tool_use":
                result["tool_calls"].append({
                    "name": block.name,
                    "arguments": block.input
                })

        return result

    @property
    def available_models(self) -> list[dict]:
        return [
            {"id": "claude-3-5-haiku-latest", "type": "fast", "cost": "low"},
            {"id": "claude-3-5-sonnet-latest", "type": "balanced", "cost": "medium"},
            {"id": "claude-sonnet-4-20250514", "type": "best", "cost": "medium"},
        ]
```

### 3.2 OpenAI

#### Setup

```bash
pip install openai
export OPENAI_API_KEY="your-api-key"
```

#### Integration

```python
from openai import AsyncOpenAI

class OpenAIProvider:
    """OpenAI API provider"""

    def __init__(self, api_key: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key)
        self.default_model = "gpt-4o-mini"

    async def complete(
        self,
        messages: list[dict],
        model: str | None = None,
        tools: list[dict] | None = None,
        stream: bool = True
    ) -> dict:
        """Generate completion from OpenAI"""
        model = model or self.default_model

        # Convert tools to OpenAI format
        openai_tools = self._convert_tools(tools) if tools else None

        if stream:
            return self._stream_complete(messages, model, openai_tools)

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=openai_tools
        )
        return self._parse_response(response)

    async def _stream_complete(
        self,
        messages: list[dict],
        model: str,
        tools: list[dict] | None
    ):
        """Stream completion"""
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert MCP tools to OpenAI format"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            }
            for tool in tools
        ]

    def _parse_response(self, response) -> dict:
        """Parse OpenAI response"""
        message = response.choices[0].message
        result = {
            "content": message.content or "",
            "tool_calls": []
        }

        if message.tool_calls:
            for tc in message.tool_calls:
                result["tool_calls"].append({
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments)
                })

        return result

    @property
    def available_models(self) -> list[dict]:
        return [
            {"id": "gpt-4o-mini", "type": "fast", "cost": "low"},
            {"id": "gpt-4o", "type": "balanced", "cost": "medium"},
            {"id": "o1", "type": "reasoning", "cost": "high"},
        ]
```

### 3.3 Other Providers

#### Groq (Ultra-Fast Inference)

```python
from openai import AsyncOpenAI

class GroqProvider:
    """Groq API provider (OpenAI compatible)"""

    def __init__(self, api_key: str | None = None):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.default_model = "llama-3.2-3b-preview"

    # Same interface as OpenAIProvider...
```

#### Together AI

```python
class TogetherProvider:
    """Together AI provider (OpenAI compatible)"""

    def __init__(self, api_key: str | None = None):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.together.xyz/v1"
        )
        self.default_model = "meta-llama/Llama-3.2-3B-Instruct-Turbo"
```

---

## 4. LLM Router

### 4.1 Router Architecture

```python
from enum import Enum
from dataclasses import dataclass
from typing import Protocol

class TaskType(Enum):
    SIMPLE = "simple"          # Basic commands
    MODERATE = "moderate"       # Multi-step tasks
    COMPLEX = "complex"         # Complex reasoning
    CREATIVE = "creative"       # Creative tasks

@dataclass
class RouterConfig:
    """LLM Router configuration"""
    default_provider: str = "ollama"
    fallback_provider: str = "claude"
    local_first: bool = True
    cost_optimization: bool = True
    max_retries: int = 3

class LLMProvider(Protocol):
    """Protocol for LLM providers"""
    async def complete(
        self,
        messages: list[dict],
        model: str | None,
        tools: list[dict] | None,
        stream: bool
    ) -> dict: ...

    async def check_health(self) -> bool: ...

class LLMRouter:
    """Routes requests to appropriate LLM providers"""

    def __init__(self, config: RouterConfig):
        self.config = config
        self.providers: dict[str, LLMProvider] = {}
        self._init_providers()

    def _init_providers(self):
        """Initialize available providers"""
        # Local providers
        self.providers["ollama"] = OllamaProvider()

        # Cloud providers (if API keys available)
        if os.getenv("ANTHROPIC_API_KEY"):
            self.providers["claude"] = ClaudeProvider()

        if os.getenv("OPENAI_API_KEY"):
            self.providers["openai"] = OpenAIProvider()

        if os.getenv("GROQ_API_KEY"):
            self.providers["groq"] = GroqProvider()

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        task_type: TaskType = TaskType.SIMPLE,
        preferred_provider: str | None = None,
        stream: bool = True
    ) -> dict:
        """Route request to appropriate provider"""

        # Select provider
        provider_name = preferred_provider or self._select_provider(task_type)
        provider = self.providers.get(provider_name)

        if not provider:
            # Fallback to default
            provider_name = self.config.default_provider
            provider = self.providers.get(provider_name)

        if not provider:
            raise ValueError("No LLM providers available")

        # Try with fallback
        for attempt in range(self.config.max_retries):
            try:
                # Check provider health
                if not await provider.check_health():
                    raise ConnectionError(f"{provider_name} is not available")

                # Get completion
                return await provider.complete(
                    messages=messages,
                    model=self._get_model_for_task(provider_name, task_type),
                    tools=tools,
                    stream=stream
                )

            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    # Try fallback provider
                    provider_name = self._get_fallback(provider_name)
                    provider = self.providers.get(provider_name)
                    if not provider:
                        raise
                else:
                    raise

    def _select_provider(self, task_type: TaskType) -> str:
        """Select best provider for task type"""

        if self.config.local_first:
            # Check if local is available
            if "ollama" in self.providers:
                # For complex tasks, might need cloud
                if task_type == TaskType.COMPLEX:
                    if "claude" in self.providers:
                        return "claude"
                return "ollama"

        if self.config.cost_optimization:
            # Use cheapest available
            if "ollama" in self.providers:
                return "ollama"
            if "groq" in self.providers:
                return "groq"

        return self.config.default_provider

    def _get_model_for_task(
        self,
        provider: str,
        task_type: TaskType
    ) -> str:
        """Get appropriate model for task complexity"""

        model_map = {
            "ollama": {
                TaskType.SIMPLE: "llama3.2:1b",
                TaskType.MODERATE: "llama3.2:3b",
                TaskType.COMPLEX: "llama3.2:3b",
                TaskType.CREATIVE: "llama3.2:3b"
            },
            "claude": {
                TaskType.SIMPLE: "claude-3-5-haiku-latest",
                TaskType.MODERATE: "claude-3-5-haiku-latest",
                TaskType.COMPLEX: "claude-3-5-sonnet-latest",
                TaskType.CREATIVE: "claude-3-5-sonnet-latest"
            },
            "openai": {
                TaskType.SIMPLE: "gpt-4o-mini",
                TaskType.MODERATE: "gpt-4o-mini",
                TaskType.COMPLEX: "gpt-4o",
                TaskType.CREATIVE: "gpt-4o"
            }
        }

        return model_map.get(provider, {}).get(task_type, "default")

    def _get_fallback(self, current: str) -> str:
        """Get fallback provider"""
        fallback_chain = ["ollama", "claude", "openai", "groq"]

        try:
            idx = fallback_chain.index(current)
            for provider in fallback_chain[idx + 1:]:
                if provider in self.providers:
                    return provider
        except ValueError:
            pass

        return self.config.fallback_provider

    async def list_available_providers(self) -> list[dict]:
        """List all available providers with status"""
        result = []
        for name, provider in self.providers.items():
            healthy = await provider.check_health()
            result.append({
                "name": name,
                "available": healthy,
                "type": "local" if name == "ollama" else "cloud"
            })
        return result
```

### 4.2 Task Classification

```python
import re

class TaskClassifier:
    """Classify user requests by complexity"""

    SIMPLE_PATTERNS = [
        r"open\s+\w+",
        r"list\s+(files|directory)",
        r"what\s+time",
        r"show\s+\w+",
    ]

    COMPLEX_PATTERNS = [
        r"set\s+up",
        r"configure",
        r"create\s+.+\s+project",
        r"explain\s+.+\s+in\s+detail",
        r"analyze",
        r"debug",
    ]

    def classify(self, user_input: str) -> TaskType:
        """Classify user input into task type"""
        input_lower = user_input.lower()

        # Check for complex patterns
        for pattern in self.COMPLEX_PATTERNS:
            if re.search(pattern, input_lower):
                return TaskType.COMPLEX

        # Check for simple patterns
        for pattern in self.SIMPLE_PATTERNS:
            if re.search(pattern, input_lower):
                return TaskType.SIMPLE

        # Check length and complexity indicators
        word_count = len(user_input.split())

        if word_count < 5:
            return TaskType.SIMPLE
        elif word_count < 15:
            return TaskType.MODERATE
        else:
            return TaskType.COMPLEX
```

---

## 5. Context Management

### 5.1 Conversation Context

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

@dataclass
class Message:
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)

class ConversationManager:
    """Manages conversation history and context"""

    def __init__(self, max_tokens: int = 8000):
        self.messages: list[Message] = []
        self.max_tokens = max_tokens
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        return """You are the AI assistant for LLM-OS, an operating system controlled through natural language.

Your capabilities:
- Execute system commands through MCP tools
- Manage files and directories
- Launch and control applications
- Browse the web
- Perform development tasks (git, code, etc.)

Guidelines:
1. Be concise but helpful
2. Explain what you're doing before executing
3. Ask for confirmation before destructive operations
4. Handle errors gracefully
5. Remember context from earlier in the conversation

Current session started: {timestamp}
"""

    def add_message(self, role: str, content: str, **kwargs) -> None:
        """Add message to history"""
        self.messages.append(Message(role=role, content=content, **kwargs))
        self._trim_context()

    def _trim_context(self) -> None:
        """Trim context to fit within token limit"""
        # Simple token estimation (4 chars = 1 token)
        while self._estimate_tokens() > self.max_tokens:
            # Remove oldest non-system message
            for i, msg in enumerate(self.messages):
                if msg.role != "system":
                    self.messages.pop(i)
                    break

    def _estimate_tokens(self) -> int:
        """Estimate token count"""
        total_chars = sum(len(m.content) for m in self.messages)
        return total_chars // 4

    def get_messages_for_llm(self) -> list[dict]:
        """Get messages in format for LLM"""
        result = [{"role": "system", "content": self.system_prompt}]

        for msg in self.messages:
            message_dict = {"role": msg.role, "content": msg.content}

            if msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls

            result.append(message_dict)

        return result

    def get_last_referenced_items(self) -> dict:
        """Extract recently referenced items for pronoun resolution"""
        references = {
            "files": [],
            "directories": [],
            "applications": [],
            "urls": []
        }

        # Scan recent messages for references
        for msg in reversed(self.messages[-5:]):
            # Extract file paths
            files = re.findall(r'/[\w/.-]+\.\w+', msg.content)
            references["files"].extend(files)

            # Extract URLs
            urls = re.findall(r'https?://\S+', msg.content)
            references["urls"].extend(urls)

        return references
```

---

## 6. System Prompt Engineering

### 6.1 Main System Prompt

```python
SYSTEM_PROMPT = """You are the AI core of LLM-OS, a natural language operating system.

# Your Role
You translate natural language commands into system operations using the available tools.

# Available Tool Categories
- **Filesystem**: Read, write, move, copy, delete files and directories
- **Applications**: Launch, close, and manage applications
- **Browser**: Web browsing and automation
- **Git**: Version control operations
- **System**: System information and management

# Response Guidelines

1. **Be Proactive**: Execute the obvious intent without asking unnecessary questions
   - "open firefox" → Just open Firefox, don't ask "Are you sure?"
   - "show my files" → List the home directory

2. **Ask When Ambiguous**: Only ask for clarification when truly needed
   - "delete the file" → "Which file would you like to delete?"
   - "open the document" → "I see multiple documents. Which one?"

3. **Confirm Destructive Actions**: Always confirm before:
   - Deleting files or directories
   - Modifying system settings
   - Sending messages or emails
   - Installing or removing software

4. **Provide Feedback**: Clearly communicate what you're doing
   - ✓ "Opening Firefox..."
   - ✓ "Created directory 'projects'"
   - ✗ "Done" (too vague)

5. **Handle Errors Gracefully**:
   - Explain what went wrong
   - Suggest alternatives
   - Don't expose technical stack traces

# Context Understanding

- Remember previous commands in the conversation
- Resolve pronouns: "open it" → refers to last mentioned item
- Understand implicit references: "the file" → recently discussed file

# Examples

User: "open firefox and go to github"
Assistant: Opening Firefox... Navigating to github.com... Done!

User: "create a new folder for my python projects"
Assistant: Creating folder 'python-projects' in your home directory... ✓ Created /home/user/python-projects

User: "delete my downloads folder"
Assistant: ⚠️ This will permanently delete /home/user/Downloads and all its contents. Are you sure?

Current Time: {current_time}
Working Directory: {working_directory}
User: {username}
"""
```

### 6.2 Tool-Aware Prompt Enhancement

```python
def build_tool_prompt(tools: list[dict]) -> str:
    """Build prompt section describing available tools"""
    prompt = "\n# Available Tools\n\n"

    for tool in tools:
        prompt += f"## {tool['name']}\n"
        prompt += f"{tool['description']}\n"
        prompt += f"Parameters: {json.dumps(tool['inputSchema']['properties'], indent=2)}\n\n"

    return prompt
```

---

## 7. Error Handling and Fallbacks

### 7.1 Error Types

```python
class LLMError(Exception):
    """Base LLM error"""
    pass

class ProviderUnavailableError(LLMError):
    """Provider is not available"""
    pass

class RateLimitError(LLMError):
    """Rate limit exceeded"""
    pass

class ContextTooLongError(LLMError):
    """Context exceeds model limit"""
    pass

class ToolExecutionError(LLMError):
    """Tool execution failed"""
    pass
```

### 7.2 Error Recovery

```python
class ErrorHandler:
    """Handle LLM errors with user-friendly messages"""

    ERROR_MESSAGES = {
        ProviderUnavailableError: (
            "The AI service is temporarily unavailable. "
            "Trying backup service..."
        ),
        RateLimitError: (
            "Rate limit reached. Please wait a moment before trying again."
        ),
        ContextTooLongError: (
            "Conversation too long. Starting fresh context..."
        )
    }

    async def handle_error(
        self,
        error: Exception,
        router: LLMRouter,
        context: ConversationManager
    ) -> str:
        """Handle error and provide recovery"""

        error_type = type(error)
        message = self.ERROR_MESSAGES.get(
            error_type,
            f"An error occurred: {str(error)}"
        )

        # Recovery actions
        if isinstance(error, ProviderUnavailableError):
            # Try fallback provider
            fallback = router._get_fallback(router.config.default_provider)
            if fallback:
                return f"{message} Using {fallback}..."

        elif isinstance(error, ContextTooLongError):
            # Clear old context
            context.messages = context.messages[-5:]
            return f"{message} Keeping only recent messages."

        return message
```

---

## 8. Configuration

### 8.1 LLM Configuration File

```yaml
# /etc/llm-os/llm-config.yaml

# Provider settings
providers:
  ollama:
    enabled: true
    base_url: "http://localhost:11434"
    default_model: "llama3.2:3b"
    models:
      fast: "llama3.2:1b"
      default: "llama3.2:3b"
      reasoning: "deepseek-r1:1.5b"

  claude:
    enabled: true
    # API key from environment: ANTHROPIC_API_KEY
    default_model: "claude-3-5-haiku-latest"
    models:
      fast: "claude-3-5-haiku-latest"
      default: "claude-3-5-haiku-latest"
      best: "claude-3-5-sonnet-latest"

  openai:
    enabled: true
    # API key from environment: OPENAI_API_KEY
    default_model: "gpt-4o-mini"

# Router settings
router:
  default_provider: "ollama"
  fallback_provider: "claude"
  local_first: true
  cost_optimization: true
  max_retries: 3

# Context settings
context:
  max_tokens: 8000
  keep_messages: 50

# Performance settings
performance:
  streaming: true
  timeout: 30
  concurrent_tools: 3
```

### 8.2 User Configuration Override

```yaml
# ~/.config/llm-os/llm.yaml

# User preferences
preferences:
  default_provider: "claude"  # Override system default
  always_stream: true
  verbose_output: false

# Custom models
models:
  ollama:
    default: "qwen2.5:7b"  # If user has more VRAM
```

---

## 9. Monitoring and Logging

### 9.1 Usage Tracking

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LLMUsage:
    """Track LLM usage"""
    timestamp: datetime
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    success: bool
    error: str | None = None

class UsageTracker:
    """Track and report LLM usage"""

    def __init__(self):
        self.usage_log: list[LLMUsage] = []

    def log_request(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        success: bool = True,
        error: str | None = None
    ):
        """Log a request"""
        self.usage_log.append(LLMUsage(
            timestamp=datetime.now(),
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=success,
            error=error
        ))

    def get_summary(self) -> dict:
        """Get usage summary"""
        if not self.usage_log:
            return {"total_requests": 0}

        return {
            "total_requests": len(self.usage_log),
            "successful": sum(1 for u in self.usage_log if u.success),
            "failed": sum(1 for u in self.usage_log if not u.success),
            "total_tokens": sum(u.input_tokens + u.output_tokens for u in self.usage_log),
            "avg_latency_ms": sum(u.latency_ms for u in self.usage_log) / len(self.usage_log),
            "by_provider": self._group_by_provider()
        }

    def _group_by_provider(self) -> dict:
        """Group usage by provider"""
        from collections import defaultdict
        groups = defaultdict(lambda: {"requests": 0, "tokens": 0})

        for usage in self.usage_log:
            groups[usage.provider]["requests"] += 1
            groups[usage.provider]["tokens"] += usage.input_tokens + usage.output_tokens

        return dict(groups)
```

---

## 10. Testing

### 10.1 Provider Tests

```python
import pytest

@pytest.mark.asyncio
async def test_ollama_provider():
    """Test Ollama provider"""
    provider = OllamaProvider()

    # Check health
    assert await provider.check_health()

    # Test completion
    response = await provider.complete(
        messages=[{"role": "user", "content": "Say hello"}],
        stream=False
    )

    assert response["message"]["content"]

@pytest.mark.asyncio
async def test_router_fallback():
    """Test router fallback mechanism"""
    config = RouterConfig(
        default_provider="fake_provider",
        fallback_provider="ollama"
    )
    router = LLMRouter(config)

    # Should fallback to ollama
    response = await router.complete(
        messages=[{"role": "user", "content": "Hello"}]
    )

    assert response
```

---

## References

- [Ollama Documentation](https://ollama.com/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [vLLM Documentation](https://docs.vllm.ai/)
- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)

---

*Document Version: 1.0*
*Last Updated: January 2026*
