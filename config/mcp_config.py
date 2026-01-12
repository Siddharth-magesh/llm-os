"""
MCP Server Configuration
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExternalServerConfig:
    """Configuration for external MCP servers (stdio-based)."""
    # Which official servers to enable
    enabled_official: list[str] = field(default_factory=lambda: [
        "filesystem", "git", "fetch", "memory"
    ])
    # Whether to use official servers instead of internal implementations
    use_official_filesystem: bool = True
    use_official_git: bool = True
    # Custom external server configurations
    custom_servers: list[dict[str, Any]] = field(default_factory=list)
    # Global environment variables for all external servers
    global_env: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled_official": self.enabled_official,
            "use_official_filesystem": self.use_official_filesystem,
            "use_official_git": self.use_official_git,
            "custom_servers": self.custom_servers,
            "global_env": self.global_env,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExternalServerConfig:
        """Create from dictionary."""
        return cls(
            enabled_official=data.get("enabled_official", ["filesystem", "git", "fetch", "memory"]),
            use_official_filesystem=data.get("use_official_filesystem", True),
            use_official_git=data.get("use_official_git", True),
            custom_servers=data.get("custom_servers", []),
            global_env=data.get("global_env", {}),
        )


@dataclass
class MCPConfig:
    """MCP server configuration."""
    auto_start: bool = True
    health_check_interval: float = 30.0
    auto_restart: bool = True
    max_restart_attempts: int = 3
    # Internal Python servers to enable
    enabled_servers: list[str] = field(default_factory=lambda: [
        "applications", "process", "system"
    ])
    # External MCP server settings
    external: ExternalServerConfig = field(default_factory=ExternalServerConfig)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "auto_start": self.auto_start,
            "health_check_interval": self.health_check_interval,
            "auto_restart": self.auto_restart,
            "max_restart_attempts": self.max_restart_attempts,
            "enabled_servers": self.enabled_servers,
            "external": self.external.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MCPConfig:
        """Create from dictionary."""
        external = ExternalServerConfig.from_dict(data.get("external", {}))
        return cls(
            auto_start=data.get("auto_start", True),
            health_check_interval=data.get("health_check_interval", 30.0),
            auto_restart=data.get("auto_restart", True),
            max_restart_attempts=data.get("max_restart_attempts", 3),
            enabled_servers=data.get("enabled_servers", ["applications", "process", "system"]),
            external=external,
        )
