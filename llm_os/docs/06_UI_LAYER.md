# UI Layer Documentation

## Overview

The UI Layer provides a terminal-based user interface using the Textual framework. It offers a chat-style interface for natural language interaction.

## Main Application

### NLShellApp (`ui/app.py`)

The main application class.

```python
from llm_os.ui import NLShellApp, run_app

# Simple usage
app = NLShellApp()
app.run()

# With message handler
async def handle_message(message: str) -> str:
    # Process the message and return response
    return f"Response to: {message}"

run_app(message_handler=handle_message)
```

### Key Bindings

| Key | Action |
|-----|--------|
| `Ctrl+C` | Cancel current operation |
| `Ctrl+D` | Quit application |
| `Ctrl+L` | Clear screen |
| `F1` | Show help |
| `F2` | Show status |

### Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help panel |
| `/clear` | Clear conversation |
| `/status` | Show system status |
| `/tools` | List available tools |
| `/quit` | Exit application |
| `/provider <name>` | Switch LLM provider |

## Widgets

### MessageDisplay

Scrollable container for chat messages.

```python
from llm_os.ui.widgets import MessageDisplay

display = MessageDisplay()

# Add messages
display.add_user_message("Hello!")
display.add_assistant_message("Hi there!")
display.add_system_message("System initialized.")
display.add_tool_message("Command completed successfully.")
display.add_error_message("An error occurred.")

# Update last message (for streaming)
display.update_last_message("Updated content...")

# Clear all
display.clear_messages()
```

### ChatMessage

Individual message widget with role-based styling.

```python
from llm_os.ui.widgets import ChatMessage, MessageRole

message = ChatMessage(
    content="This is the message text",
    role=MessageRole.ASSISTANT,
    timestamp=datetime.now(),
)
```

**Message Roles:**
- `USER` - User input (cyan border)
- `ASSISTANT` - LLM response (green border)
- `SYSTEM` - System messages (yellow border)
- `TOOL` - Tool results (green border)
- `ERROR` - Error messages (red border)

### InputPrompt

User input widget.

```python
from llm_os.ui.widgets import InputPrompt

prompt = InputPrompt(
    prompt="❯",
    placeholder="Type a message...",
)

# Focus the input
prompt.focus_input()

# Disable during processing
prompt.set_disabled(True)
```

**Events:**
- `InputPrompt.Submitted` - Fired when user presses Enter

### StatusBar

Bottom status bar showing system information.

```python
from llm_os.ui.widgets import StatusBar

status_bar = StatusBar()

# Update status
status_bar.set_status(
    provider="Ollama",
    model="llama3.2:3b",
    tool_count=25,
)

# Or update individually
status_bar.provider = "Anthropic"
status_bar.model = "claude-3-5-haiku"
```

### ToolProgress

Shows tool execution progress.

```python
from llm_os.ui.widgets import ToolProgress

progress = ToolProgress()

# Show progress
progress.start_tool("read_file")

# Mark complete
progress.complete_tool(success=True)

# Hide
progress.hide()
```

### WelcomeBanner

Welcome message shown on startup.

```python
from llm_os.ui.widgets import WelcomeBanner

banner = WelcomeBanner()
# Renders ASCII art banner with quick start tips
```

### HelpPanel

Help information panel.

```python
from llm_os.ui.widgets import HelpPanel

help_panel = HelpPanel()
# Renders markdown help content
```

### ConfirmDialog

Confirmation dialog for dangerous operations.

```python
from llm_os.ui.widgets import ConfirmDialog

dialog = ConfirmDialog(
    title="Delete File",
    message="Are you sure you want to delete important.txt?",
)

# Events:
# - ConfirmDialog.Confirmed
# - ConfirmDialog.Cancelled
```

### CodeBlock

Syntax-highlighted code display.

```python
from llm_os.ui.widgets import CodeBlock

code = CodeBlock(
    code="def hello():\n    print('Hello!')",
    language="python",
)
```

## Styling

The UI uses Textual's CSS-like styling system:

```python
class NLShellApp(App):
    CSS = """
    Screen {
        background: $background;
    }

    ChatMessage.user {
        background: $surface;
        border-left: thick $primary;
    }

    ChatMessage.assistant {
        background: $surface-darken-1;
        border-left: thick $secondary;
    }

    StatusBar {
        dock: bottom;
        height: 1;
        background: $primary-darken-3;
    }
    """
```

## Customization

### Custom Message Handler

```python
from llm_os.ui import NLShellApp

class MyApp(NLShellApp):
    async def on_input_prompt_submitted(self, event):
        message = event.value.strip()

        # Custom preprocessing
        if message.startswith("!"):
            await self.handle_special_command(message)
            return

        # Default handling
        await super().on_input_prompt_submitted(event)

    async def handle_special_command(self, cmd):
        self.add_system_message(f"Special: {cmd}")
```

### Custom Widgets

```python
from textual.widget import Widget
from textual.reactive import reactive

class CustomWidget(Widget):
    DEFAULT_CSS = """
    CustomWidget {
        padding: 1;
        background: $surface;
    }
    """

    value = reactive("")

    def render(self):
        return f"Custom: {self.value}"
```

## CLI Modes

### TUI Mode (Default)

```bash
llm-os
```

Full terminal UI with all widgets.

### CLI Mode

```bash
llm-os --no-ui
```

Simple command-line interface without TUI.

### Single Command Mode

```bash
llm-os -c "list files in home directory"
```

Execute one command and exit.

## Application Lifecycle

```
1. NLShellApp instantiated
2. compose() creates widget tree
3. on_mount() called
   - Focus input
   - Set up timers
4. Event loop runs
   - Handle user input
   - Process messages
   - Update UI
5. Exit on quit command
```
