"""
OpenAI Provider Implementation

Cloud LLM inference using OpenAI's API.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, AsyncIterator

from llm_os.llm.base import (
    BaseLLMProvider,
    LLMResponse,
    Message,
    MessageRole,
    ProviderUnavailableError,
    StreamChunk,
    ToolCall,
    ToolDefinition,
    AuthenticationError,
    RateLimitError,
    ContextTooLongError,
)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider for GPT models.

    Uses the official OpenAI Python SDK for API calls.
    Also compatible with OpenAI-compatible APIs (Groq, Together, etc.)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str = "gpt-4o-mini",
        timeout: float = 120.0,
        organization: str | None = None,
    ):
        super().__init__(default_model)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url
        self.timeout = timeout
        self.organization = organization
        self._client: Any = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def is_local(self) -> bool:
        return False

    def _get_client(self) -> Any:
        """Get or create OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                kwargs: dict[str, Any] = {
                    "api_key": self.api_key,
                    "timeout": self.timeout,
                }
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                if self.organization:
                    kwargs["organization"] = self.organization

                self._client = AsyncOpenAI(**kwargs)
            except ImportError:
                raise ProviderUnavailableError(
                    "openai package not installed. Run: pip install openai"
                )
        return self._client

    async def check_health(self) -> bool:
        """Check if API key is configured."""
        if not self.api_key:
            return False
        return True

    def _convert_tools(self, tools: list[ToolDefinition] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert tools to OpenAI format."""
        result = []
        for tool in tools:
            if isinstance(tool, dict):
                # Already in MCP format, convert to OpenAI
                result.append({
                    "type": "function",
                    "function": {
                        "name": tool.get("name", ""),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {}),
                    }
                })
            else:
                result.append(tool.to_openai_format())
        return result

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert messages to OpenAI format."""
        converted: list[dict[str, Any]] = []

        for msg in messages:
            message_dict: dict[str, Any] = {
                "role": msg.role.value,
                "content": msg.content,
            }

            # Handle assistant messages with tool calls
            if msg.role == MessageRole.ASSISTANT and msg.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        }
                    }
                    for tc in msg.tool_calls
                ]

            # Handle tool results
            if msg.role == MessageRole.TOOL:
                message_dict["tool_call_id"] = msg.tool_call_id or ""
                if msg.name:
                    message_dict["name"] = msg.name

            converted.append(message_dict)

        return converted

    def _parse_tool_calls(self, tool_calls: list[Any]) -> list[ToolCall]:
        """Parse tool calls from OpenAI response."""
        result: list[ToolCall] = []

        for tc in tool_calls:
            arguments = tc.function.arguments
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}

            result.append(ToolCall(
                id=tc.id,
                name=tc.function.name,
                arguments=arguments,
            ))

        return result

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> LLMResponse:
        """Generate a completion using OpenAI."""
        if not self.api_key:
            raise AuthenticationError("OPENAI_API_KEY not set")

        model = model or self.default_model
        start_time = time.time()

        client = self._get_client()
        converted_messages = self._convert_messages(messages)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": converted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if tools:
            kwargs["tools"] = self._convert_tools(tools)
            kwargs["tool_choice"] = "auto"

        try:
            response = await client.chat.completions.create(**kwargs)
        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str:
                raise RateLimitError(f"Rate limit exceeded: {e}")
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(f"Authentication failed: {e}")
            elif "context_length" in error_str or "maximum context" in error_str:
                raise ContextTooLongError(f"Context too long: {e}")
            raise ProviderUnavailableError(f"OpenAI request failed: {e}")

        latency_ms = (time.time() - start_time) * 1000
        choice = response.choices[0]
        message = choice.message

        tool_calls: list[ToolCall] = []
        if message.tool_calls:
            tool_calls = self._parse_tool_calls(message.tool_calls)

        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            model=model,
            provider=self.name,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            finish_reason=choice.finish_reason or "stop",
            latency_ms=latency_ms,
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion from OpenAI."""
        if not self.api_key:
            raise AuthenticationError("OPENAI_API_KEY not set")

        model = model or self.default_model
        client = self._get_client()
        converted_messages = self._convert_messages(messages)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": converted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        if tools:
            kwargs["tools"] = self._convert_tools(tools)
            kwargs["tool_choice"] = "auto"

        try:
            stream = await client.chat.completions.create(**kwargs)

            # Track tool calls being built across chunks
            tool_call_builders: dict[int, dict[str, Any]] = {}

            async for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason

                # Handle content
                content = delta.content or ""

                # Handle tool calls
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        index = tc_delta.index

                        if index not in tool_call_builders:
                            tool_call_builders[index] = {
                                "id": tc_delta.id or "",
                                "name": "",
                                "arguments": "",
                            }

                        if tc_delta.id:
                            tool_call_builders[index]["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                tool_call_builders[index]["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                tool_call_builders[index]["arguments"] += tc_delta.function.arguments

                # Build final tool calls if we're done
                tool_calls: list[ToolCall] = []
                is_complete = finish_reason is not None

                if is_complete and tool_call_builders:
                    for builder in tool_call_builders.values():
                        try:
                            args = json.loads(builder["arguments"]) if builder["arguments"] else {}
                        except json.JSONDecodeError:
                            args = {}

                        tool_calls.append(ToolCall(
                            id=builder["id"],
                            name=builder["name"],
                            arguments=args,
                        ))

                yield StreamChunk(
                    content=content,
                    is_complete=is_complete,
                    tool_calls=tool_calls,
                )

        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str:
                raise RateLimitError(f"Rate limit exceeded: {e}")
            elif "authentication" in error_str:
                raise AuthenticationError(f"Authentication failed: {e}")
            raise ProviderUnavailableError(f"OpenAI streaming failed: {e}")

    async def close(self) -> None:
        """Close the client."""
        if self._client:
            # AsyncOpenAI doesn't need explicit closing
            self._client = None

    async def __aenter__(self) -> OpenAIProvider:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()


class GroqProvider(OpenAIProvider):
    """
    Groq provider using OpenAI-compatible API.

    Groq provides ultra-fast inference for open models.
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "llama-3.2-3b-preview",
        timeout: float = 60.0,
    ):
        super().__init__(
            api_key=api_key or os.environ.get("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
            default_model=default_model,
            timeout=timeout,
        )

    @property
    def name(self) -> str:
        return "groq"


class TogetherProvider(OpenAIProvider):
    """
    Together AI provider using OpenAI-compatible API.

    Together AI provides access to various open models.
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "meta-llama/Llama-3.2-3B-Instruct-Turbo",
        timeout: float = 120.0,
    ):
        super().__init__(
            api_key=api_key or os.environ.get("TOGETHER_API_KEY"),
            base_url="https://api.together.xyz/v1",
            default_model=default_model,
            timeout=timeout,
        )

    @property
    def name(self) -> str:
        return "together"
