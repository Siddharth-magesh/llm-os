"""
NL-Shell UI Module

Provides the terminal user interface for LLM-OS using Textual.
"""

from llm_os.ui.app import NLShellApp, run_app
from llm_os.ui.widgets import (
    MessageDisplay,
    InputPrompt,
    StatusBar,
    ToolProgress,
    WelcomeBanner,
    HelpPanel,
    ConfirmDialog,
    ChatMessage,
    CodeBlock,
    MessageRole,
)

__all__ = [
    # App
    "NLShellApp",
    "run_app",
    # Widgets
    "MessageDisplay",
    "InputPrompt",
    "StatusBar",
    "ToolProgress",
    "WelcomeBanner",
    "HelpPanel",
    "ConfirmDialog",
    "ChatMessage",
    "CodeBlock",
    "MessageRole",
]
