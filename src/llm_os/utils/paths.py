"""
Path resolution for LLM-OS.

This module provides path resolution that separates:
1. System installation directory (read-only core)
2. User data directory (per-user config, history, logs)
3. Working directory (where user commands execute)
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_system_dir() -> Path:
    """
    Get system installation directory.

    In production: /opt/llm-os
    In development: ~/llm-os (or wherever installed)

    Returns:
        Path to system installation directory
    """
    # Try environment variable first
    if env_path := os.environ.get('LLM_OS_HOME'):
        return Path(env_path)

    # Try production path
    prod_path = Path('/opt/llm-os')
    if prod_path.exists():
        return prod_path

    # Fall back to package directory (development)
    # This is where the code is actually installed
    package_dir = Path(__file__).parent.parent.parent
    return package_dir


def get_user_dir() -> Path:
    """
    Get user data directory.

    This is where user-specific configuration, history, logs, and cache are stored.
    Default: ~/.llm-os

    Returns:
        Path to user data directory
    """
    default = Path.home() / '.llm-os'
    user_dir = Path(os.environ.get('LLM_OS_USER_DIR', default))
    return user_dir


def get_working_dir() -> Path:
    """
    Get current working directory where user commands execute.

    This is the user's current directory (pwd), NOT the system directory.
    User commands should execute here.

    Returns:
        Path to current working directory
    """
    return Path.cwd()


def get_config_dir() -> Path:
    """
    Get configuration directory.

    Returns:
        Path to config directory (system or package)
    """
    # Try system config directory first
    system_config = get_system_dir() / 'config'
    if system_config.exists():
        return system_config

    # Fall back to package config directory
    package_config = get_system_dir() / 'config'
    return package_config


def get_user_config_file() -> Path:
    """Get user configuration file path."""
    return get_user_dir() / 'config.yaml'


def get_user_history_file() -> Path:
    """Get user history file path."""
    return get_user_dir() / 'history.json'


def get_user_log_dir() -> Path:
    """Get user log directory path."""
    return get_user_dir() / 'logs'


def get_user_cache_dir() -> Path:
    """Get user cache directory path."""
    return get_user_dir() / 'cache'


def ensure_user_dirs() -> None:
    """
    Ensure user directories exist.

    Creates:
    - ~/.llm-os/
    - ~/.llm-os/logs/
    - ~/.llm-os/cache/
    - ~/.llm-os/cache/context/
    """
    user_dir = get_user_dir()

    # Create main user directory
    user_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (user_dir / 'logs').mkdir(exist_ok=True)
    (user_dir / 'cache').mkdir(exist_ok=True)
    (user_dir / 'cache' / 'context').mkdir(exist_ok=True)

    logger.debug(f"User directories initialized at: {user_dir}")


def is_development_mode() -> bool:
    """
    Check if running in development mode.

    Returns:
        True if running from development directory
    """
    system_dir = get_system_dir()

    # Check if we're in a git repository (development)
    git_dir = system_dir / '.git'
    if git_dir.exists():
        return True

    # Check if installed in /opt (production)
    if str(system_dir).startswith('/opt/llm-os'):
        return False

    # Check if installed via pip (user or system)
    # If we're in site-packages, we're in production
    if 'site-packages' in str(system_dir) or 'dist-packages' in str(system_dir):
        return False

    # Default to development
    return True


def log_paths_info() -> None:
    """Log information about current path configuration."""
    logger.info("=" * 60)
    logger.info("LLM-OS Path Configuration")
    logger.info("=" * 60)
    logger.info(f"System Directory:    {get_system_dir()}")
    logger.info(f"Config Directory:    {get_config_dir()}")
    logger.info(f"User Directory:      {get_user_dir()}")
    logger.info(f"Working Directory:   {get_working_dir()}")
    logger.info(f"Development Mode:    {is_development_mode()}")
    logger.info("=" * 60)


# For convenience, pre-compute these at module load
SYSTEM_DIR = get_system_dir()
USER_DIR = get_user_dir()
WORKING_DIR = get_working_dir()


__all__ = [
    'get_system_dir',
    'get_user_dir',
    'get_working_dir',
    'get_config_dir',
    'get_user_config_file',
    'get_user_history_file',
    'get_user_log_dir',
    'get_user_cache_dir',
    'ensure_user_dirs',
    'is_development_mode',
    'log_paths_info',
    'SYSTEM_DIR',
    'USER_DIR',
    'WORKING_DIR',
]
