"""
MCP Server Types

Type definitions for MCP server configuration and status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ServerState(str, Enum):
    """Server lifecycle states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class TransportType(str, Enum):
    """MCP transport types."""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"


class PermissionLevel(str, Enum):
    """Permission levels for server operations."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    SYSTEM = "system"
    DANGEROUS = "dangerous"


@dataclass
class ServerConfig:
    """Configuration for an MCP server."""
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"

    # Execution settings
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    working_directory: str | None = None
    transport: TransportType = TransportType.STDIO

    # Server settings
    auto_start: bool = False
    timeout: float = 30.0
    max_retries: int = 3

    # Security settings
    trusted: bool = True
    permission_level: PermissionLevel = PermissionLevel.READ
    sandbox: bool = False
    allowed_paths: list[str] = field(default_factory=list)

    # Metadata
    author: str = ""
    tags: list[str] = field(default_factory=list)
    config_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "working_directory": self.working_directory,
            "transport": self.transport.value,
            "auto_start": self.auto_start,
            "timeout": self.timeout,
            "trusted": self.trusted,
            "permission_level": self.permission_level.value,
            "sandbox": self.sandbox,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServerConfig:
        """Create from dictionary."""
        return cls(
            id=data.get("id", data.get("name", "")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            command=data.get("command", ""),
            args=data.get("args", []),
            env=data.get("env", {}),
            working_directory=data.get("working_directory"),
            transport=TransportType(data.get("transport", "stdio")),
            auto_start=data.get("auto_start", False),
            timeout=data.get("timeout", 30.0),
            max_retries=data.get("max_retries", 3),
            trusted=data.get("trusted", True),
            permission_level=PermissionLevel(data.get("permission_level", "read")),
            sandbox=data.get("sandbox", False),
            allowed_paths=data.get("allowed_paths", []),
            author=data.get("author", ""),
            tags=data.get("tags", []),
        )


@dataclass
class ServerStatus:
    """Runtime status of an MCP server."""
    server_id: str
    state: ServerState
    pid: int | None = None
    started_at: datetime | None = None
    last_heartbeat: datetime | None = None
    tool_count: int = 0
    request_count: int = 0
    error_count: int = 0
    last_error: str | None = None
    error: str | None = None  # Added for initialization errors

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self.state == ServerState.RUNNING

    @property
    def uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        if not self.started_at or self.state != ServerState.RUNNING:
            return 0.0
        return (datetime.now() - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "server_id": self.server_id,
            "state": self.state.value,
            "pid": self.pid,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "tool_count": self.tool_count,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "uptime_seconds": self.uptime_seconds,
        }


@dataclass
class ServerCapabilities:
    """Capabilities reported by an MCP server."""
    tools: bool = True
    resources: bool = False
    prompts: bool = False
    logging: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tools": self.tools,
            "resources": self.resources,
            "prompts": self.prompts,
            "logging": self.logging,
        }


@dataclass
class ServerInfo:
    """Full information about an MCP server."""
    config: ServerConfig
    status: ServerStatus
    capabilities: ServerCapabilities = field(default_factory=ServerCapabilities)
    tools: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config": self.config.to_dict(),
            "status": self.status.to_dict(),
            "capabilities": self.capabilities.to_dict(),
            "tools": self.tools,
        }
