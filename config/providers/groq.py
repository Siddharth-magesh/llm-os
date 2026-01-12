"""
Groq Provider Configuration
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from config.llm_config import LLMProviderConfig


@dataclass
class GroqConfig(LLMProviderConfig):
    """Groq-specific configuration."""
    api_key: str = field(default_factory=lambda: os.environ.get("GROQ_API_KEY", ""))
    base_url: str = "https://api.groq.com/openai/v1"
    default_model: str = "llama-3.3-70b-versatile"
    models: dict[str, str] = field(default_factory=lambda: {
        "fast": "llama-3.1-8b-instant",
        "default": "llama-3.3-70b-versatile",  # Best balance
        "best": "llama-3.3-70b-versatile",
    })
