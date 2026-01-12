"""
LLM-OS: Natural Language Operating System

A complete operating system interface powered by Large Language Models,
enabling users to control their computer using natural language commands.
"""

__version__ = "0.1.0"
__author__ = "LLM-OS Team"

from config import Config, get_config, load_config
from llm_os.core import LLMOS, LLMOSConfig, create_llmos

__all__ = [
    "__version__",
    # Configuration
    "Config",
    "get_config",
    "load_config",
    # Core
    "LLMOS",
    "LLMOSConfig",
    "create_llmos",
]


def main() -> int:
    """Main entry point for the CLI."""
    from llm_os.cli import main as cli_main
    return cli_main()
