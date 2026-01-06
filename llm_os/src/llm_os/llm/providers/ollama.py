"""
Ollama Provider Implementation

Local LLM inference using Ollama.
"""

from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator

import httpx

from llm_os.llm.base import (
    BaseLLMProvider,
    LLMResponse,
    Message,
    ProviderUnavailableError,
    StreamChunk,
    ToolCall,
    ToolDefinition,
    ModelNotFoundError,
)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for local LLM inference.

    Ollama provides easy-to-use local model deployment with REST API.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3.2:3b",
        timeout: float = 120.0,
    ):
        super().__init__(default_model)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def is_local(self) -> bool:
        return True

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def check_health(self) -> bool:
        """Check if Ollama is running and responding."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """List available models."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            raise ProviderUnavailableError(f"Failed to list models: {e}")

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/pull",
                json={"name": model},
                timeout=httpx.Timeout(600.0),  # Models can take time to download
            )
            return response.status_code == 200
        except Exception:
            return False

    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]]:
        """Convert tools to Ollama format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
            for tool in tools
        ]

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert messages to Ollama format."""
        result = []
        for msg in messages:
            message_dict: dict[str, Any] = {
                "role": msg.role.value,
                "content": msg.content,
            }

            # Handle tool calls in assistant messages
            if msg.tool_calls:
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

            result.append(message_dict)

        return result

    def _parse_tool_calls(self, tool_calls_data: list[dict[str, Any]]) -> list[ToolCall]:
        """Parse tool calls from Ollama response."""
        tool_calls = []
        for tc in tool_calls_data:
            func = tc.get("function", {})
            arguments = func.get("arguments", "{}")

            # Parse arguments if they're a string
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}

            tool_calls.append(ToolCall(
                id=tc.get("id", f"call_{len(tool_calls)}"),
                name=func.get("name", ""),
                arguments=arguments,
            ))

        return tool_calls

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> LLMResponse:
        """Generate a completion using Ollama."""
        if not await self.check_health():
            raise ProviderUnavailableError("Ollama is not available")

        model = model or self.default_model
        start_time = time.time()

        client = await self._get_client()

        payload: dict[str, Any] = {
            "model": model,
            "messages": self._convert_messages(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        if tools:
            payload["tools"] = self._convert_tools(tools)

        try:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ModelNotFoundError(f"Model '{model}' not found")
            raise ProviderUnavailableError(f"Ollama request failed: {e}")
        except Exception as e:
            raise ProviderUnavailableError(f"Ollama request failed: {e}")

        latency_ms = (time.time() - start_time) * 1000

        message_data = data.get("message", {})
        tool_calls = self._parse_tool_calls(message_data.get("tool_calls", []))

        return LLMResponse(
            content=message_data.get("content", ""),
            tool_calls=tool_calls,
            model=model,
            provider=self.name,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            finish_reason=data.get("done_reason", "stop"),
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
        """Stream a completion from Ollama."""
        if not await self.check_health():
            raise ProviderUnavailableError("Ollama is not available")

        model = model or self.default_model
        client = await self._get_client()

        payload: dict[str, Any] = {
            "model": model,
            "messages": self._convert_messages(messages),
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        if tools:
            payload["tools"] = self._convert_tools(tools)

        try:
            async with client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()

                accumulated_tool_calls: list[ToolCall] = []

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    message_data = data.get("message", {})
                    content = message_data.get("content", "")
                    is_done = data.get("done", False)

                    # Parse any tool calls
                    if message_data.get("tool_calls"):
                        accumulated_tool_calls = self._parse_tool_calls(
                            message_data["tool_calls"]
                        )

                    yield StreamChunk(
                        content=content,
                        is_complete=is_done,
                        tool_calls=accumulated_tool_calls if is_done else [],
                    )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ModelNotFoundError(f"Model '{model}' not found")
            raise ProviderUnavailableError(f"Ollama streaming failed: {e}")
        except Exception as e:
            raise ProviderUnavailableError(f"Ollama streaming failed: {e}")

    async def __aenter__(self) -> OllamaProvider:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
