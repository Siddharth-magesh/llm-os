# API Reference

## Core Module

### LLMOS Class

Main orchestration class.

```python
class LLMOS:
    def __init__(
        self,
        config: LLMOSConfig | None = None,
        system_config: Config | None = None,
    ) -> None: ...

    async def initialize(self) -> None:
        """Initialize all components."""

    async def shutdown(self) -> None:
        """Shutdown all components."""

    async def process_message(
        self,
        user_input: str,
        stream: bool = False,
    ) -> str:
        """Process a user message and return response."""

    async def stream_message(
        self,
        user_input: str,
    ) -> AsyncIterator[str]:
        """Stream response chunks."""

    def set_tool_callback(self, callback: callable) -> None:
        """Set callback for tool execution events."""

    def set_confirmation_callback(self, callback: callable) -> None:
        """Set callback for confirmation requests."""

    def clear_context(self) -> None:
        """Clear conversation context."""

    def get_status(self) -> dict[str, Any]:
        """Get current system status."""

    @property
    def current_provider(self) -> str: ...
    @property
    def current_model(self) -> str | None: ...
    @property
    def available_providers(self) -> list[str]: ...
    @property
    def available_tools(self) -> list[Tool]: ...
```

### LLMOSConfig

```python
@dataclass
class LLMOSConfig:
    default_provider: str = "ollama"
    default_model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    max_context_tokens: int = 8000
    max_messages: int = 100
    persist_history: bool = True
    history_path: Path | None = None
    auto_start_servers: bool = True
    security_policy: SecurityPolicy = field(default_factory=SecurityPolicy)
    show_tool_calls: bool = True
    stream_responses: bool = True
```

## LLM Module

### LLMRouter

```python
class LLMRouter:
    def __init__(
        self,
        config: RouterConfig | None = None,
        providers: dict[str, BaseLLMProvider] | None = None,
    ) -> None: ...

    async def initialize(self) -> None: ...
    async def close(self) -> None: ...

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        task_type: TaskType | None = None,
        preferred_provider: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> LLMResponse: ...

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        task_type: TaskType | None = None,
        preferred_provider: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]: ...

    def classify_task(self, user_input: str) -> ClassificationResult: ...
    def get_usage_summary(self) -> dict[str, Any]: ...
```

### Message

```python
@dataclass
class Message:
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None

    @classmethod
    def user(cls, content: str) -> Message: ...
    @classmethod
    def assistant(cls, content: str, tool_calls: list[ToolCall] | None = None) -> Message: ...
    @classmethod
    def system(cls, content: str) -> Message: ...
    @classmethod
    def tool_result(cls, tool_call_id: str, content: str, name: str | None = None) -> Message: ...
```

### LLMResponse

```python
@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
```

### TaskClassifier

```python
class TaskClassifier:
    def classify(self, user_input: str) -> ClassificationResult: ...

class TaskType(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    REASONING = "reasoning"
    CREATIVE = "creative"

@dataclass
class ClassificationResult:
    task_type: TaskType
    confidence: float
    suggested_tier: str
    reasoning: str
```

### ContextManager

```python
class ContextManager:
    def __init__(
        self,
        max_tokens: int = 8000,
        max_messages: int = 100,
        system_prompt: str | None = None,
        persist_path: Path | None = None,
    ) -> None: ...

    def add_user_message(self, content: str) -> Message: ...
    def add_assistant_message(self, content: str, tool_calls: list[ToolCall] | None = None) -> Message: ...
    def add_tool_result(self, tool_call_id: str, content: str, tool_name: str | None = None, is_error: bool = False) -> Message: ...
    def get_messages_for_llm(self) -> list[Message]: ...
    def resolve_references(self, text: str) -> str: ...
    def set_working_directory(self, path: str) -> None: ...
    def estimate_tokens(self) -> int: ...
    def clear(self) -> None: ...
    def get_summary(self) -> dict[str, Any]: ...
```

## MCP Module

### MCPOrchestrator

```python
class MCPOrchestrator:
    def __init__(
        self,
        config: OrchestratorConfig | None = None,
        confirmation_handler: ConfirmationHandler | None = None,
    ) -> None: ...

    async def initialize(self) -> dict[str, bool]: ...
    async def shutdown(self) -> None: ...

    def register_server(self, server: BaseMCPServer) -> None: ...
    def register_builtin_servers(self) -> None: ...

    def get_tools(self) -> list[Tool]: ...
    def get_tools_for_llm(self) -> list[dict[str, Any]]: ...

    async def execute_tool(self, tool_call: ToolCall, timeout: float | None = None) -> ToolResult: ...
    async def execute_tools(self, tool_calls: list[ToolCall], parallel: bool = True) -> dict[str, ToolResult]: ...
    async def call_tool(self, name: str, **arguments: Any) -> ToolResult: ...

    def get_status(self) -> dict[str, Any]: ...
```

### Tool Types

```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    server_id: str = ""
    requires_confirmation: bool = False
    permission_level: str = "read"

    def get_input_schema(self) -> dict[str, Any]: ...
    def to_llm_format(self) -> dict[str, Any]: ...
    def validate_arguments(self, arguments: dict[str, Any]) -> tuple[bool, str]: ...

@dataclass
class ToolParameter:
    name: str
    type: ParameterType
    description: str
    required: bool = True
    default: Any = None
    enum: list[str] | None = None
    items: dict[str, Any] | None = None

@dataclass
class ToolResult:
    success: bool
    content: list[ToolContent]
    is_error: bool = False
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(cls, text: str, **metadata: Any) -> ToolResult: ...
    @classmethod
    def error_result(cls, error: str, **metadata: Any) -> ToolResult: ...
    def get_text(self) -> str: ...

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]
    server_id: str | None = None
```

### BaseMCPServer

```python
class BaseMCPServer(ABC):
    server_id: str = "base"
    server_name: str = "Base Server"
    server_version: str = "1.0.0"
    server_description: str = "Base MCP server"

    def register_tool(
        self,
        name: str,
        description: str,
        handler: ToolHandler,
        parameters: list[ToolParameter] | None = None,
        requires_confirmation: bool = False,
        permission_level: str = "read",
    ) -> None: ...

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult: ...
    async def initialize(self) -> None: ...
    async def shutdown(self) -> None: ...

    @abstractmethod
    def _register_tools(self) -> None: ...

    # Parameter helpers
    @staticmethod
    def string_param(name: str, description: str, required: bool = True, default: str | None = None, enum: list[str] | None = None) -> ToolParameter: ...
    @staticmethod
    def number_param(name: str, description: str, required: bool = True, default: float | None = None) -> ToolParameter: ...
    @staticmethod
    def integer_param(name: str, description: str, required: bool = True, default: int | None = None) -> ToolParameter: ...
    @staticmethod
    def boolean_param(name: str, description: str, required: bool = False, default: bool = False) -> ToolParameter: ...
    @staticmethod
    def array_param(name: str, description: str, item_type: ParameterType = ParameterType.STRING, required: bool = True) -> ToolParameter: ...
```

### SecurityManager

```python
class SecurityManager:
    def __init__(
        self,
        policy: SecurityPolicy | None = None,
        confirmation_handler: ConfirmationHandler | None = None,
    ) -> None: ...

    def check_tool_permission(self, tool: Tool, arguments: dict[str, Any]) -> SecurityCheckResult: ...
    async def execute_with_security(self, tool: Tool, arguments: dict[str, Any], executor: Callable) -> ToolResult: ...
    def get_audit_log(self, limit: int = 100, status_filter: str | None = None) -> list[dict[str, Any]]: ...

@dataclass
class SecurityPolicy:
    require_confirmation_for_write: bool = True
    require_confirmation_for_execute: bool = True
    require_confirmation_for_system: bool = True
    require_confirmation_for_dangerous: bool = True
    sandbox_enabled: bool = True
    sandbox_allowed_paths: list[str] = field(default_factory=list)
    sandbox_blocked_paths: list[str] = field(default_factory=list)
    blocked_commands: list[str] = field(default_factory=list)
    max_operations_per_minute: int = 60
```

## UI Module

### NLShellApp

```python
class NLShellApp(App):
    def __init__(
        self,
        message_handler: MessageHandler | None = None,
        confirmation_handler: Callable | None = None,
        **kwargs: Any,
    ) -> None: ...

    def set_message_handler(self, handler: MessageHandler) -> None: ...
    def update_status(self, provider: str | None = None, model: str | None = None, tool_count: int | None = None) -> None: ...
    def show_tool_progress(self, tool_name: str) -> None: ...
    def hide_tool_progress(self, success: bool = True) -> None: ...
    async def show_confirmation(self, title: str, message: str) -> bool: ...
    def add_message(self, content: str, role: str = MessageRole.ASSISTANT) -> None: ...
    def add_user_message(self, content: str) -> None: ...
    def add_assistant_message(self, content: str) -> None: ...
    def add_system_message(self, content: str) -> None: ...
    def add_error_message(self, content: str) -> None: ...

def run_app(message_handler: MessageHandler | None = None, **kwargs: Any) -> None: ...
```

## CLI Module

### Main Entry Point

```python
def main() -> int:
    """Main CLI entry point."""

# CLI Arguments
parser.add_argument("-c", "--command", help="Execute single command")
parser.add_argument("-p", "--provider", choices=["ollama", "anthropic", "openai"])
parser.add_argument("-m", "--model", help="Specific model")
parser.add_argument("--local-only", action="store_true")
parser.add_argument("--no-ui", action="store_true")
parser.add_argument("--no-stream", action="store_true")
parser.add_argument("--config", type=Path)
parser.add_argument("-v", "--verbose", action="count")
parser.add_argument("--log-file", type=Path)
parser.add_argument("--version", action="version")
```
