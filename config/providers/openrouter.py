"""
OpenRouter Provider Configuration
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from config.llm_config import LLMProviderConfig


@dataclass
class OpenRouterConfig(LLMProviderConfig):
    """OpenRouter-specific configuration."""
    api_key: str = field(default_factory=lambda: os.environ.get("OPENROUTER_API_KEY", ""))
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "google/gemini-2.0-flash-exp:free"
    models: dict[str, str] = field(default_factory=lambda: {
        "fast": "google/gemini-2.0-flash-exp:free",
        "default": "google/gemini-2.0-flash-exp:free",
        "best": "google/gemini-2.5-pro-exp-03-25:free",
    })
