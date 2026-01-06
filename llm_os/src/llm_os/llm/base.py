"""
LLM Base Types and Provider Interface

This module defines the core types and abstract base class for LLM providers.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Protocol, runtime_checkable


class MessageRole(str, Enum):
    """Message roles in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]

    def __repr__(self) -> str:
        return f"ToolCall(name={self.name!r}, arguments={self.arguments!r})"


@dataclass
class ToolResult:
    """Result from executing a tool."""
    tool_call_id: str
    content: str
    is_error: bool = False

    def __repr__(self) -> str:
        status = "error" if self.is_error else "success"
        return f"ToolResult({status}, content={self.content[:50]!r}...)"


@dataclass
class Message:
    """A single message in a conversation."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None  # For tool results
    name: str | None = None  # For tool results

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for API calls."""
        result: dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }

        if self.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": tc.arguments,
                    }
                }
                for tc in self.tool_calls
            ]

        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id

        if self.name:
            result["name"] = self.name

        return result

    @classmethod
    def user(cls, content: str) -> Message:
        """Create a user message."""
        return cls(role=MessageRole.USER, content=content)

    @classmethod
    def assistant(cls, content: str, tool_calls: list[ToolCall] | None = None) -> Message:
        """Create an assistant message."""
        return cls(
            role=MessageRole.ASSISTANT,
            content=content,
            tool_calls=tool_calls or []
        )

    @classmethod
    def system(cls, content: str) -> Message:
        """Create a system message."""
        return cls(role=MessageRole.SYSTEM, content=content)

    @classmethod
    def tool_result(cls, tool_call_id: str, content: str, name: str | None = None) -> Message:
        """Create a tool result message."""
        return cls(
            role=MessageRole.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            name=name
        )


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = ""
    latency_ms: float = 0.0

    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return len(self.tool_calls) > 0

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens


@dataclass
class StreamChunk:
    """A chunk of streamed response."""
    content: str
    is_complete: bool = False
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class ToolDefinition:
    """Definition of a tool for LLM."""
    name: str
    description: str
    parameters: dict[str, Any]

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

    def to_anthropic_format(self) -> dict[str, Any]:
        """Convert to Anthropic tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol defining the interface for LLM providers."""

    @property
    def name(self) -> str:
        """Provider name."""
        ...

    @property
    def is_local(self) -> bool:
        """Whether this provider runs locally."""
        ...

    async def check_health(self) -> bool:
        """Check if the provider is available and healthy."""
        ...

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> LLMResponse:
        """Generate a completion."""
        ...

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion."""
        ...


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, default_model: str | None = None):
        self._default_model = default_model

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @property
    @abstractmethod
    def is_local(self) -> bool:
        """Whether this provider runs locally."""
        pass

    @property
    def default_model(self) -> str:
        """Get the default model."""
        return self._default_model or ""

    @abstractmethod
    async def check_health(self) -> bool:
        """Check if the provider is available and healthy."""
        pass

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> LLMResponse:
        """Generate a completion."""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion."""
        pass

    def _prepare_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert messages to API format."""
        return [msg.to_dict() for msg in messages]


class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class ProviderUnavailableError(LLMError):
    """Provider is not available."""
    pass


class RateLimitError(LLMError):
    """Rate limit exceeded."""
    pass


class ContextTooLongError(LLMError):
    """Context exceeds maximum length."""
    pass


class AuthenticationError(LLMError):
    """Authentication failed."""
    pass


class ModelNotFoundError(LLMError):
    """Requested model not found."""
    pass
