"""
NL-Shell Main Application

The main Textual application for LLM-OS natural language shell.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header

from llm_os.ui.widgets import (
    MessageDisplay,
    InputPrompt,
    StatusBar,
    ToolProgress,
    WelcomeBanner,
    HelpPanel,
    ConfirmDialog,
    MessageRole,
)


logger = logging.getLogger(__name__)


# Type for message handlers
MessageHandler = Callable[[str], Coroutine[Any, Any, str]]


class MainScreen(Screen):
    """Main conversation screen."""

    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }

    MainScreen #main-container {
        height: 1fr;
    }

    MainScreen #messages {
        height: 1fr;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the main screen."""
        yield Header(show_clock=True)
        with Container(id="main-container"):
            yield WelcomeBanner()
            yield MessageDisplay(id="messages")
            yield ToolProgress(id="tool-progress")
        yield InputPrompt(id="input-prompt")
        yield StatusBar(id="status-bar")
        yield Footer()


class NLShellApp(App):
    """
    Natural Language Shell Application.

    The main terminal UI for LLM-OS, providing a chat-like interface
    for natural language system interaction.
    """

    TITLE = "LLM-OS"
    SUB_TITLE = "Natural Language Shell"
    CSS_PATH = None  # Using inline CSS

    CSS = """
    Screen {
        background: $background;
    }

    Header {
        background: $primary-darken-3;
    }

    Footer {
        background: $primary-darken-3;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "cancel", "Cancel", show=True),
        Binding("ctrl+d", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_screen", "Clear", show=True),
        Binding("f1", "help", "Help", show=True),
        Binding("f2", "status", "Status", show=True),
    ]

    def __init__(
        self,
        message_handler: MessageHandler | None = None,
        confirmation_handler: Callable[[str, str], Coroutine[Any, Any, bool]] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the application.

        Args:
            message_handler: Async function to handle user messages
            confirmation_handler: Async function for confirmations
        """
        super().__init__(**kwargs)
        self._message_handler = message_handler
        self._confirmation_handler = confirmation_handler
        self._processing = False
        self._current_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield MainScreen()

    def on_mount(self) -> None:
        """Handle application mount."""
        # Focus the input
        self.call_later(self._focus_input)

    def _focus_input(self) -> None:
        """Focus the input prompt."""
        try:
            input_prompt = self.query_one("#input-prompt", InputPrompt)
            input_prompt.focus_input()
        except Exception:
            pass

    async def on_input_prompt_submitted(self, event: InputPrompt.Submitted) -> None:
        """Handle user input submission."""
        message = event.value.strip()

        if not message:
            return

        # Check for special commands
        if message.startswith("/"):
            await self._handle_command(message)
            return

        # Add user message to display
        messages = self.query_one("#messages", MessageDisplay)
        messages.add_user_message(message)

        # Process with handler
        if self._message_handler:
            await self._process_message(message)
        else:
            messages.add_system_message(
                "No message handler configured. Running in demo mode."
            )

        self._focus_input()

    async def _handle_command(self, command: str) -> None:
        """Handle special slash commands."""
        messages = self.query_one("#messages", MessageDisplay)
        cmd = command.lower().strip()

        if cmd in ("/help", "/h", "/?"):
            await self.action_help()

        elif cmd in ("/clear", "/cls"):
            messages.clear_messages()
            messages.add_system_message("Conversation cleared.")

        elif cmd in ("/status", "/s"):
            await self.action_status()

        elif cmd in ("/quit", "/exit", "/q"):
            self.exit()

        elif cmd.startswith("/tools"):
            await self._show_tools()

        elif cmd.startswith("/provider"):
            # Change provider command
            parts = cmd.split(maxsplit=1)
            if len(parts) > 1:
                provider = parts[1]
                messages.add_system_message(f"Switching to provider: {provider}")
            else:
                messages.add_system_message("Usage: /provider <name>")

        else:
            messages.add_system_message(f"Unknown command: {command}")

    async def _process_message(self, message: str) -> None:
        """Process a user message."""
        if self._processing:
            return

        self._processing = True
        messages = self.query_one("#messages", MessageDisplay)
        input_prompt = self.query_one("#input-prompt", InputPrompt)
        input_prompt.set_disabled(True)

        try:
            # Add placeholder for response
            messages.add_assistant_message("Thinking...")

            # Call handler
            response = await self._message_handler(message)

            # Update with actual response
            messages.update_last_message(response)

        except asyncio.CancelledError:
            messages.update_last_message("*Cancelled*")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            messages.update_last_message(f"Error: {str(e)}")

        finally:
            self._processing = False
            input_prompt.set_disabled(False)
            self._focus_input()

    async def _show_tools(self) -> None:
        """Show available tools."""
        messages = self.query_one("#messages", MessageDisplay)
        messages.add_system_message(
            "Use `/tools` with a connected LLM to see available tools."
        )

    def action_cancel(self) -> None:
        """Cancel current operation."""
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            messages = self.query_one("#messages", MessageDisplay)
            messages.add_system_message("Operation cancelled.")

    def action_clear_screen(self) -> None:
        """Clear the screen."""
        messages = self.query_one("#messages", MessageDisplay)
        messages.clear_messages()

    async def action_help(self) -> None:
        """Show help."""
        messages = self.query_one("#messages", MessageDisplay)
        help_text = """## Available Commands

**Natural Language**: Just type what you want to do!
- "list files in the current directory"
- "show system information"
- "open firefox"

**Slash Commands**:
- `/help` - Show this help
- `/clear` - Clear conversation
- `/status` - Show system status
- `/tools` - List available tools
- `/quit` - Exit

**Keyboard Shortcuts**:
- `Ctrl+C` - Cancel operation
- `Ctrl+D` - Exit
- `Ctrl+L` - Clear screen
- `F1` - Help
- `F2` - Status"""
        messages.add_system_message(help_text)

    async def action_status(self) -> None:
        """Show status."""
        status_bar = self.query_one("#status-bar", StatusBar)
        messages = self.query_one("#messages", MessageDisplay)

        status_text = f"""## System Status
- **Provider**: {status_bar.provider}
- **Model**: {status_bar.model or 'Not set'}
- **Tools Available**: {status_bar.tool_count}"""

        messages.add_system_message(status_text)

    def set_message_handler(self, handler: MessageHandler) -> None:
        """Set the message handler."""
        self._message_handler = handler

    def set_confirmation_handler(
        self,
        handler: Callable[[str, str], Coroutine[Any, Any, bool]],
    ) -> None:
        """Set the confirmation handler."""
        self._confirmation_handler = handler

    def update_status(
        self,
        provider: str | None = None,
        model: str | None = None,
        tool_count: int | None = None,
    ) -> None:
        """Update status bar."""
        try:
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_status(provider, model, tool_count)
        except Exception:
            pass

    def show_tool_progress(self, tool_name: str) -> None:
        """Show tool execution progress."""
        try:
            progress = self.query_one("#tool-progress", ToolProgress)
            progress.start_tool(tool_name)
        except Exception:
            pass

    def hide_tool_progress(self, success: bool = True) -> None:
        """Hide tool execution progress."""
        try:
            progress = self.query_one("#tool-progress", ToolProgress)
            progress.complete_tool(success)
            # Hide after a short delay
            self.set_timer(1.0, progress.hide)
        except Exception:
            pass

    async def show_confirmation(
        self,
        title: str,
        message: str,
    ) -> bool:
        """Show a confirmation dialog."""
        if self._confirmation_handler:
            return await self._confirmation_handler(title, message)

        # Default: use built-in dialog
        result = asyncio.Event()
        confirmed = False

        def on_confirmed(_: ConfirmDialog.Confirmed) -> None:
            nonlocal confirmed
            confirmed = True
            result.set()

        def on_cancelled(_: ConfirmDialog.Cancelled) -> None:
            result.set()

        dialog = ConfirmDialog(title=title, message=message)
        dialog.on(ConfirmDialog.Confirmed, on_confirmed)
        dialog.on(ConfirmDialog.Cancelled, on_cancelled)

        await self.mount(dialog)
        await result.wait()

        return confirmed

    def add_message(
        self,
        content: str,
        role: str = MessageRole.ASSISTANT,
    ) -> None:
        """Add a message to the display."""
        try:
            messages = self.query_one("#messages", MessageDisplay)
            messages.add_message(content, role)
        except Exception:
            pass

    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.add_message(content, MessageRole.USER)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message."""
        self.add_message(content, MessageRole.ASSISTANT)

    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        self.add_message(content, MessageRole.SYSTEM)

    def add_error_message(self, content: str) -> None:
        """Add an error message."""
        self.add_message(content, MessageRole.ERROR)


def run_app(
    message_handler: MessageHandler | None = None,
    **kwargs: Any,
) -> None:
    """
    Run the NL-Shell application.

    Args:
        message_handler: Async function to handle user messages
        **kwargs: Additional arguments for the app
    """
    app = NLShellApp(message_handler=message_handler, **kwargs)
    app.run()


if __name__ == "__main__":
    # Demo mode
    async def demo_handler(message: str) -> str:
        await asyncio.sleep(1)  # Simulate processing
        return f"Demo response to: {message}\n\nIn production, this would be handled by the LLM."

    run_app(message_handler=demo_handler)
