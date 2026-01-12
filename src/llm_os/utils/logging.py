"""
LLM-OS Logging System

Comprehensive logging system for LLM-OS with different log categories:
- User Logs: User interactions, commands, responses
- System Logs: System health, startup, shutdown, errors
- Tool Logs: MCP tool executions, parameters, results
- LLM Logs: LLM provider calls, token usage, latency
- Security Logs: Permission checks, security events
- Performance Logs: Timing, resource usage, bottlenecks

Features:
- Automatic log rotation to prevent large files
- Structured JSON logging for machine readability
- Human-readable formatted logs
- Separate files for each log category
- Configurable log levels and retention
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Default log directory
DEFAULT_LOG_DIR = Path.home() / ".llm-os" / "logs"

# Log file names for each category
LOG_FILES = {
    "user": "user_interactions.log",
    "system": "system_health.log",
    "tool": "tool_executions.log",
    "llm": "llm_calls.log",
    "security": "security.log",
    "performance": "performance.log",
    "error": "errors.log",
}

# Maximum log file size before rotation (10 MB)
MAX_LOG_SIZE = 10 * 1024 * 1024

# Number of backup files to keep
BACKUP_COUNT = 5


class LogCategory(Enum):
    """Log categories."""
    USER = "user"
    SYSTEM = "system"
    TOOL = "tool"
    LLM = "llm"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR = "error"


@dataclass
class LogEntry:
    """Base class for structured log entries."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    category: str = ""
    level: str = "INFO"
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class UserLogEntry(LogEntry):
    """User interaction log entry."""
    user_input: str = ""
    response_summary: str = ""  # Truncated response, not full text
    tool_calls: list[str] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    duration_ms: float = 0.0

    def __post_init__(self):
        self.category = "user"


@dataclass
class SystemLogEntry(LogEntry):
    """System health log entry."""
    event_type: str = ""  # startup, shutdown, error, warning
    component: str = ""  # Which component (router, orchestrator, etc.)
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.category = "system"


@dataclass
class ToolLogEntry(LogEntry):
    """Tool execution log entry."""
    tool_name: str = ""
    tool_server: str = ""  # Which MCP server
    parameters: dict[str, Any] = field(default_factory=dict)
    result_summary: str = ""  # Summary, not full result
    success: bool = True
    error: Optional[str] = None
    duration_ms: float = 0.0

    def __post_init__(self):
        self.category = "tool"


@dataclass
class LLMLogEntry(LogEntry):
    """LLM call log entry."""
    provider: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    streaming: bool = False

    def __post_init__(self):
        self.category = "llm"


@dataclass
class SecurityLogEntry(LogEntry):
    """Security event log entry."""
    event_type: str = ""  # permission_denied, unauthorized_access, etc.
    resource: str = ""  # What was being accessed
    action: str = ""  # What action was attempted
    allowed: bool = False
    reason: str = ""

    def __post_init__(self):
        self.category = "security"


@dataclass
class PerformanceLogEntry(LogEntry):
    """Performance metric log entry."""
    operation: str = ""
    duration_ms: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.category = "performance"


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "log_entry"):
            log_data.update(record.log_entry.to_dict())
        elif hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter with colors and formatting."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
        "RESET": "\033[0m",       # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record in human-readable format."""
        # Add color if terminal supports it
        color = self.COLORS.get(record.levelname, "")
        reset = self.COLORS["RESET"] if color else ""

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Format message
        message = record.getMessage()

        # Add extra context if present
        if hasattr(record, "log_entry"):
            entry = record.log_entry
            if isinstance(entry, UserLogEntry):
                message += f"\n  Input: {self._truncate(entry.user_input, 100)}"
                if entry.response_summary:
                    message += f"\n  Response: {self._truncate(entry.response_summary, 100)}"
                if entry.tool_calls:
                    message += f"\n  Tools: {', '.join(entry.tool_calls)}"
                message += f"\n  Duration: {entry.duration_ms:.2f}ms"

            elif isinstance(entry, ToolLogEntry):
                message += f"\n  Tool: {entry.tool_name} ({entry.tool_server})"
                if entry.parameters:
                    message += f"\n  Params: {self._truncate(str(entry.parameters), 150)}"
                message += f"\n  Duration: {entry.duration_ms:.2f}ms"

            elif isinstance(entry, LLMLogEntry):
                message += f"\n  Provider: {entry.provider}, Model: {entry.model}"
                message += f"\n  Tokens: {entry.total_tokens} ({entry.prompt_tokens}+{entry.completion_tokens})"
                message += f"\n  Duration: {entry.duration_ms:.2f}ms"

        return f"{color}[{timestamp}] {record.levelname:8s} {record.name:20s}{reset} {message}"

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text to max length."""
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."


class CategoryLogger:
    """Base class for category-specific loggers."""

    def __init__(self, category: LogCategory, log_dir: Path = DEFAULT_LOG_DIR):
        """
        Initialize category logger.

        Args:
            category: Log category
            log_dir: Directory for log files
        """
        self.category = category
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up logger
        self.logger = logging.getLogger(f"llm_os.{category.value}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # Don't propagate to root logger

        # Remove existing handlers
        self.logger.handlers.clear()

        # Add rotating file handler with JSON format
        log_file = self.log_dir / LOG_FILES[category.value]
        json_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
        )
        json_handler.setFormatter(JSONFormatter())
        json_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(json_handler)

        # Add console handler with human-readable format (only for errors)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(HumanReadableFormatter())
        console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
        self.logger.addHandler(console_handler)

    def _log(self, level: str, entry: LogEntry) -> None:
        """Log an entry."""
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, entry.message, extra={"log_entry": entry})


class UserLogger(CategoryLogger):
    """Logger for user interactions."""

    def __init__(self, log_dir: Path = DEFAULT_LOG_DIR):
        super().__init__(LogCategory.USER, log_dir)

    def log_interaction(
        self,
        user_input: str,
        response: str,
        tool_calls: list[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> None:
        """
        Log a user interaction.

        Args:
            user_input: User's input command
            response: Assistant's response (will be truncated)
            tool_calls: List of tools called
            success: Whether the interaction succeeded
            error: Error message if failed
            duration_ms: Duration in milliseconds
        """
        # Truncate response for storage
        response_summary = response[:500] + "..." if len(response) > 500 else response

        entry = UserLogEntry(
            message=f"User interaction: {user_input[:100]}",
            user_input=user_input,
            response_summary=response_summary,
            tool_calls=tool_calls or [],
            success=success,
            error=error,
            duration_ms=duration_ms,
        )

        level = "INFO" if success else "ERROR"
        self._log(level, entry)


class SystemLogger(CategoryLogger):
    """Logger for system health and events."""

    def __init__(self, log_dir: Path = DEFAULT_LOG_DIR):
        super().__init__(LogCategory.SYSTEM, log_dir)

    def log_startup(self, component: str, details: dict[str, Any] = None) -> None:
        """Log system startup."""
        entry = SystemLogEntry(
            message=f"Starting {component}",
            event_type="startup",
            component=component,
            details=details or {},
        )
        self._log("INFO", entry)

    def log_shutdown(self, component: str, details: dict[str, Any] = None) -> None:
        """Log system shutdown."""
        entry = SystemLogEntry(
            message=f"Shutting down {component}",
            event_type="shutdown",
            component=component,
            details=details or {},
        )
        self._log("INFO", entry)

    def log_error(self, component: str, error: str, details: dict[str, Any] = None) -> None:
        """Log system error."""
        entry = SystemLogEntry(
            message=f"Error in {component}: {error}",
            level="ERROR",
            event_type="error",
            component=component,
            details=details or {},
        )
        self._log("ERROR", entry)

    def log_warning(self, component: str, warning: str, details: dict[str, Any] = None) -> None:
        """Log system warning."""
        entry = SystemLogEntry(
            message=f"Warning in {component}: {warning}",
            level="WARNING",
            event_type="warning",
            component=component,
            details=details or {},
        )
        self._log("WARNING", entry)


class ToolLogger(CategoryLogger):
    """Logger for tool executions."""

    def __init__(self, log_dir: Path = DEFAULT_LOG_DIR):
        super().__init__(LogCategory.TOOL, log_dir)

    def log_execution(
        self,
        tool_name: str,
        tool_server: str,
        parameters: dict[str, Any],
        result: Any,
        success: bool = True,
        error: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> None:
        """
        Log tool execution.

        Args:
            tool_name: Name of the tool
            tool_server: MCP server name
            parameters: Tool parameters (will be truncated if large)
            result: Tool result (will be summarized)
            success: Whether execution succeeded
            error: Error message if failed
            duration_ms: Duration in milliseconds
        """
        # Truncate large parameters
        params_str = str(parameters)
        if len(params_str) > 500:
            params_truncated = {
                **parameters,
                "_truncated": f"(truncated, original length: {len(params_str)})"
            }
        else:
            params_truncated = parameters

        # Summarize result
        result_str = str(result)
        result_summary = result_str[:500] + "..." if len(result_str) > 500 else result_str

        entry = ToolLogEntry(
            message=f"Tool execution: {tool_name}",
            tool_name=tool_name,
            tool_server=tool_server,
            parameters=params_truncated,
            result_summary=result_summary,
            success=success,
            error=error,
            duration_ms=duration_ms,
        )

        level = "INFO" if success else "ERROR"
        self._log(level, entry)


class LLMLogger(CategoryLogger):
    """Logger for LLM calls."""

    def __init__(self, log_dir: Path = DEFAULT_LOG_DIR):
        super().__init__(LogCategory.LLM, log_dir)

    def log_call(
        self,
        provider: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        duration_ms: float = 0.0,
        success: bool = True,
        error: Optional[str] = None,
        streaming: bool = False,
    ) -> None:
        """
        Log LLM API call.

        Args:
            provider: LLM provider name
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            duration_ms: Duration in milliseconds
            success: Whether call succeeded
            error: Error message if failed
            streaming: Whether response was streamed
        """
        total_tokens = prompt_tokens + completion_tokens

        entry = LLMLogEntry(
            message=f"LLM call: {provider}/{model}",
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
            success=success,
            error=error,
            streaming=streaming,
        )

        level = "INFO" if success else "ERROR"
        self._log(level, entry)


class SecurityLogger(CategoryLogger):
    """Logger for security events."""

    def __init__(self, log_dir: Path = DEFAULT_LOG_DIR):
        super().__init__(LogCategory.SECURITY, log_dir)

    def log_event(
        self,
        event_type: str,
        resource: str,
        action: str,
        allowed: bool,
        reason: str = "",
    ) -> None:
        """
        Log security event.

        Args:
            event_type: Type of event (permission_check, access_denied, etc.)
            resource: Resource being accessed
            action: Action being performed
            allowed: Whether action was allowed
            reason: Reason for decision
        """
        entry = SecurityLogEntry(
            message=f"Security: {event_type} - {action} on {resource}",
            event_type=event_type,
            resource=resource,
            action=action,
            allowed=allowed,
            reason=reason,
        )

        level = "WARNING" if not allowed else "INFO"
        self._log(level, entry)


class PerformanceLogger(CategoryLogger):
    """Logger for performance metrics."""

    def __init__(self, log_dir: Path = DEFAULT_LOG_DIR):
        super().__init__(LogCategory.PERFORMANCE, log_dir)

    def log_metric(
        self,
        operation: str,
        duration_ms: float,
        memory_mb: float = 0.0,
        cpu_percent: float = 0.0,
        details: dict[str, Any] = None,
    ) -> None:
        """
        Log performance metric.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            memory_mb: Memory usage in MB
            cpu_percent: CPU usage percentage
            details: Additional details
        """
        entry = PerformanceLogEntry(
            message=f"Performance: {operation}",
            operation=operation,
            duration_ms=duration_ms,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            details=details or {},
        )

        # Warn if operation is slow
        level = "WARNING" if duration_ms > 5000 else "INFO"
        self._log(level, entry)


class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self, logger: PerformanceLogger, operation: str):
        """
        Initialize timer.

        Args:
            logger: Performance logger
            operation: Operation name
        """
        self.logger = logger
        self.operation = operation
        self.start_time = 0.0

    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and log."""
        duration_ms = (time.time() - self.start_time) * 1000
        self.logger.log_metric(self.operation, duration_ms)


# Global logger instances
_loggers: dict[str, CategoryLogger] = {}


def setup_logging(log_dir: Path = DEFAULT_LOG_DIR) -> None:
    """
    Set up logging system.

    Args:
        log_dir: Directory for log files
    """
    global _loggers

    # Create log directory
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Initialize all category loggers
    _loggers = {
        "user": UserLogger(log_dir),
        "system": SystemLogger(log_dir),
        "tool": ToolLogger(log_dir),
        "llm": LLMLogger(log_dir),
        "security": SecurityLogger(log_dir),
        "performance": PerformanceLogger(log_dir),
    }

    # Log setup completion
    _loggers["system"].log_startup(
        "logging_system",
        {"log_dir": str(log_dir), "categories": list(_loggers.keys())}
    )


def get_logger(category: str) -> CategoryLogger:
    """
    Get logger for category.

    Args:
        category: Log category name

    Returns:
        Category logger instance
    """
    if category not in _loggers:
        raise ValueError(f"Unknown log category: {category}")
    return _loggers[category]


__all__ = [
    "LogCategory",
    "setup_logging",
    "get_logger",
    "UserLogger",
    "SystemLogger",
    "ToolLogger",
    "LLMLogger",
    "SecurityLogger",
    "PerformanceLogger",
    "PerformanceTimer",
]
