"""
Security Configuration
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SecurityConfig:
    """Security configuration."""
    require_confirmation_write: bool = True
    require_confirmation_execute: bool = True
    require_confirmation_system: bool = True
    require_confirmation_dangerous: bool = True
    sandbox_enabled: bool = True
    allowed_paths: list[str] = field(default_factory=list)
    blocked_paths: list[str] = field(default_factory=lambda: [
        "/etc/passwd", "/etc/shadow", "/root", "/boot"
    ])

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "require_confirmation_write": self.require_confirmation_write,
            "require_confirmation_execute": self.require_confirmation_execute,
            "require_confirmation_system": self.require_confirmation_system,
            "require_confirmation_dangerous": self.require_confirmation_dangerous,
            "sandbox_enabled": self.sandbox_enabled,
            "allowed_paths": self.allowed_paths,
            "blocked_paths": self.blocked_paths,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SecurityConfig:
        """Create from dictionary."""
        return cls(
            require_confirmation_write=data.get("require_confirmation_write", True),
            require_confirmation_execute=data.get("require_confirmation_execute", True),
            require_confirmation_system=data.get("require_confirmation_system", True),
            require_confirmation_dangerous=data.get("require_confirmation_dangerous", True),
            sandbox_enabled=data.get("sandbox_enabled", True),
            allowed_paths=data.get("allowed_paths", []),
            blocked_paths=data.get("blocked_paths", ["/etc/passwd", "/etc/shadow", "/root", "/boot"]),
        )
