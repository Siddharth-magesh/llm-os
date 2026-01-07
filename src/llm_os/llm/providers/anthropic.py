"""
Anthropic Claude Provider Implementation

Cloud LLM inference using Anthropic's Claude API.
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


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic provider for Claude API.

    Uses the official Anthropic Python SDK for API calls.
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "claude-3-5-haiku-latest",
        max_tokens: int = 4096,
        timeout: float = 120.0,
    ):
        super().__init__(default_model)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._client: Any = None

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def is_local(self) -> bool:
        return False

    def _get_client(self) -> Any:
        """Get or create Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(
                    api_key=self.api_key,
                    timeout=self.timeout,
                )
            except ImportError:
                raise ProviderUnavailableError(
                    "anthropic package not installed. Run: pip install anthropic"
                )
        return self._client

    async def check_health(self) -> bool:
        """Check if API key is configured."""
        if not self.api_key:
            return False

        # We can't easily test the API without making a call,
        # so we just verify the key exists
        return True

    def _convert_tools(self, tools: list[ToolDefinition] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert tools to Anthropic format."""
        result = []
        for tool in tools:
            if isinstance(tool, dict):
                # Already in MCP format, convert to Anthropic
                result.append({
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "input_schema": tool.get("inputSchema", {}),
                })
            else:
                result.append(tool.to_anthropic_format())
        return result

    def _convert_messages(
        self, messages: list[Message]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """
        Convert messages to Anthropic format.

        Returns (system_prompt, messages) tuple.
        """
        system_prompt: str | None = None
        converted: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Anthropic handles system prompt separately
                system_prompt = msg.content
                continue

            message_dict: dict[str, Any] = {
                "role": msg.role.value if msg.role != MessageRole.TOOL else "user",
                "content": msg.content,
            }

            # Handle tool results
            if msg.role == MessageRole.TOOL and msg.tool_call_id:
                message_dict = {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content,
                        }
                    ],
                }

            converted.append(message_dict)

        return system_prompt, converted

    def _parse_response(self, response: Any) -> tuple[str, list[ToolCall]]:
        """Parse Anthropic response into content and tool calls."""
        content_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        for block in response.content:
            if block.type == "text":
                content_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input if isinstance(block.input, dict) else {},
                ))

        return "".join(content_parts), tool_calls

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> LLMResponse:
        """Generate a completion using Claude."""
        if not self.api_key:
            raise AuthenticationError("ANTHROPIC_API_KEY not set")

        model = model or self.default_model
        start_time = time.time()

        client = self._get_client()
        system_prompt, converted_messages = self._convert_messages(messages)

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": converted_messages,
            "temperature": temperature,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        try:
            response = await client.messages.create(**kwargs)
        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str:
                raise RateLimitError(f"Rate limit exceeded: {e}")
            elif "authentication" in error_str or "401" in error_str:
                raise AuthenticationError(f"Authentication failed: {e}")
            elif "context_length" in error_str or "too long" in error_str:
                raise ContextTooLongError(f"Context too long: {e}")
            raise ProviderUnavailableError(f"Anthropic request failed: {e}")

        latency_ms = (time.time() - start_time) * 1000
        content, tool_calls = self._parse_response(response)

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            model=model,
            provider=self.name,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            finish_reason=response.stop_reason or "stop",
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
        """Stream a completion from Claude."""
        if not self.api_key:
            raise AuthenticationError("ANTHROPIC_API_KEY not set")

        model = model or self.default_model
        client = self._get_client()
        system_prompt, converted_messages = self._convert_messages(messages)

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": converted_messages,
            "temperature": temperature,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        try:
            async with client.messages.stream(**kwargs) as stream:
                accumulated_tool_calls: list[ToolCall] = []
                current_tool_use: dict[str, Any] | None = None

                async for event in stream:
                    if event.type == "content_block_start":
                        if hasattr(event.content_block, "type"):
                            if event.content_block.type == "tool_use":
                                current_tool_use = {
                                    "id": event.content_block.id,
                                    "name": event.content_block.name,
                                    "input": "",
                                }

                    elif event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield StreamChunk(
                                content=event.delta.text,
                                is_complete=False,
                            )
                        elif hasattr(event.delta, "partial_json"):
                            if current_tool_use:
                                current_tool_use["input"] += event.delta.partial_json

                    elif event.type == "content_block_stop":
                        if current_tool_use:
                            try:
                                args = json.loads(current_tool_use["input"])
                            except json.JSONDecodeError:
                                args = {}

                            accumulated_tool_calls.append(ToolCall(
                                id=current_tool_use["id"],
                                name=current_tool_use["name"],
                                arguments=args,
                            ))
                            current_tool_use = None

                    elif event.type == "message_stop":
                        yield StreamChunk(
                            content="",
                            is_complete=True,
                            tool_calls=accumulated_tool_calls,
                        )

        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str:
                raise RateLimitError(f"Rate limit exceeded: {e}")
            elif "authentication" in error_str:
                raise AuthenticationError(f"Authentication failed: {e}")
            raise ProviderUnavailableError(f"Anthropic streaming failed: {e}")

    async def close(self) -> None:
        """Close the client."""
        if self._client:
            # AsyncAnthropic doesn't need explicit closing
            self._client = None

    async def __aenter__(self) -> AnthropicProvider:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
