"""
UI Configuration
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class UIConfig:
    """UI configuration."""
    theme: str = "default"
    show_timestamps: bool = True
    show_tool_calls: bool = True
    stream_responses: bool = True
    history_size: int = 1000

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "theme": self.theme,
            "show_timestamps": self.show_timestamps,
            "show_tool_calls": self.show_tool_calls,
            "stream_responses": self.stream_responses,
            "history_size": self.history_size,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UIConfig:
        """Create from dictionary."""
        return cls(
            theme=data.get("theme", "default"),
            show_timestamps=data.get("show_timestamps", True),
            show_tool_calls=data.get("show_tool_calls", True),
            stream_responses=data.get("stream_responses", True),
            history_size=data.get("history_size", 1000),
        )
