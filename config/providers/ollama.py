"""
Ollama Provider Configuration
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from config.llm_config import LLMProviderConfig


@dataclass
class OllamaConfig(LLMProviderConfig):
    """Ollama-specific configuration."""
    base_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    default_model: str = field(default_factory=lambda: os.environ.get("OLLAMA_MODEL", "qwen2.5:7b"))
    models: dict[str, str] = field(default_factory=lambda: {
        "fast": "llama3.2:3b",
        "default": "qwen2.5:7b",  # Excellent tool calling
        "best": "qwen2.5:7b",
        "reasoning": "deepseek-r1:1.5b",
    })
