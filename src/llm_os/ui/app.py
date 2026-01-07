"""
LLM-OS Terminal UI - Clean Implementation

Based on working simple_app.py pattern.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine
from rich.console import RenderableType
from rich.markdown import Markdown
from rich.panel import Panel

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static, Input, Footer, Header
from textual.binding import Binding


class ChatMessage(Static):
    """A single chat message widget."""

    def __init__(self, content: str, is_user: bool = False) -> None:
        """Initialize message."""
        super().__init__()
        self.content = content
        self.is_user = is_user

    def render(self) -> RenderableType:
        """Render the message."""
        style = "bold cyan" if self.is_user else "green"
        label = "You" if self.is_user else "Assistant"

        return Panel(
            Markdown(self.content) if not self.is_user else self.content,
            title=f"[{style}]{label}[/{style}]",
            border_style=style,
        )


class ChatDisplay(ScrollableContainer):
    """Scrollable chat message display."""

    DEFAULT_CSS = """
    ChatDisplay {
        height: 1fr;
        border: solid green;
        padding: 1;
    }

    ChatMessage {
        margin: 1;
    }
    """

    def add_message(self, content: str, is_user: bool = False) -> None:
        """Add a message to the display."""
        message = ChatMessage(content, is_user)
        self.mount(message)
        self.scroll_end(animate=False)

    def update_last_message(self, content: str) -> None:
        """Update the last message (for streaming)."""
        if self.children:
            last_message = self.children[-1]
            if isinstance(last_message, ChatMessage):
                last_message.content = content
                last_message.refresh()


class ChatInput(Input):
    """Custom input widget for chat."""

    DEFAULT_CSS = """
    ChatInput {
        dock: bottom;
        border: solid cyan;
        height: 3;
        padding: 0 1;
    }
    """


class NLShellApp(App):
    """LLM-OS Natural Language Shell - Terminal UI."""

    TITLE = "LLM-OS"
    SUB_TITLE = "Natural Language Shell"

    # Disable command palette
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Screen {
        background: $background;
    }

    Header {
        background: $primary;
    }

    Footer {
        background: $primary;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+d", "quit", "Quit", show=False),
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("f1", "help", "Help", show=True),
        Binding("f2", "status", "Status", show=True),
    ]

    def __init__(
        self,
        message_handler: Callable[[str], Coroutine[Any, Any, str]] | None = None,
        stream_handler: Any | None = None,
        confirmation_handler: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize app."""
        super().__init__(**kwargs)
        self._message_handler = message_handler
        self._stream_handler = stream_handler
        self._confirmation_handler = confirmation_handler
        self._processing = False
        self._provider = "Not connected"
        self._model = ""
        self._tool_count = 0

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield ChatDisplay(id="chat")
        yield ChatInput(placeholder="Type your message here...", id="input")
        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event."""
        # Add welcome message
        chat = self.query_one("#chat", ChatDisplay)
        welcome = """# Welcome to LLM-OS!

**Natural Language Operating System**

Type a message below to control your system with natural language.

## Keyboard Shortcuts
- **Ctrl+C** / **Ctrl+D** - Quit
- **Ctrl+L** - Clear chat
- **F1** - Help
- **F2** - Status

## Slash Commands
- `/help` - Show help
- `/clear` - Clear chat
- `/status` - Show status
- `/quit` - Exit

Try: "list files" or "show system info"
"""
        chat.add_message(welcome)

        # Focus input
        self.query_one("#input", ChatInput).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if self._processing:
            return

        message = event.value.strip()
        if not message:
            return

        # Clear input
        event.input.value = ""

        # Handle commands
        if message.startswith("/"):
            await self._handle_command(message)
            return

        # Add user message
        chat = self.query_one("#chat", ChatDisplay)
        chat.add_message(message, is_user=True)

        # Process message
        await self._process_message(message)

    async def _process_message(self, message: str) -> None:
        """Process user message."""
        self._processing = True
        chat = self.query_one("#chat", ChatDisplay)

        try:
            if self._stream_handler:
                # Streaming response
                response = ""
                # Add placeholder
                chat.add_message("")
                async for chunk in self._stream_handler(message):
                    response += chunk
                    chat.update_last_message(response)
            elif self._message_handler:
                # Non-streaming response
                response = await self._message_handler(message)
                chat.add_message(response)
            else:
                # Echo mode (for testing)
                chat.add_message(f"**Echo:** {message}\n\nThis is echo mode. No LLM handler configured.")
        except Exception as e:
            chat.add_message(f"**Error:** {str(e)}")
        finally:
            self._processing = False
            # Re-focus input
            self.query_one("#input", ChatInput).focus()

    async def _handle_command(self, cmd: str) -> None:
        """Handle slash commands."""
        chat = self.query_one("#chat", ChatDisplay)
        cmd_lower = cmd.lower()

        if cmd_lower in ("/help", "/h", "/?"):
            await self.action_help()
        elif cmd_lower in ("/clear", "/cls"):
            await self.action_clear()
        elif cmd_lower in ("/status", "/s"):
            await self.action_status()
        elif cmd_lower in ("/quit", "/exit", "/q"):
            self.exit()
        else:
            chat.add_message(f"Unknown command: `{cmd}`\n\nTry `/help` for available commands.")

    def action_clear(self) -> None:
        """Clear chat."""
        chat = self.query_one("#chat", ChatDisplay)
        chat.remove_children()
        chat.add_message("**Chat cleared.**")

    def action_help(self) -> None:
        """Show help."""
        chat = self.query_one("#chat", ChatDisplay)
        help_text = """# LLM-OS Help

## Natural Language Commands
Just type what you want to do:
- "list files in the current directory"
- "show system information"
- "what's the git status?"
- "find all python files"

## Slash Commands
- `/help` or `/h` - Show this help
- `/clear` or `/cls` - Clear chat history
- `/status` or `/s` - Show system status
- `/quit` or `/q` - Exit application

## Keyboard Shortcuts
- **Ctrl+C** / **Ctrl+D** - Quit
- **Ctrl+L** - Clear chat
- **F1** - Help
- **F2** - Status

## Examples
```
"list files"
"show system info"
"what branch am I on?"
"find all .py files and show git status"
```

Type naturally and let the AI handle it!
"""
        chat.add_message(help_text)

    def action_status(self) -> None:
        """Show status."""
        chat = self.query_one("#chat", ChatDisplay)
        status_text = f"""# System Status

- **Provider:** {self._provider}
- **Model:** {self._model or 'Not set'}
- **Tools Available:** {self._tool_count}
- **Processing:** {'Yes' if self._processing else 'No'}
"""
        chat.add_message(status_text)

    def update_status(
        self,
        provider: str | None = None,
        model: str | None = None,
        tool_count: int | None = None,
    ) -> None:
        """Update status information."""
        if provider is not None:
            self._provider = provider
        if model is not None:
            self._model = model
        if tool_count is not None:
            self._tool_count = tool_count

    def show_tool_progress(self, tool_name: str) -> None:
        """Show tool execution progress."""
        # For now, just add a message
        # Can be enhanced later with a progress widget
        pass

    def hide_tool_progress(self, success: bool = True) -> None:
        """Hide tool execution progress."""
        pass


def run_app(
    message_handler: Any | None = None,
    stream_handler: Any | None = None,
    **kwargs: Any,
) -> None:
    """Run the NL-Shell application."""
    app = NLShellApp(
        message_handler=message_handler,
        stream_handler=stream_handler,
        **kwargs
    )
    app.run()


if __name__ == "__main__":
    # Demo mode with echo
    run_app()
