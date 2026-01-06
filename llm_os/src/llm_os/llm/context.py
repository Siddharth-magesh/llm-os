"""
Context Manager

Manages conversation history, context window, and reference resolution.
"""

from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from llm_os.llm.base import Message, MessageRole, ToolCall


@dataclass
class ContextReference:
    """A reference to something mentioned in conversation."""
    type: str  # "file", "directory", "url", "application", "process"
    value: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextState:
    """Current state of the context."""
    working_directory: str = ""
    last_command: str = ""
    last_result: str = ""
    last_error: str | None = None
    active_application: str | None = None
    references: dict[str, ContextReference] = field(default_factory=dict)


class ContextManager:
    """
    Manages conversation context for the LLM.

    Features:
    - Message history management
    - Token counting and trimming
    - Reference resolution (pronouns, "it", "that", etc.)
    - Context state tracking
    - Persistence (optional)
    """

    # Average characters per token (rough estimate)
    CHARS_PER_TOKEN = 4

    # Reference patterns
    PRONOUN_PATTERNS = [
        (re.compile(r"\b(it|that|this)\b", re.IGNORECASE), ["file", "directory", "application"]),
        (re.compile(r"\b(them|those|these)\b", re.IGNORECASE), ["files", "directories"]),
        (re.compile(r"\bthe file\b", re.IGNORECASE), ["file"]),
        (re.compile(r"\bthe folder\b", re.IGNORECASE), ["directory"]),
        (re.compile(r"\bthe app(lication)?\b", re.IGNORECASE), ["application"]),
        (re.compile(r"\bthere\b", re.IGNORECASE), ["directory"]),
    ]

    def __init__(
        self,
        max_tokens: int = 8000,
        max_messages: int = 100,
        system_prompt: str | None = None,
        persist_path: Path | None = None,
    ):
        """
        Initialize the context manager.

        Args:
            max_tokens: Maximum tokens to keep in context
            max_messages: Maximum messages to keep
            system_prompt: System prompt to always include
            persist_path: Path to persist history (optional)
        """
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        self.system_prompt = system_prompt
        self.persist_path = persist_path

        self._messages: deque[Message] = deque(maxlen=max_messages)
        self._state = ContextState()
        self._tool_results: dict[str, Any] = {}

        # Load persisted history if available
        if persist_path and persist_path.exists():
            self._load_history()

    @property
    def state(self) -> ContextState:
        """Get current context state."""
        return self._state

    @property
    def message_count(self) -> int:
        """Get number of messages in context."""
        return len(self._messages)

    def add_user_message(self, content: str) -> Message:
        """Add a user message to the context."""
        # Extract references from the message
        self._extract_references(content)

        message = Message.user(content)
        self._messages.append(message)
        self._state.last_command = content

        self._trim_if_needed()
        self._persist_if_enabled()

        return message

    def add_assistant_message(
        self,
        content: str,
        tool_calls: list[ToolCall] | None = None
    ) -> Message:
        """Add an assistant message to the context."""
        message = Message.assistant(content, tool_calls)
        self._messages.append(message)
        self._state.last_result = content

        self._trim_if_needed()
        self._persist_if_enabled()

        return message

    def add_tool_result(
        self,
        tool_call_id: str,
        content: str,
        tool_name: str | None = None,
        is_error: bool = False
    ) -> Message:
        """Add a tool result to the context."""
        message = Message.tool_result(tool_call_id, content, tool_name)
        self._messages.append(message)

        # Store for reference resolution
        self._tool_results[tool_call_id] = {
            "content": content,
            "name": tool_name,
            "is_error": is_error,
        }

        if is_error:
            self._state.last_error = content
        else:
            self._state.last_error = None

        # Extract references from tool results
        self._extract_references_from_result(content, tool_name)

        self._trim_if_needed()
        self._persist_if_enabled()

        return message

    def get_messages_for_llm(self) -> list[Message]:
        """
        Get messages formatted for LLM API call.

        Returns messages with system prompt prepended.
        """
        messages: list[Message] = []

        # Add system prompt
        if self.system_prompt:
            messages.append(Message.system(self._build_system_prompt()))

        # Add conversation messages
        messages.extend(self._messages)

        return messages

    def _build_system_prompt(self) -> str:
        """Build system prompt with current context."""
        prompt_parts = [self.system_prompt or ""]

        # Add current state information
        state_info = []

        if self._state.working_directory:
            state_info.append(f"Current directory: {self._state.working_directory}")

        if self._state.active_application:
            state_info.append(f"Active application: {self._state.active_application}")

        if state_info:
            prompt_parts.append("\nCurrent context:")
            prompt_parts.extend(state_info)

        return "\n".join(prompt_parts)

    def resolve_references(self, text: str) -> str:
        """
        Resolve pronoun references in text.

        Replaces "it", "that", etc. with actual references from context.
        """
        resolved = text

        for pattern, ref_types in self.PRONOUN_PATTERNS:
            if pattern.search(resolved):
                # Find most recent reference of matching type
                for ref_type in ref_types:
                    if ref_type in self._state.references:
                        ref = self._state.references[ref_type]
                        # Replace pronoun with actual value
                        resolved = pattern.sub(f'"{ref.value}"', resolved, count=1)
                        break

        return resolved

    def get_recent_references(self, ref_type: str | None = None) -> list[ContextReference]:
        """Get recent references, optionally filtered by type."""
        if ref_type:
            if ref_type in self._state.references:
                return [self._state.references[ref_type]]
            return []

        return list(self._state.references.values())

    def set_working_directory(self, path: str) -> None:
        """Set the current working directory."""
        self._state.working_directory = path
        self._state.references["directory"] = ContextReference(
            type="directory",
            value=path,
        )

    def set_active_application(self, app_name: str | None) -> None:
        """Set the currently active application."""
        self._state.active_application = app_name
        if app_name:
            self._state.references["application"] = ContextReference(
                type="application",
                value=app_name,
            )

    def _extract_references(self, text: str) -> None:
        """Extract references from user input."""
        # Extract file paths
        file_patterns = [
            r'["\']([^"\']+\.[a-zA-Z0-9]+)["\']',  # Quoted paths with extension
            r'(/[\w/.-]+\.\w+)',  # Unix absolute paths
            r'(~/[\w/.-]+)',  # Home-relative paths
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                self._state.references["file"] = ContextReference(
                    type="file",
                    value=match,
                )

        # Extract URLs
        url_pattern = r'(https?://[^\s]+)'
        urls = re.findall(url_pattern, text)
        for url in urls:
            self._state.references["url"] = ContextReference(
                type="url",
                value=url,
            )

        # Extract directory references
        dir_patterns = [
            r'(?:in|to|from)\s+["\']?([/~][\w/.-]+)["\']?',
            r'folder\s+["\']?([/~]?[\w/.-]+)["\']?',
        ]

        for pattern in dir_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if not re.search(r'\.\w+$', match):  # No file extension
                    self._state.references["directory"] = ContextReference(
                        type="directory",
                        value=match,
                    )

    def _extract_references_from_result(
        self,
        content: str,
        tool_name: str | None
    ) -> None:
        """Extract references from tool results."""
        if not tool_name:
            return

        # File operations
        if tool_name in ("read_file", "write_file", "file_info"):
            # Extract file path from result
            path_match = re.search(r'["\']?(/[\w/.-]+)["\']?', content)
            if path_match:
                self._state.references["file"] = ContextReference(
                    type="file",
                    value=path_match.group(1),
                    metadata={"from_tool": tool_name},
                )

        # Directory operations
        if tool_name in ("list_directory", "create_directory"):
            path_match = re.search(r'["\']?(/[\w/.-]+)["\']?', content)
            if path_match:
                self._state.references["directory"] = ContextReference(
                    type="directory",
                    value=path_match.group(1),
                    metadata={"from_tool": tool_name},
                )

        # Application operations
        if tool_name in ("launch_app", "close_app"):
            app_match = re.search(r'(?:Launched|Opened|Closed)\s+(\w+)', content)
            if app_match:
                self._state.references["application"] = ContextReference(
                    type="application",
                    value=app_match.group(1),
                    metadata={"from_tool": tool_name},
                )

    def estimate_tokens(self) -> int:
        """Estimate total tokens in current context."""
        total_chars = 0

        if self.system_prompt:
            total_chars += len(self._build_system_prompt())

        for msg in self._messages:
            total_chars += len(msg.content)
            for tc in msg.tool_calls:
                total_chars += len(json.dumps(tc.arguments))

        return total_chars // self.CHARS_PER_TOKEN

    def _trim_if_needed(self) -> None:
        """Trim context if it exceeds token limit."""
        while self.estimate_tokens() > self.max_tokens and len(self._messages) > 2:
            # Remove oldest non-system message
            self._messages.popleft()

    def clear(self) -> None:
        """Clear all messages and state."""
        self._messages.clear()
        self._state = ContextState()
        self._tool_results.clear()

    def _persist_if_enabled(self) -> None:
        """Persist history to disk if enabled."""
        if not self.persist_path:
            return

        try:
            history = {
                "messages": [
                    {
                        "role": msg.role.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "tool_calls": [
                            {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                            for tc in msg.tool_calls
                        ],
                    }
                    for msg in self._messages
                ],
                "state": {
                    "working_directory": self._state.working_directory,
                    "last_command": self._state.last_command,
                },
            }

            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            self.persist_path.write_text(json.dumps(history, indent=2))
        except Exception:
            pass  # Silently fail persistence

    def _load_history(self) -> None:
        """Load history from disk."""
        if not self.persist_path or not self.persist_path.exists():
            return

        try:
            data = json.loads(self.persist_path.read_text())

            for msg_data in data.get("messages", []):
                role = MessageRole(msg_data["role"])
                tool_calls = [
                    ToolCall(id=tc["id"], name=tc["name"], arguments=tc["arguments"])
                    for tc in msg_data.get("tool_calls", [])
                ]

                self._messages.append(Message(
                    role=role,
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data.get("timestamp", datetime.now().isoformat())),
                    tool_calls=tool_calls,
                ))

            state_data = data.get("state", {})
            self._state.working_directory = state_data.get("working_directory", "")
            self._state.last_command = state_data.get("last_command", "")

        except Exception:
            pass  # Silently fail loading

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of current context state."""
        return {
            "message_count": len(self._messages),
            "estimated_tokens": self.estimate_tokens(),
            "max_tokens": self.max_tokens,
            "working_directory": self._state.working_directory,
            "active_application": self._state.active_application,
            "last_command": self._state.last_command,
            "recent_references": {
                k: v.value for k, v in self._state.references.items()
            },
        }
