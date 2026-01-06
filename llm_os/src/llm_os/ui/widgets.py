"""
NL-Shell UI Widgets

Custom Textual widgets for the LLM-OS terminal interface.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from rich.console import RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer, Vertical, Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Input, Label, ProgressBar, Button


class MessageRole:
    """Message role constants."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    ERROR = "error"


class ChatMessage(Static):
    """A single chat message in the conversation."""

    DEFAULT_CSS = """
    ChatMessage {
        margin: 1 0;
        padding: 0 1;
    }

    ChatMessage.user {
        background: $surface;
        border-left: thick $primary;
    }

    ChatMessage.assistant {
        background: $surface-darken-1;
        border-left: thick $secondary;
    }

    ChatMessage.system {
        background: $surface-darken-2;
        border-left: thick $warning;
        color: $text-muted;
    }

    ChatMessage.tool {
        background: $surface-darken-1;
        border-left: thick $success;
    }

    ChatMessage.error {
        background: $error-darken-3;
        border-left: thick $error;
    }
    """

    def __init__(
        self,
        content: str,
        role: str = MessageRole.ASSISTANT,
        timestamp: datetime | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a chat message.

        Args:
            content: Message content (supports markdown)
            role: Message role (user, assistant, system, tool, error)
            timestamp: Message timestamp
        """
        super().__init__(**kwargs)
        self.content = content
        self.role = role
        self.timestamp = timestamp or datetime.now()
        self.add_class(role)

    def render(self) -> RenderableType:
        """Render the message content."""
        # Format header
        role_labels = {
            MessageRole.USER: "You",
            MessageRole.ASSISTANT: "Assistant",
            MessageRole.SYSTEM: "System",
            MessageRole.TOOL: "Tool Result",
            MessageRole.ERROR: "Error",
        }

        header = Text()
        header.append(f"{role_labels.get(self.role, 'Message')} ", style="bold")
        header.append(f"({self.timestamp.strftime('%H:%M')})", style="dim")

        # Render content as markdown for assistant messages
        if self.role in (MessageRole.ASSISTANT, MessageRole.SYSTEM):
            try:
                content = Markdown(self.content)
            except Exception:
                content = Text(self.content)
        else:
            content = Text(self.content)

        return Panel(
            content,
            title=header,
            title_align="left",
            border_style="dim",
        )


class MessageDisplay(ScrollableContainer):
    """Scrollable container for chat messages."""

    DEFAULT_CSS = """
    MessageDisplay {
        height: 1fr;
        scrollbar-gutter: stable;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the message display."""
        super().__init__(**kwargs)
        self._messages: list[ChatMessage] = []

    def add_message(
        self,
        content: str,
        role: str = MessageRole.ASSISTANT,
    ) -> ChatMessage:
        """Add a message to the display."""
        message = ChatMessage(content, role)
        self._messages.append(message)
        self.mount(message)
        self.scroll_end(animate=True)
        return message

    def add_user_message(self, content: str) -> ChatMessage:
        """Add a user message."""
        return self.add_message(content, MessageRole.USER)

    def add_assistant_message(self, content: str) -> ChatMessage:
        """Add an assistant message."""
        return self.add_message(content, MessageRole.ASSISTANT)

    def add_system_message(self, content: str) -> ChatMessage:
        """Add a system message."""
        return self.add_message(content, MessageRole.SYSTEM)

    def add_tool_message(self, content: str) -> ChatMessage:
        """Add a tool result message."""
        return self.add_message(content, MessageRole.TOOL)

    def add_error_message(self, content: str) -> ChatMessage:
        """Add an error message."""
        return self.add_message(content, MessageRole.ERROR)

    def clear_messages(self) -> None:
        """Clear all messages."""
        for message in self._messages:
            message.remove()
        self._messages.clear()

    def update_last_message(self, content: str) -> None:
        """Update the last message (for streaming)."""
        if self._messages:
            self._messages[-1].content = content
            self._messages[-1].refresh()


class InputPrompt(Widget):
    """Input prompt for user commands."""

    DEFAULT_CSS = """
    InputPrompt {
        dock: bottom;
        height: auto;
        padding: 1;
        background: $surface;
        border-top: solid $primary;
    }

    InputPrompt Input {
        width: 1fr;
    }

    InputPrompt .prompt-label {
        color: $primary;
        text-style: bold;
        padding-right: 1;
    }
    """

    class Submitted(Message):
        """Message sent when input is submitted."""

        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    def __init__(
        self,
        prompt: str = "❯",
        placeholder: str = "Type a message...",
        **kwargs: Any,
    ) -> None:
        """Initialize the input prompt."""
        super().__init__(**kwargs)
        self.prompt = prompt
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        """Compose the input prompt."""
        with Horizontal():
            yield Label(self.prompt, classes="prompt-label")
            yield Input(placeholder=self.placeholder, id="command-input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.value.strip():
            self.post_message(self.Submitted(event.value))
            event.input.value = ""

    def focus_input(self) -> None:
        """Focus the input field."""
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()

    def set_disabled(self, disabled: bool) -> None:
        """Enable or disable the input."""
        input_widget = self.query_one("#command-input", Input)
        input_widget.disabled = disabled


class StatusBar(Widget):
    """Status bar showing system information."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $primary-darken-3;
        color: $text;
    }

    StatusBar .status-item {
        padding: 0 2;
    }

    StatusBar .status-provider {
        color: $success;
    }

    StatusBar .status-model {
        color: $secondary;
    }

    StatusBar .status-tools {
        color: $warning;
    }

    StatusBar .status-time {
        dock: right;
        color: $text-muted;
    }
    """

    provider = reactive("Not connected")
    model = reactive("")
    tool_count = reactive(0)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the status bar."""
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        """Compose the status bar."""
        with Horizontal():
            yield Label("", id="provider", classes="status-item status-provider")
            yield Label("", id="model", classes="status-item status-model")
            yield Label("", id="tools", classes="status-item status-tools")
            yield Label("", id="time", classes="status-item status-time")

    def on_mount(self) -> None:
        """Start updating time."""
        self.set_interval(1, self._update_time)
        self._update_display()

    def _update_time(self) -> None:
        """Update the time display."""
        time_label = self.query_one("#time", Label)
        time_label.update(datetime.now().strftime("%H:%M:%S"))

    def _update_display(self) -> None:
        """Update all status displays."""
        provider_label = self.query_one("#provider", Label)
        model_label = self.query_one("#model", Label)
        tools_label = self.query_one("#tools", Label)

        provider_label.update(f"⚡ {self.provider}")
        if self.model:
            model_label.update(f"🤖 {self.model}")
        if self.tool_count > 0:
            tools_label.update(f"🔧 {self.tool_count} tools")

    def watch_provider(self) -> None:
        """React to provider changes."""
        self._update_display()

    def watch_model(self) -> None:
        """React to model changes."""
        self._update_display()

    def watch_tool_count(self) -> None:
        """React to tool count changes."""
        self._update_display()

    def set_status(
        self,
        provider: str | None = None,
        model: str | None = None,
        tool_count: int | None = None,
    ) -> None:
        """Update status values."""
        if provider is not None:
            self.provider = provider
        if model is not None:
            self.model = model
        if tool_count is not None:
            self.tool_count = tool_count


class ToolProgress(Widget):
    """Widget showing tool execution progress."""

    DEFAULT_CSS = """
    ToolProgress {
        height: auto;
        padding: 1;
        background: $surface-darken-1;
        border: solid $primary-darken-2;
        margin: 1 0;
    }

    ToolProgress .tool-name {
        text-style: bold;
        color: $primary;
    }

    ToolProgress .tool-status {
        color: $text-muted;
    }

    ToolProgress ProgressBar {
        margin-top: 1;
    }

    ToolProgress.hidden {
        display: none;
    }
    """

    is_active = reactive(False)
    tool_name = reactive("")
    status_text = reactive("Waiting...")

    def __init__(self, **kwargs: Any) -> None:
        """Initialize tool progress widget."""
        super().__init__(**kwargs)
        self.add_class("hidden")

    def compose(self) -> ComposeResult:
        """Compose the progress widget."""
        yield Label("", id="tool-name", classes="tool-name")
        yield Label("", id="status", classes="tool-status")
        yield ProgressBar(id="progress", show_eta=False)

    def watch_is_active(self) -> None:
        """Show or hide based on active state."""
        if self.is_active:
            self.remove_class("hidden")
        else:
            self.add_class("hidden")

    def watch_tool_name(self) -> None:
        """Update tool name display."""
        label = self.query_one("#tool-name", Label)
        label.update(f"🔧 Executing: {self.tool_name}")

    def watch_status_text(self) -> None:
        """Update status text."""
        label = self.query_one("#status", Label)
        label.update(self.status_text)

    def start_tool(self, name: str) -> None:
        """Start showing tool execution."""
        self.tool_name = name
        self.status_text = "Running..."
        self.is_active = True
        progress = self.query_one("#progress", ProgressBar)
        progress.update(progress=None)  # Indeterminate

    def complete_tool(self, success: bool = True) -> None:
        """Mark tool execution as complete."""
        self.status_text = "Complete" if success else "Failed"
        progress = self.query_one("#progress", ProgressBar)
        progress.update(progress=100)

    def hide(self) -> None:
        """Hide the progress widget."""
        self.is_active = False


class WelcomeBanner(Static):
    """Welcome banner shown on startup."""

    DEFAULT_CSS = """
    WelcomeBanner {
        padding: 1 2;
        background: $primary-darken-3;
        margin: 1;
        text-align: center;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize welcome banner."""
        super().__init__(**kwargs)

    def render(self) -> RenderableType:
        """Render the welcome banner."""
        banner = Text()
        banner.append("╔══════════════════════════════════════╗\n", style="bold cyan")
        banner.append("║       ", style="bold cyan")
        banner.append("LLM-OS", style="bold white")
        banner.append(" Natural Language Shell   ║\n", style="bold cyan")
        banner.append("╚══════════════════════════════════════╝\n", style="bold cyan")
        banner.append("\n")
        banner.append("Welcome! I can help you interact with your system using natural language.\n", style="dim")
        banner.append("Type your command or question, or try:\n\n", style="dim")
        banner.append("  • ", style="dim")
        banner.append("'list files in my home directory'\n", style="italic")
        banner.append("  • ", style="dim")
        banner.append("'show system information'\n", style="italic")
        banner.append("  • ", style="dim")
        banner.append("'open firefox'\n", style="italic")
        banner.append("  • ", style="dim")
        banner.append("'help' for more commands\n", style="italic")
        return banner


class HelpPanel(Widget):
    """Help panel showing available commands."""

    DEFAULT_CSS = """
    HelpPanel {
        padding: 1 2;
        background: $surface;
        border: solid $primary;
        margin: 1;
    }
    """

    def render(self) -> RenderableType:
        """Render the help panel."""
        help_text = """
# LLM-OS Help

## Natural Language Commands
Just type what you want to do in plain English:
- "List files in the current directory"
- "Show me the contents of config.py"
- "Create a new folder called projects"
- "What's my system memory usage?"

## Special Commands
- `/help` - Show this help
- `/clear` - Clear the conversation
- `/status` - Show system status
- `/tools` - List available tools
- `/quit` or `/exit` - Exit the application

## Keyboard Shortcuts
- `Ctrl+C` - Cancel current operation
- `Ctrl+D` - Exit
- `Ctrl+L` - Clear screen
- `Up/Down` - Navigate command history

## Tips
- Be specific about what you want
- You can reference previous context ("open it", "delete that file")
- Ask follow-up questions naturally
"""
        return Markdown(help_text)


class ConfirmDialog(Widget):
    """Confirmation dialog for dangerous operations."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
        padding: 2;
        background: $surface;
        border: thick $warning;
        width: 60;
        height: auto;
    }

    ConfirmDialog .title {
        text-style: bold;
        color: $warning;
        text-align: center;
        padding-bottom: 1;
    }

    ConfirmDialog .message {
        padding: 1;
    }

    ConfirmDialog .buttons {
        align: center middle;
        padding-top: 1;
    }

    ConfirmDialog Button {
        margin: 0 1;
    }
    """

    class Confirmed(Message):
        """Sent when user confirms."""
        pass

    class Cancelled(Message):
        """Sent when user cancels."""
        pass

    def __init__(
        self,
        title: str = "Confirm Action",
        message: str = "Are you sure?",
        **kwargs: Any,
    ) -> None:
        """Initialize confirmation dialog."""
        super().__init__(**kwargs)
        self.title_text = title
        self.message_text = message

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        yield Label(f"⚠️  {self.title_text}", classes="title")
        yield Label(self.message_text, classes="message")
        with Horizontal(classes="buttons"):
            yield Button("Cancel", variant="default", id="cancel")
            yield Button("Confirm", variant="warning", id="confirm")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "confirm":
            self.post_message(self.Confirmed())
        else:
            self.post_message(self.Cancelled())
        self.remove()


class CodeBlock(Static):
    """Widget for displaying code with syntax highlighting."""

    DEFAULT_CSS = """
    CodeBlock {
        padding: 1;
        margin: 1 0;
        background: $surface-darken-2;
    }
    """

    def __init__(
        self,
        code: str,
        language: str = "python",
        **kwargs: Any,
    ) -> None:
        """Initialize code block."""
        super().__init__(**kwargs)
        self.code = code
        self.language = language

    def render(self) -> RenderableType:
        """Render the code with syntax highlighting."""
        return Syntax(
            self.code,
            self.language,
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )
