"""
LLM-OS Configuration

Handles loading and managing configuration from files and environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Default configuration paths
DEFAULT_CONFIG_PATHS = [
    Path("/etc/llm-os/config.yaml"),
    Path.home() / ".config" / "llm-os" / "config.yaml",
    Path.home() / ".llm-os" / "config.yaml",
    Path("config.yaml"),
]


@dataclass
class LLMProviderConfig:
    """Configuration for an LLM provider."""
    enabled: bool = True
    api_key: str = ""
    base_url: str = ""
    models: dict[str, str] = field(default_factory=dict)
    default_model: str = ""
    timeout: float = 60.0


@dataclass
class OllamaConfig(LLMProviderConfig):
    """Ollama-specific configuration."""
    base_url: str = "http://localhost:11434"
    default_model: str = "qwen2.5:7b"
    models: dict[str, str] = field(default_factory=lambda: {
        "fast": "llama3.2:3b",
        "default": "qwen2.5:7b",  # Excellent tool calling
        "best": "qwen2.5:7b",
        "reasoning": "deepseek-r1:1.5b",
    })


@dataclass
class AnthropicConfig(LLMProviderConfig):
    """Anthropic-specific configuration."""
    default_model: str = "claude-3-5-haiku-latest"
    models: dict[str, str] = field(default_factory=lambda: {
        "fast": "claude-3-5-haiku-latest",
        "default": "claude-3-5-haiku-latest",
        "best": "claude-sonnet-4-20250514",
        "reasoning": "claude-sonnet-4-20250514",
    })


@dataclass
class OpenAIConfig(LLMProviderConfig):
    """OpenAI-specific configuration."""
    default_model: str = "gpt-4o-mini"
    models: dict[str, str] = field(default_factory=lambda: {
        "fast": "gpt-4o-mini",
        "default": "gpt-4o-mini",
        "best": "gpt-4o",
        "reasoning": "o1-mini",
    })


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


@dataclass
class UIConfig:
    """UI configuration."""
    theme: str = "default"
    show_timestamps: bool = True
    show_tool_calls: bool = True
    stream_responses: bool = True
    history_size: int = 1000


@dataclass
class Config:
    """Main LLM-OS configuration."""
    # LLM providers
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)

    # Default provider
    default_provider: str = "ollama"
    local_first: bool = True
    cost_optimization: bool = True

    # MCP
    mcp: MCPConfig = field(default_factory=MCPConfig)

    # Security
    security: SecurityConfig = field(default_factory=SecurityConfig)

    # UI
    ui: UIConfig = field(default_factory=UIConfig)

    # Paths
    data_dir: Path = field(default_factory=lambda: Path.home() / ".llm-os")
    log_dir: Path = field(default_factory=lambda: Path.home() / ".llm-os" / "logs")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "default_provider": self.default_provider,
            "local_first": self.local_first,
            "cost_optimization": self.cost_optimization,
            "ollama": {
                "enabled": self.ollama.enabled,
                "base_url": self.ollama.base_url,
                "default_model": self.ollama.default_model,
            },
            "anthropic": {
                "enabled": self.anthropic.enabled,
                "default_model": self.anthropic.default_model,
            },
            "openai": {
                "enabled": self.openai.enabled,
                "default_model": self.openai.default_model,
            },
            "mcp": {
                "auto_start": self.mcp.auto_start,
                "enabled_servers": self.mcp.enabled_servers,
                "external": {
                    "enabled_official": self.mcp.external.enabled_official,
                    "use_official_filesystem": self.mcp.external.use_official_filesystem,
                    "use_official_git": self.mcp.external.use_official_git,
                    "custom_servers": self.mcp.external.custom_servers,
                    "global_env": self.mcp.external.global_env,
                },
            },
            "security": {
                "require_confirmation_write": self.security.require_confirmation_write,
                "sandbox_enabled": self.security.sandbox_enabled,
            },
            "ui": {
                "theme": self.ui.theme,
                "stream_responses": self.ui.stream_responses,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create from dictionary."""
        config = cls()

        # Update provider configs
        if "ollama" in data:
            ollama_data = data["ollama"]
            config.ollama.enabled = ollama_data.get("enabled", True)
            config.ollama.base_url = ollama_data.get("base_url", config.ollama.base_url)
            config.ollama.default_model = ollama_data.get("default_model", config.ollama.default_model)

        if "anthropic" in data:
            anthropic_data = data["anthropic"]
            config.anthropic.enabled = anthropic_data.get("enabled", True)
            config.anthropic.api_key = anthropic_data.get("api_key", "")
            config.anthropic.default_model = anthropic_data.get("default_model", config.anthropic.default_model)

        if "openai" in data:
            openai_data = data["openai"]
            config.openai.enabled = openai_data.get("enabled", True)
            config.openai.api_key = openai_data.get("api_key", "")
            config.openai.default_model = openai_data.get("default_model", config.openai.default_model)

        # Update other configs
        config.default_provider = data.get("default_provider", config.default_provider)
        config.local_first = data.get("local_first", config.local_first)
        config.cost_optimization = data.get("cost_optimization", config.cost_optimization)

        if "mcp" in data:
            mcp_data = data["mcp"]
            config.mcp.auto_start = mcp_data.get("auto_start", True)
            config.mcp.enabled_servers = mcp_data.get("enabled_servers", config.mcp.enabled_servers)

            # Handle external server config
            if "external" in mcp_data:
                ext_data = mcp_data["external"]
                config.mcp.external.enabled_official = ext_data.get(
                    "enabled_official", config.mcp.external.enabled_official
                )
                config.mcp.external.use_official_filesystem = ext_data.get(
                    "use_official_filesystem", config.mcp.external.use_official_filesystem
                )
                config.mcp.external.use_official_git = ext_data.get(
                    "use_official_git", config.mcp.external.use_official_git
                )
                config.mcp.external.custom_servers = ext_data.get(
                    "custom_servers", config.mcp.external.custom_servers
                )
                config.mcp.external.global_env = ext_data.get(
                    "global_env", config.mcp.external.global_env
                )

        if "security" in data:
            sec_data = data["security"]
            config.security.require_confirmation_write = sec_data.get("require_confirmation_write", True)
            config.security.sandbox_enabled = sec_data.get("sandbox_enabled", True)
            config.security.allowed_paths = sec_data.get("allowed_paths", [])
            config.security.blocked_paths = sec_data.get("blocked_paths", config.security.blocked_paths)

        if "ui" in data:
            ui_data = data["ui"]
            config.ui.theme = ui_data.get("theme", "default")
            config.ui.stream_responses = ui_data.get("stream_responses", True)

        if "data_dir" in data:
            config.data_dir = Path(data["data_dir"])

        if "log_dir" in data:
            config.log_dir = Path(data["log_dir"])

        return config


def load_config(config_path: Path | str | None = None) -> Config:
    """
    Load configuration from file.

    Args:
        config_path: Path to config file (optional, will search defaults)

    Returns:
        Loaded configuration
    """
    # Find config file
    if config_path:
        paths = [Path(config_path)]
    else:
        paths = DEFAULT_CONFIG_PATHS

    config_file = None
    for path in paths:
        if path.exists():
            config_file = path
            break

    # Load from file if found
    if config_file:
        try:
            with open(config_file, "r") as f:
                data = yaml.safe_load(f) or {}
            config = Config.from_dict(data)
        except Exception as e:
            print(f"Warning: Could not load config from {config_file}: {e}")
            config = Config()
    else:
        config = Config()

    # Override with environment variables
    config = _apply_env_overrides(config)

    # Ensure directories exist
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.log_dir.mkdir(parents=True, exist_ok=True)

    return config


def _apply_env_overrides(config: Config) -> Config:
    """Apply environment variable overrides."""
    # API keys
    if api_key := os.environ.get("ANTHROPIC_API_KEY"):
        config.anthropic.api_key = api_key
        config.anthropic.enabled = True

    if api_key := os.environ.get("OPENAI_API_KEY"):
        config.openai.api_key = api_key
        config.openai.enabled = True

    # Ollama
    if base_url := os.environ.get("OLLAMA_BASE_URL"):
        config.ollama.base_url = base_url

    if model := os.environ.get("OLLAMA_MODEL"):
        config.ollama.default_model = model

    # Default provider
    if provider := os.environ.get("LLM_OS_PROVIDER"):
        config.default_provider = provider

    return config


def save_config(config: Config, config_path: Path | str | None = None) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration to save
        config_path: Path to save to (default: ~/.llm-os/config.yaml)
    """
    if config_path is None:
        config_path = Path.home() / ".llm-os" / "config.yaml"
    else:
        config_path = Path(config_path)

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Save
    with open(config_path, "w") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
