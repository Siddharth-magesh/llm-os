"""
LLM Provider Configuration Base Classes
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMProviderConfig:
    """Base configuration for an LLM provider."""
    enabled: bool = True
    api_key: str = ""
    base_url: str = ""
    models: dict[str, str] = field(default_factory=dict)
    default_model: str = ""
    timeout: float = 60.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "api_key": self.api_key if self.api_key else "",
            "base_url": self.base_url,
            "default_model": self.default_model,
            "timeout": self.timeout,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LLMProviderConfig:
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", ""),
            default_model=data.get("default_model", ""),
            timeout=data.get("timeout", 60.0),
        )
