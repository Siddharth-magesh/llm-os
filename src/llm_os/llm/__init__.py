"""
LLM Integration Layer

This module provides a unified interface for interacting with various LLM providers
including local models (Ollama) and cloud APIs (Anthropic Claude, OpenAI).
"""

from llm_os.llm.base import LLMProvider, LLMResponse, Message, ToolCall
from llm_os.llm.router import LLMRouter
from llm_os.llm.context import ContextManager
from llm_os.llm.classifier import TaskClassifier, TaskType
from llm_os.llm.providers.ollama import OllamaProvider
from llm_os.llm.providers.anthropic import AnthropicProvider
from llm_os.llm.providers.openai import OpenAIProvider

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "Message",
    "ToolCall",
    "LLMRouter",
    "ContextManager",
    "TaskClassifier",
    "TaskType",
    "OllamaProvider",
    "AnthropicProvider",
    "OpenAIProvider",
]
