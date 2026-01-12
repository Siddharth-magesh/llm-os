"""
OSSARTH Terminal UI - Redesigned based on Claude Code style
"""
from __future__ import annotations

import asyncio
import platform
import subprocess
from typing import Any, Callable, Coroutine
from rich.console import RenderableType
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.align import Align

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, ScrollableContainer
from textual.widgets import Static, Input
from textual.binding import Binding


class HeaderBar(Static):
    """Clean header bar like Claude Code."""

    def __init__(self, provider: str = "Unknown", model: str = "Unknown") -> None:
        super().__init__()
        self.provider = provider
        self.model = model

    def render(self) -> RenderableType:
        """Render header with left and right sections."""
        # Left side - Logo and branding
        left = Text.from_markup(
            f"[bold cyan]OSSARTH[/] [dim]v0.1.0[/]\n"
            f"[dim]Natural Language Operating System[/]"
        )

        # Right side - Configuration
        right = Text.from_markup(
            f"[bold]Configuration[/]\n"
            f"Provider: [cyan]{self.provider}[/]\n"
            f"Model: [cyan]{self.model}[/]\n"
            f"Status: [green]Ready[/]\n"
            f"OS: [white]{platform.system()} {platform.release()}[/]"
        )

        # Create columns for side-by-side layout
        return Columns([left, right], expand=True, padding=(0, 2))


class OutputArea(ScrollableContainer):
    """Output area with automatic scrolling."""

    DEFAULT_CSS = """
    OutputArea {
        height: 1fr;
        padding: 0 2;
        background: #1e1e1e;
    }

    OutputArea > Static {
        margin-bottom: 1;
    }
    """

    def add_line(self, content: str, role: str = "assistant") -> None:
        """Add a line to output."""
        widget = Static()

        if role == "user":
            widget.update(Text(f"❯ {content}", style="bold #5a9ac5"))
        elif role == "system":
            widget.update(Text(content, style="#d0d0d0"))
        elif role == "error":
            widget.update(Text(f"✗ {content}", style="bold red"))
        else:
            # Assistant output
            widget.update(Text(content, style="#e0e0e0"))

        self.mount(widget)
        self.scroll_end(animate=False)

    def update_last_line(self, content: str) -> None:
        """Update last line for streaming."""
        if self.children:
            last = self.children[-1]
            if isinstance(last, Static):
                last.update(Text(content, style="#e0e0e0"))


class InputBar(Static):
    """Input bar container."""

    DEFAULT_CSS = """
    InputBar {
        height: 3;
        dock: bottom;
        background: #1e1e1e;
        padding: 0 2;
    }
    """

    def compose(self) -> ComposeResult:
        """Create input widget."""
        yield Input(placeholder="❯ Type your command...", id="prompt")


class NLShellApp(App):
    """OSSARTH - Natural Language OS Interface"""

    TITLE = "OSSARTH"

    CSS = """
    Screen {
        background: #1e1e1e;
    }

    HeaderBar {
        height: auto;
        padding: 1 2;
        background: #1e1e1e;
        border-bottom: solid #2a4a6a;
        margin-bottom: 1;
    }

    OutputArea {
        background: #1e1e1e;
    }

    InputBar {
        background: #1e1e1e;
        border-top: solid #2a4a6a;
    }

    Input {
        height: 1;
        background: #1e1e1e;
        border: none;
        padding: 0;
        color: #ffffff;
    }

    Input:focus {
        border: none;
        background: #1e1e1e;
    }

    Input > .input--placeholder {
        color: #808080;
    }

    Static {
        color: #e0e0e0;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+d", "quit", "Quit", show=False),
        Binding("ctrl+l", "clear", "Clear", show=False),
    ]

    def __init__(
        self,
        message_handler: Callable[[str], Coroutine[Any, Any, str]] | None = None,
        stream_handler: Any | None = None,
        provider: str = "Unknown",
        model: str = "Unknown",
        llmos_instance: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize OSSARTH."""
        super().__init__(**kwargs)
        self._message_handler = message_handler
        self._stream_handler = stream_handler
        self._processing = False
        self._provider = provider
        self._model = model
        self._llmos = llmos_instance

    def compose(self) -> ComposeResult:
        """Create UI components."""
        yield HeaderBar(provider=self._provider, model=self._model)
        yield OutputArea(id="output")
        yield InputBar()

    def on_mount(self) -> None:
        """Show startup message."""
        output = self.query_one("#output", OutputArea)
        output.add_line("Type your command or /help for assistance.\n", "system")

        # Focus input
        self.set_timer(0.1, lambda: self.query_one("#prompt", Input).focus())

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        if self._processing:
            return

        message = event.value.strip()
        if not message:
            return

        # Clear input
        event.input.value = ""

        # Show user input
        output = self.query_one("#output", OutputArea)
        output.add_line(message, "user")

        # Handle CLI bypass (commands starting with !)
        if message.startswith("!"):
            await self._handle_cli_command(message[1:].strip())
            return

        # Handle slash commands
        if message.startswith("/"):
            await self._handle_command(message)
            return

        # Process message
        await self._process_message(message)

    async def _process_message(self, message: str) -> None:
        """Process user message."""
        self._processing = True
        output = self.query_one("#output", OutputArea)

        try:
            if self._stream_handler:
                # Streaming response
                response = ""
                output.add_line("")  # Placeholder
                async for chunk in self._stream_handler(message):
                    response += chunk
                    output.update_last_line(response)
            elif self._message_handler:
                # Non-streaming response
                response = await self._message_handler(message)
                output.add_line(response)
            else:
                output.add_line("No backend configured.", "error")
        except Exception as e:
            output.add_line(f"Error: {str(e)}", "error")
        finally:
            output.add_line("", "system")  # Spacing
            self._processing = False
            self.query_one("#prompt", Input).focus()

    async def _handle_command(self, cmd: str) -> None:
        """Handle slash commands."""
        output = self.query_one("#output", OutputArea)
        cmd_lower = cmd.lower()

        if cmd_lower in ("/help", "/h"):
            help_text = """Available Commands:
  /help     - Show this help
  /clear    - Clear screen
  /status   - Show system status
  /config   - Show configuration
  /provider <name> - Switch provider (groq/ollama/openrouter)
  /model <name>    - Switch model
  /quit     - Exit OSSARTH

CLI Bypass:
  !<command> - Execute shell command directly
  Examples: !dir | !ls -la | !git status | !python --version

Natural Language:
  Just type what you want to do:
  "list files" | "show system info" | "read file.txt"

Shortcuts: Ctrl+C/D=Quit | Ctrl+L=Clear"""
            output.add_line(help_text, "system")

        elif cmd_lower in ("/clear", "/cls"):
            output.remove_children()
            output.add_line("Screen cleared.\n", "system")

        elif cmd_lower in ("/status", "/s"):
            status = f"""System Status:
  Provider: {self._provider}
  Model: {self._model}
  Processing: {'Yes' if self._processing else 'No'}
  Platform: {platform.system()} {platform.release()}"""
            output.add_line(status, "system")

        elif cmd_lower in ("/config", "/cfg"):
            await self._show_config()

        elif cmd_lower.startswith("/provider "):
            provider_name = cmd[10:].strip()
            await self._switch_provider(provider_name)

        elif cmd_lower.startswith("/model "):
            model_name = cmd[7:].strip()
            await self._switch_model(model_name)

        elif cmd_lower in ("/quit", "/exit", "/q"):
            self.exit()

        else:
            output.add_line(f"Unknown command: {cmd}", "error")
            output.add_line("Type /help for available commands.", "system")

        output.add_line("", "system")

    async def _handle_cli_command(self, cmd: str) -> None:
        """Handle CLI bypass commands (starting with !)."""
        output = self.query_one("#output", OutputArea)

        if not cmd:
            output.add_line("No command specified.", "error")
            output.add_line("", "system")
            return

        try:
            # Execute command using subprocess
            # Use shell=True for Windows compatibility
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )

            stdout, stderr = await process.communicate()

            # Display output
            if stdout:
                output.add_line(stdout.decode("utf-8", errors="replace"), "system")
            if stderr:
                output.add_line(stderr.decode("utf-8", errors="replace"), "error")

            # Show return code if non-zero
            if process.returncode != 0:
                output.add_line(f"Exit code: {process.returncode}", "error")

        except Exception as e:
            output.add_line(f"Command failed: {str(e)}", "error")

        output.add_line("", "system")

    async def _show_config(self) -> None:
        """Show current configuration."""
        output = self.query_one("#output", OutputArea)

        if not self._llmos:
            output.add_line("Configuration not available.", "error")
            return

        try:
            from config import get_config
            config = get_config()

            config_text = f"""Current Configuration:
  Provider: {config.default_provider}

  Groq:
    Enabled: {config.groq.enabled}
    Model: {config.groq.default_model}
    API Key: {'***' + config.groq.api_key[-8:] if config.groq.api_key else 'Not set'}

  OpenRouter:
    Enabled: {config.openrouter.enabled}
    Model: {config.openrouter.default_model}
    API Key: {'***' + config.openrouter.api_key[-8:] if config.openrouter.api_key else 'Not set'}

  Ollama:
    Enabled: {config.ollama.enabled}
    Model: {config.ollama.default_model}
    Base URL: {config.ollama.base_url}

  MCP:
    Auto Start: {config.mcp.auto_start}
    Servers: {', '.join(config.mcp.enabled_servers)}

  UI:
    Stream Responses: {config.ui.stream_responses}
    Show Tool Calls: {config.ui.show_tool_calls}"""

            output.add_line(config_text, "system")

        except Exception as e:
            output.add_line(f"Error reading config: {str(e)}", "error")

    async def _switch_provider(self, provider_name: str) -> None:
        """Switch LLM provider."""
        output = self.query_one("#output", OutputArea)

        if not self._llmos:
            output.add_line("LLM-OS instance not available.", "error")
            return

        provider_name = provider_name.lower()
        if provider_name not in ["groq", "ollama", "openrouter"]:
            output.add_line(f"Invalid provider: {provider_name}", "error")
            output.add_line("Available providers: groq, ollama, openrouter", "system")
            return

        try:
            from config import get_config, save_config

            # Update configuration
            config = get_config()
            config.default_provider = provider_name

            # Save config
            save_config(config)

            # Update internal state
            self._provider = provider_name

            # Update header
            header = self.query_one(HeaderBar)
            header.provider = provider_name

            output.add_line(f"Provider switched to: {provider_name}", "system")
            output.add_line("Restart recommended for changes to take full effect.", "system")

        except Exception as e:
            output.add_line(f"Error switching provider: {str(e)}", "error")

    async def _switch_model(self, model_name: str) -> None:
        """Switch LLM model."""
        output = self.query_one("#output", OutputArea)

        if not self._llmos:
            output.add_line("LLM-OS instance not available.", "error")
            return

        try:
            from config import get_config, save_config

            config = get_config()
            provider = config.default_provider

            # Update model for current provider
            if provider == "groq":
                config.groq.default_model = model_name
            elif provider == "ollama":
                config.ollama.default_model = model_name
            elif provider == "openrouter":
                config.openrouter.default_model = model_name

            # Save config
            save_config(config)

            # Update internal state
            self._model = model_name

            # Update header
            header = self.query_one(HeaderBar)
            header.model = model_name

            output.add_line(f"Model switched to: {model_name}", "system")
            output.add_line("Restart recommended for changes to take full effect.", "system")

        except Exception as e:
            output.add_line(f"Error switching model: {str(e)}", "error")

    def action_clear(self) -> None:
        """Clear screen."""
        output = self.query_one("#output", OutputArea)
        output.remove_children()
        output.add_line("Screen cleared.\n", "system")


def run_app(
    message_handler: Any | None = None,
    stream_handler: Any | None = None,
    provider: str = "Unknown",
    model: str = "Unknown",
    llmos_instance: Any | None = None,
    **kwargs: Any,
) -> None:
    """Run OSSARTH application."""
    app = NLShellApp(
        message_handler=message_handler,
        stream_handler=stream_handler,
        provider=provider,
        model=model,
        llmos_instance=llmos_instance,
        **kwargs
    )
    app.run()


if __name__ == "__main__":
    run_app()
