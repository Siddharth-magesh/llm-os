"""
LLM-OS Configuration System

Modular configuration system that loads from:
1. Config files (YAML)
2. Environment variables (.env)
3. Runtime updates

No hardcoded values - everything is configurable.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
import yaml

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Import all config modules
from config.llm_config import LLMProviderConfig
from config.providers.ollama import OllamaConfig
from config.providers.groq import GroqConfig
from config.mcp_config import MCPConfig, ExternalServerConfig
from config.security_config import SecurityConfig
from config.ui_config import UIConfig


# Default configuration paths
DEFAULT_CONFIG_PATHS = [
    Path("/etc/llm-os/config.yaml"),
    Path.home() / ".config" / "llm-os" / "config.yaml",
    Path.home() / ".llm-os" / "config.yaml",
    Path("config.yaml"),
]


@dataclass
class Config:
    """Main LLM-OS configuration."""
    # LLM providers (Ollama + Groq only)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    groq: GroqConfig = field(default_factory=GroqConfig)

    # Default provider (from environment or fallback)
    default_provider: str = field(default_factory=lambda: os.environ.get("LLM_OS_PROVIDER", "groq"))
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
            "groq": {
                "enabled": self.groq.enabled,
                "api_key": self.groq.api_key,
                "default_model": self.groq.default_model,
            },
            "mcp": self.mcp.to_dict(),
            "security": self.security.to_dict(),
            "ui": self.ui.to_dict(),
            "data_dir": str(self.data_dir),
            "log_dir": str(self.log_dir),
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

        if "groq" in data:
            groq_data = data["groq"]
            config.groq.enabled = groq_data.get("enabled", True)
            config.groq.api_key = groq_data.get("api_key", "")
            config.groq.default_model = groq_data.get("default_model", config.groq.default_model)

        # Update other configs
        config.default_provider = data.get("default_provider", config.default_provider)
        config.local_first = data.get("local_first", config.local_first)
        config.cost_optimization = data.get("cost_optimization", config.cost_optimization)

        if "mcp" in data:
            config.mcp = MCPConfig.from_dict(data["mcp"])

        if "security" in data:
            config.security = SecurityConfig.from_dict(data["security"])

        if "ui" in data:
            config.ui = UIConfig.from_dict(data["ui"])

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

    # Ensure directories exist
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.log_dir.mkdir(parents=True, exist_ok=True)

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


def reload_config() -> Config:
    """Reload configuration from file."""
    global _config
    _config = load_config()
    return _config


# Export all config classes
__all__ = [
    "Config",
    "LLMProviderConfig",
    "OllamaConfig",
    "GroqConfig",
    "MCPConfig",
    "ExternalServerConfig",
    "SecurityConfig",
    "UIConfig",
    "load_config",
    "save_config",
    "get_config",
    "set_config",
    "reload_config",
]
