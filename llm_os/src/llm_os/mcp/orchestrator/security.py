"""
MCP Security Manager

Handles permission checking, confirmation prompts, and security policies
for tool execution.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine

from llm_os.mcp.types.server import PermissionLevel
from llm_os.mcp.types.tools import Tool, ToolResult


logger = logging.getLogger(__name__)


class SecurityAction(str, Enum):
    """Actions that can be taken on a security check."""
    ALLOW = "allow"
    DENY = "deny"
    CONFIRM = "confirm"
    SANDBOX = "sandbox"


@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    # Permission settings
    require_confirmation_for_write: bool = True
    require_confirmation_for_execute: bool = True
    require_confirmation_for_system: bool = True
    require_confirmation_for_dangerous: bool = True

    # Sandboxing
    sandbox_enabled: bool = True
    sandbox_allowed_paths: list[str] = field(default_factory=list)
    sandbox_blocked_paths: list[str] = field(default_factory=lambda: [
        "/etc/passwd",
        "/etc/shadow",
        "/etc/sudoers",
        "/root",
        "/boot",
        "/sys",
        "/proc/kcore",
    ])

    # Command restrictions
    blocked_commands: list[str] = field(default_factory=lambda: [
        "rm -rf /",
        "dd if=/dev/zero",
        "mkfs",
        ":(){:|:&};:",  # Fork bomb
        "chmod -R 777 /",
        "wget * | sh",
        "curl * | sh",
    ])

    # File restrictions
    blocked_extensions: list[str] = field(default_factory=lambda: [
        ".exe",
        ".dll",
        ".bat",
        ".cmd",
        ".vbs",
        ".ps1",
    ])

    # Network restrictions
    allow_network_access: bool = True
    blocked_domains: list[str] = field(default_factory=list)

    # Rate limiting
    max_operations_per_minute: int = 60
    max_file_operations_per_minute: int = 30


@dataclass
class SecurityContext:
    """Context for security decisions."""
    user_id: str = "default"
    session_id: str = ""
    trust_level: int = 0  # 0=untrusted, 1=basic, 2=trusted, 3=admin
    confirmed_operations: set[str] = field(default_factory=set)
    denied_operations: set[str] = field(default_factory=set)
    operation_count: int = 0
    file_operation_count: int = 0


@dataclass
class SecurityCheckResult:
    """Result of a security check."""
    action: SecurityAction
    reason: str | None = None
    requires_confirmation: bool = False
    confirmation_message: str | None = None
    modified_arguments: dict[str, Any] | None = None


# Type alias for confirmation handlers
ConfirmationHandler = Callable[[str, str], Coroutine[Any, Any, bool]]


class SecurityManager:
    """
    Manages security for MCP tool execution.

    Features:
    - Permission level checking
    - Path sandboxing
    - Command filtering
    - Confirmation prompts
    - Rate limiting
    - Audit logging
    """

    def __init__(
        self,
        policy: SecurityPolicy | None = None,
        confirmation_handler: ConfirmationHandler | None = None,
    ):
        """
        Initialize security manager.

        Args:
            policy: Security policy to enforce
            confirmation_handler: Async function to prompt for confirmation
        """
        self.policy = policy or SecurityPolicy()
        self._confirmation_handler = confirmation_handler
        self._context = SecurityContext()
        self._audit_log: list[dict[str, Any]] = []

    def set_confirmation_handler(self, handler: ConfirmationHandler) -> None:
        """Set the confirmation handler."""
        self._confirmation_handler = handler

    def set_context(self, context: SecurityContext) -> None:
        """Set security context."""
        self._context = context

    def check_tool_permission(
        self,
        tool: Tool,
        arguments: dict[str, Any],
    ) -> SecurityCheckResult:
        """
        Check if a tool execution is permitted.

        Args:
            tool: Tool to check
            arguments: Tool arguments

        Returns:
            SecurityCheckResult with action and details
        """
        # Check if operation was already denied
        operation_key = f"{tool.name}:{hash(frozenset(arguments.items()))}"
        if operation_key in self._context.denied_operations:
            return SecurityCheckResult(
                action=SecurityAction.DENY,
                reason="Operation previously denied in this session",
            )

        # Check permission level
        permission_check = self._check_permission_level(tool)
        if permission_check.action == SecurityAction.DENY:
            return permission_check

        # Check arguments for security issues
        argument_check = self._check_arguments(tool, arguments)
        if argument_check.action == SecurityAction.DENY:
            return argument_check

        # Check if confirmation required
        if tool.requires_confirmation or permission_check.requires_confirmation:
            # Check if already confirmed
            if operation_key in self._context.confirmed_operations:
                return SecurityCheckResult(action=SecurityAction.ALLOW)

            return SecurityCheckResult(
                action=SecurityAction.CONFIRM,
                requires_confirmation=True,
                confirmation_message=self._build_confirmation_message(tool, arguments),
            )

        return SecurityCheckResult(action=SecurityAction.ALLOW)

    async def execute_with_security(
        self,
        tool: Tool,
        arguments: dict[str, Any],
        executor: Callable[..., Coroutine[Any, Any, ToolResult]],
    ) -> ToolResult:
        """
        Execute a tool with security checks.

        Args:
            tool: Tool to execute
            arguments: Tool arguments
            executor: Function to execute the tool

        Returns:
            ToolResult from execution or error
        """
        # Perform security check
        check_result = self.check_tool_permission(tool, arguments)

        operation_key = f"{tool.name}:{hash(frozenset(arguments.items()))}"

        if check_result.action == SecurityAction.DENY:
            self._audit_log_operation(tool, arguments, "denied", check_result.reason)
            return ToolResult.error_result(
                f"Permission denied: {check_result.reason}"
            )

        if check_result.action == SecurityAction.CONFIRM:
            if not self._confirmation_handler:
                return ToolResult.error_result(
                    "Confirmation required but no handler available"
                )

            # Request confirmation
            confirmed = await self._confirmation_handler(
                tool.name,
                check_result.confirmation_message or "Confirm execution?",
            )

            if not confirmed:
                self._context.denied_operations.add(operation_key)
                self._audit_log_operation(tool, arguments, "user_denied")
                return ToolResult.error_result("Operation cancelled by user")

            # Mark as confirmed
            self._context.confirmed_operations.add(operation_key)

        # Apply any argument modifications
        if check_result.modified_arguments:
            arguments = {**arguments, **check_result.modified_arguments}

        # Execute the tool
        try:
            self._audit_log_operation(tool, arguments, "executing")
            result = await executor(**arguments)
            self._audit_log_operation(
                tool, arguments,
                "success" if result.success else "failed",
                result.error_message,
            )
            return result
        except Exception as e:
            self._audit_log_operation(tool, arguments, "error", str(e))
            raise

    def _check_permission_level(self, tool: Tool) -> SecurityCheckResult:
        """Check permission level requirements."""
        level = tool.permission_level

        if level == "dangerous":
            if self._context.trust_level < 3:
                return SecurityCheckResult(
                    action=SecurityAction.DENY,
                    reason="Dangerous operations require admin trust level",
                )
            if self.policy.require_confirmation_for_dangerous:
                return SecurityCheckResult(
                    action=SecurityAction.CONFIRM,
                    requires_confirmation=True,
                )

        elif level == "system":
            if self._context.trust_level < 2:
                return SecurityCheckResult(
                    action=SecurityAction.DENY,
                    reason="System operations require trusted level",
                )
            if self.policy.require_confirmation_for_system:
                return SecurityCheckResult(
                    action=SecurityAction.CONFIRM,
                    requires_confirmation=True,
                )

        elif level == "execute":
            if self.policy.require_confirmation_for_execute:
                return SecurityCheckResult(
                    action=SecurityAction.CONFIRM,
                    requires_confirmation=True,
                )

        elif level == "write":
            if self.policy.require_confirmation_for_write:
                return SecurityCheckResult(
                    action=SecurityAction.CONFIRM,
                    requires_confirmation=True,
                )

        return SecurityCheckResult(action=SecurityAction.ALLOW)

    def _check_arguments(
        self,
        tool: Tool,
        arguments: dict[str, Any],
    ) -> SecurityCheckResult:
        """Check arguments for security issues."""
        # Check for path-based arguments
        for key, value in arguments.items():
            if isinstance(value, str):
                # Check blocked paths
                if self._is_blocked_path(value):
                    return SecurityCheckResult(
                        action=SecurityAction.DENY,
                        reason=f"Access to path '{value}' is not allowed",
                    )

                # Check blocked commands
                if key in ("command", "cmd", "script"):
                    if self._is_blocked_command(value):
                        return SecurityCheckResult(
                            action=SecurityAction.DENY,
                            reason="Command matches blocked pattern",
                        )

                # Check blocked file extensions
                if key in ("path", "file", "filename"):
                    if self._has_blocked_extension(value):
                        return SecurityCheckResult(
                            action=SecurityAction.DENY,
                            reason=f"File extension not allowed",
                        )

                # Check for command injection attempts
                if self._contains_injection(value):
                    return SecurityCheckResult(
                        action=SecurityAction.DENY,
                        reason="Potential command injection detected",
                    )

        return SecurityCheckResult(action=SecurityAction.ALLOW)

    def _is_blocked_path(self, path: str) -> bool:
        """Check if a path is blocked."""
        try:
            resolved = Path(path).resolve()
            path_str = str(resolved)

            for blocked in self.policy.sandbox_blocked_paths:
                if path_str.startswith(blocked) or path_str == blocked:
                    return True

            # If sandbox is enabled and allowed paths are specified
            if self.policy.sandbox_enabled and self.policy.sandbox_allowed_paths:
                allowed = False
                for allowed_path in self.policy.sandbox_allowed_paths:
                    if path_str.startswith(allowed_path):
                        allowed = True
                        break
                return not allowed

        except Exception:
            return True  # Block on error

        return False

    def _is_blocked_command(self, command: str) -> bool:
        """Check if a command matches blocked patterns."""
        command_lower = command.lower().strip()

        for blocked in self.policy.blocked_commands:
            if blocked.lower() in command_lower:
                return True

        # Check for dangerous patterns
        dangerous_patterns = [
            r"rm\s+-[rf]+\s+/",
            r"dd\s+if=/dev/(zero|random)",
            r"mkfs\.",
            r"chmod\s+-R\s+777\s+/",
            r">\s*/dev/sd[a-z]",
            r"\|\s*(ba)?sh",
            r"eval\s+",
            r"`.*`",
            r"\$\(",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, command_lower):
                return True

        return False

    def _has_blocked_extension(self, path: str) -> bool:
        """Check if path has a blocked extension."""
        path_lower = path.lower()
        for ext in self.policy.blocked_extensions:
            if path_lower.endswith(ext):
                return True
        return False

    def _contains_injection(self, value: str) -> bool:
        """Check for command injection patterns."""
        injection_patterns = [
            r";\s*\w+",  # Command chaining with semicolon
            r"\|\s*\w+",  # Pipe to another command
            r"&&\s*\w+",  # AND chaining
            r"\|\|\s*\w+",  # OR chaining
            r"\$\([^)]+\)",  # Command substitution
            r"`[^`]+`",  # Backtick command substitution
            r">\s*[/~]",  # Redirect to file
            r"<\s*[/~]",  # Read from file
        ]

        # Only flag if it looks like it might be injection
        # (not just normal shell usage)
        suspicious_count = 0
        for pattern in injection_patterns:
            if re.search(pattern, value):
                suspicious_count += 1

        # Require multiple suspicious patterns
        return suspicious_count >= 2

    def _build_confirmation_message(
        self,
        tool: Tool,
        arguments: dict[str, Any],
    ) -> str:
        """Build a confirmation message for the user."""
        lines = [
            f"Tool: {tool.name}",
            f"Permission Level: {tool.permission_level}",
            "Arguments:",
        ]

        for key, value in arguments.items():
            # Truncate long values
            str_value = str(value)
            if len(str_value) > 100:
                str_value = str_value[:97] + "..."
            lines.append(f"  {key}: {str_value}")

        lines.append("\nDo you want to proceed?")

        return "\n".join(lines)

    def _audit_log_operation(
        self,
        tool: Tool,
        arguments: dict[str, Any],
        status: str,
        details: str | None = None,
    ) -> None:
        """Log operation for auditing."""
        from datetime import datetime

        entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool.name,
            "server": tool.server_id,
            "permission_level": tool.permission_level,
            "arguments": arguments,
            "status": status,
            "details": details,
            "user_id": self._context.user_id,
            "session_id": self._context.session_id,
        }

        self._audit_log.append(entry)

        # Keep only recent entries
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-500:]

        # Log to standard logger as well
        if status in ("denied", "error", "user_denied"):
            logger.warning(f"Security: {status} - {tool.name}: {details}")
        else:
            logger.debug(f"Security: {status} - {tool.name}")

    def get_audit_log(
        self,
        limit: int = 100,
        status_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get audit log entries."""
        entries = self._audit_log[-limit:]

        if status_filter:
            entries = [e for e in entries if e["status"] == status_filter]

        return entries

    def clear_confirmations(self) -> None:
        """Clear confirmed operations (for new session)."""
        self._context.confirmed_operations.clear()
        self._context.denied_operations.clear()

    def reset_context(self) -> None:
        """Reset security context completely."""
        self._context = SecurityContext()


class PathSandbox:
    """
    Sandboxes file operations to specific directories.
    """

    def __init__(
        self,
        allowed_paths: list[str] | None = None,
        home_dir: str | None = None,
    ):
        """
        Initialize sandbox.

        Args:
            allowed_paths: List of allowed path prefixes
            home_dir: User's home directory
        """
        self.allowed_paths = allowed_paths or []
        self.home_dir = home_dir or str(Path.home())

        # Always allow home directory by default
        if self.home_dir not in self.allowed_paths:
            self.allowed_paths.append(self.home_dir)

    def validate_path(self, path: str) -> tuple[bool, str]:
        """
        Validate a path against the sandbox.

        Returns (is_valid, resolved_path or error_message).
        """
        try:
            # Resolve the path
            resolved = Path(path).expanduser().resolve()
            resolved_str = str(resolved)

            # Check against allowed paths
            for allowed in self.allowed_paths:
                allowed_resolved = str(Path(allowed).expanduser().resolve())
                if resolved_str.startswith(allowed_resolved):
                    return True, resolved_str

            return False, f"Path outside sandbox: {resolved_str}"

        except Exception as e:
            return False, f"Invalid path: {e}"

    def sandbox_path(self, path: str, base_dir: str | None = None) -> str:
        """
        Convert a path to be within the sandbox.

        If path is relative, makes it relative to base_dir or home.
        If path is absolute but outside sandbox, raises error.
        """
        base = Path(base_dir) if base_dir else Path(self.home_dir)

        try:
            p = Path(path)

            if not p.is_absolute():
                # Make relative to base
                resolved = (base / p).resolve()
            else:
                resolved = p.expanduser().resolve()

            # Validate
            is_valid, result = self.validate_path(str(resolved))
            if not is_valid:
                raise PermissionError(result)

            return str(resolved)

        except Exception as e:
            raise PermissionError(f"Cannot sandbox path '{path}': {e}")
