"""
LLM Router

Routes requests to appropriate LLM providers based on task type,
availability, and configuration.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator

from llm_os.llm.base import (
    BaseLLMProvider,
    LLMResponse,
    Message,
    StreamChunk,
    ToolDefinition,
    LLMError,
    ProviderUnavailableError,
    RateLimitError,
)
from llm_os.llm.classifier import TaskClassifier, TaskType, ClassificationResult
from llm_os.llm.providers.ollama import OllamaProvider
from llm_os.llm.providers.groq import GroqProvider


logger = logging.getLogger(__name__)


@dataclass
class RouterConfig:
    """Configuration for the LLM router."""
    default_provider: str = "ollama"
    fallback_chain: list[str] = field(default_factory=lambda: ["ollama", "groq"])
    local_first: bool = True
    cost_optimization: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 120.0
    groq_api_key: str | None = None


@dataclass
class UsageStats:
    """Statistics for LLM usage."""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: str | None = None


class LLMRouter:
    """
    Routes LLM requests to appropriate providers.

    Features:
    - Automatic provider selection based on task complexity
    - Fallback chain for resilience
    - Cost optimization routing
    - Local-first preference
    - Usage tracking
    """

    def __init__(
        self,
        config: RouterConfig | None = None,
        providers: dict[str, BaseLLMProvider] | None = None,
    ):
        """
        Initialize the LLM router.

        Args:
            config: Router configuration
            providers: Pre-configured providers (optional)
        """
        self.config = config or RouterConfig()
        self._providers: dict[str, BaseLLMProvider] = providers or {}
        self._classifier = TaskClassifier()
        self._usage_history: list[UsageStats] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize providers based on available API keys."""
        if self._initialized:
            return

        # Initialize Ollama (local - FREE)
        if "ollama" not in self._providers:
            try:
                ollama = OllamaProvider()
                if await ollama.check_health():
                    self._providers["ollama"] = ollama
                    logger.info("Ollama provider initialized")
                else:
                    logger.warning("Ollama not running or not healthy")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama: {e}")

        # Initialize Groq (cloud - FAST)
        groq_key = self.config.groq_api_key or os.environ.get("GROQ_API_KEY")
        if "groq" not in self._providers and groq_key:
            try:
                groq = GroqProvider(api_key=groq_key)
                self._providers["groq"] = groq
                logger.info("Groq provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq: {e}")

        self._initialized = True

        if not self._providers:
            logger.error("No LLM providers available! Install Ollama or set GROQ_API_KEY")
        else:
            logger.info(f"Initialized providers: {', '.join(self._providers.keys())}")

    async def close(self) -> None:
        """Close all provider connections."""
        for provider in self._providers.values():
            if hasattr(provider, "close"):
                await provider.close()

    @property
    def available_providers(self) -> list[str]:
        """Get list of available provider names."""
        return list(self._providers.keys())

    def get_provider(self, name: str) -> BaseLLMProvider | None:
        """Get a specific provider by name."""
        return self._providers.get(name)

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
    ) -> LLMResponse:
        """
        Generate a completion using the most appropriate provider.

        Args:
            messages: Conversation messages
            tools: Available tools for function calling
            task_type: Pre-classified task type (optional, will classify if not provided)
            preferred_provider: Specific provider to use (optional)
            model: Specific model to use (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream (not used here, use stream() method)

        Returns:
            LLMResponse with the completion
        """
        await self.initialize()

        if not self._providers:
            raise ProviderUnavailableError("No LLM providers available")

        # Classify task if not provided
        if task_type is None:
            # Get user message for classification
            user_messages = [m for m in messages if m.role.value == "user"]
            if user_messages:
                classification = self._classifier.classify(user_messages[-1].content)
                task_type = classification.task_type
            else:
                task_type = TaskType.MODERATE

        # Select provider
        provider_name = preferred_provider or self._select_provider(task_type)

        # Get model for task type
        if model is None:
            model = self._get_model_for_task(provider_name, task_type)

        # Try with fallbacks
        last_error: Exception | None = None

        for attempt in range(self.config.max_retries):
            provider = self._providers.get(provider_name)

            if not provider:
                provider_name = self._get_next_fallback(provider_name)
                continue

            try:
                # Check provider health
                if not await provider.check_health():
                    raise ProviderUnavailableError(f"{provider_name} is not available")

                # Make request
                response = await provider.complete(
                    messages=messages,
                    tools=tools,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                # Track usage
                self._track_usage(response)

                return response

            except RateLimitError as e:
                logger.warning(f"Rate limit on {provider_name}: {e}")
                last_error = e
                # Wait before retry
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

            except ProviderUnavailableError as e:
                logger.warning(f"Provider {provider_name} unavailable: {e}")
                last_error = e
                # Try next provider in fallback chain
                provider_name = self._get_next_fallback(provider_name)
                model = None  # Reset model for new provider

            except LLMError as e:
                logger.error(f"LLM error on {provider_name}: {e}")
                last_error = e
                provider_name = self._get_next_fallback(provider_name)
                model = None

        # All retries exhausted
        raise ProviderUnavailableError(
            f"All providers failed. Last error: {last_error}"
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        task_type: TaskType | None = None,
        preferred_provider: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a completion from the most appropriate provider.

        Yields StreamChunk objects as they arrive.
        """
        await self.initialize()

        if not self._providers:
            raise ProviderUnavailableError("No LLM providers available")

        # Classify task if not provided
        if task_type is None:
            user_messages = [m for m in messages if m.role.value == "user"]
            if user_messages:
                classification = self._classifier.classify(user_messages[-1].content)
                task_type = classification.task_type
            else:
                task_type = TaskType.MODERATE

        # Select provider
        provider_name = preferred_provider or self._select_provider(task_type)

        # Get model for task type
        if model is None:
            model = self._get_model_for_task(provider_name, task_type)

        provider = self._providers.get(provider_name)

        if not provider:
            raise ProviderUnavailableError(f"Provider {provider_name} not available")

        if not await provider.check_health():
            raise ProviderUnavailableError(f"{provider_name} is not available")

        async for chunk in provider.stream(
            messages=messages,
            tools=tools,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        ):
            yield chunk

    def classify_task(self, user_input: str) -> ClassificationResult:
        """Classify a user input."""
        return self._classifier.classify(user_input)

    def _select_provider(self, task_type: TaskType) -> str:
        """Select the best provider for a task type."""
        # Local first preference
        if self.config.local_first and "ollama" in self._providers:
            # For complex/reasoning tasks, prefer cloud if available
            if task_type in (TaskType.COMPLEX, TaskType.REASONING):
                if "anthropic" in self._providers:
                    return "anthropic"
                if "openai" in self._providers:
                    return "openai"
            return "ollama"

        # Cost optimization
        if self.config.cost_optimization:
            # Use cheaper providers for simple tasks
            if task_type == TaskType.SIMPLE:
                if "ollama" in self._providers:
                    return "ollama"

        # Use default provider
        if self.config.default_provider in self._providers:
            return self.config.default_provider

        # Use first available
        if self._providers:
            return list(self._providers.keys())[0]

        return "ollama"  # Will fail gracefully if not available

    def _get_model_for_task(
        self,
        provider_name: str,
        task_type: TaskType
    ) -> str | None:
        """Get the appropriate model for a task type."""
        # Model tier mapping
        tier_mapping = {
            TaskType.SIMPLE: "fast",
            TaskType.MODERATE: "default",
            TaskType.COMPLEX: "best",
            TaskType.REASONING: "reasoning",
            TaskType.CREATIVE: "default",
        }

        tier = tier_mapping.get(task_type, "default")

        # Provider-specific model mapping
        model_configs = {
            "ollama": {
                "fast": "llama3.2:3b",  # Changed from 1b - not commonly available
                "default": "llama3.2:3b",
                "best": "llama3.2:3b",
                "reasoning": "deepseek-r1:1.5b",
            },
            "anthropic": {
                "fast": "claude-3-5-haiku-latest",
                "default": "claude-3-5-haiku-latest",
                "best": "claude-sonnet-4-20250514",
                "reasoning": "claude-sonnet-4-20250514",
            },
            "openai": {
                "fast": "gpt-4o-mini",
                "default": "gpt-4o-mini",
                "best": "gpt-4o",
                "reasoning": "o1-mini",
            },
        }

        provider_models = model_configs.get(provider_name, {})
        return provider_models.get(tier)

    def _get_next_fallback(self, current: str) -> str:
        """Get the next provider in the fallback chain."""
        try:
            idx = self.config.fallback_chain.index(current)
            for provider in self.config.fallback_chain[idx + 1:]:
                if provider in self._providers:
                    return provider
        except ValueError:
            pass

        # Return first available provider
        for provider in self.config.fallback_chain:
            if provider in self._providers and provider != current:
                return provider

        return current

    def _track_usage(self, response: LLMResponse) -> None:
        """Track usage statistics."""
        stats = UsageStats(
            provider=response.provider,
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            latency_ms=response.latency_ms,
        )
        self._usage_history.append(stats)

        # Keep only recent history
        if len(self._usage_history) > 1000:
            self._usage_history = self._usage_history[-500:]

    def get_usage_summary(self) -> dict[str, Any]:
        """Get usage statistics summary."""
        if not self._usage_history:
            return {"total_requests": 0}

        total_input = sum(s.input_tokens for s in self._usage_history)
        total_output = sum(s.output_tokens for s in self._usage_history)
        total_latency = sum(s.latency_ms for s in self._usage_history)

        by_provider: dict[str, dict[str, Any]] = {}
        for stats in self._usage_history:
            if stats.provider not in by_provider:
                by_provider[stats.provider] = {
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                }
            by_provider[stats.provider]["requests"] += 1
            by_provider[stats.provider]["input_tokens"] += stats.input_tokens
            by_provider[stats.provider]["output_tokens"] += stats.output_tokens

        return {
            "total_requests": len(self._usage_history),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "average_latency_ms": total_latency / len(self._usage_history),
            "by_provider": by_provider,
        }

    async def check_all_providers(self) -> dict[str, bool]:
        """Check health of all providers."""
        await self.initialize()

        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.check_health()
            except Exception:
                results[name] = False

        return results

    async def __aenter__(self) -> LLMRouter:
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
