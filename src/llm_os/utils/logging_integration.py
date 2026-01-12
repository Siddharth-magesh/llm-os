"""
Logging Integration Examples for LLM-OS

This file provides examples and helper functions for integrating logging
throughout the LLM-OS codebase.

Usage Examples:
    # In core.py - Log user interactions
    from llm_os.utils.logging import get_logger
    import time

    user_logger = get_logger("user")
    start_time = time.time()

    # ... process user message ...

    duration_ms = (time.time() - start_time) * 1000
    user_logger.log_interaction(
        user_input=user_input,
        response=response_text,
        tool_calls=tool_names,
        success=True,
        duration_ms=duration_ms,
    )

    # In LLM router - Log LLM calls
    llm_logger = get_logger("llm")

    llm_logger.log_call(
        provider="groq",
        model="llama3-70b",
        prompt_tokens=150,
        completion_tokens=80,
        duration_ms=1234.5,
        success=True,
        streaming=False,
    )

    # In MCP orchestrator - Log tool executions
    tool_logger = get_logger("tool")

    tool_logger.log_execution(
        tool_name="list_directory",
        tool_server="filesystem",
        parameters={"path": "/home/user"},
        result={"files": ["file1.txt", "file2.txt"]},
        success=True,
        duration_ms=45.2,
    )

    # In system components - Log startup/shutdown
    system_logger = get_logger("system")

    system_logger.log_startup("llm_router", {"default_provider": "groq"})
    system_logger.log_shutdown("llm_router")
    system_logger.log_error("mcp_orchestrator", "Failed to start server", {"server": "git"})

    # In security checks - Log security events
    security_logger = get_logger("security")

    security_logger.log_event(
        event_type="permission_check",
        resource="/etc/passwd",
        action="read",
        allowed=False,
        reason="Outside allowed directories",
    )

    # Performance monitoring
    performance_logger = get_logger("performance")

    with PerformanceTimer(performance_logger, "process_message"):
        # ... operation to time ...
        pass
"""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, Optional

from llm_os.utils.logging import get_logger


def log_user_interaction(func: Callable) -> Callable:
    """
    Decorator to automatically log user interactions.

    Usage:
        @log_user_interaction
        async def process_message(self, user_input: str) -> str:
            ...
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        user_logger = get_logger("user")
        start_time = time.time()

        # Extract user_input from args or kwargs
        user_input = kwargs.get("user_input") or (args[1] if len(args) > 1 else "")

        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            user_logger.log_interaction(
                user_input=user_input,
                response=result,
                success=True,
                duration_ms=duration_ms,
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            user_logger.log_interaction(
                user_input=user_input,
                response="",
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )

            raise

    return wrapper


def log_llm_call(func: Callable) -> Callable:
    """
    Decorator to automatically log LLM calls.

    Usage:
        @log_llm_call
        async def complete(self, messages: list, **kwargs):
            ...
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        llm_logger = get_logger("llm")
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            # Extract token usage from result if available
            prompt_tokens = getattr(result, "prompt_tokens", 0)
            completion_tokens = getattr(result, "completion_tokens", 0)
            provider = getattr(result, "provider", "unknown")
            model = getattr(result, "model", "unknown")

            llm_logger.log_call(
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                duration_ms=duration_ms,
                success=True,
                streaming=kwargs.get("stream", False),
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            llm_logger.log_call(
                provider="unknown",
                model="unknown",
                duration_ms=duration_ms,
                success=False,
                error=str(e),
            )

            raise

    return wrapper


def log_tool_execution(func: Callable) -> Callable:
    """
    Decorator to automatically log tool executions.

    Usage:
        @log_tool_execution
        async def execute_tool(self, tool_name: str, parameters: dict):
            ...
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        tool_logger = get_logger("tool")
        start_time = time.time()

        # Extract tool info from args or kwargs
        tool_name = kwargs.get("tool_name") or (args[1] if len(args) > 1 else "unknown")
        parameters = kwargs.get("parameters") or (args[2] if len(args) > 2 else {})

        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            tool_logger.log_execution(
                tool_name=tool_name,
                tool_server=kwargs.get("server", "unknown"),
                parameters=parameters,
                result=result,
                success=True,
                duration_ms=duration_ms,
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            tool_logger.log_execution(
                tool_name=tool_name,
                tool_server=kwargs.get("server", "unknown"),
                parameters=parameters,
                result=None,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )

            raise

    return wrapper


def log_performance(operation: str) -> Callable:
    """
    Decorator to log performance metrics.

    Usage:
        @log_performance("initialize_router")
        async def initialize(self):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            performance_logger = get_logger("performance")
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                performance_logger.log_metric(
                    operation=operation,
                    duration_ms=duration_ms,
                )

                return result

            except Exception as e:
                # Log even if failed
                duration_ms = (time.time() - start_time) * 1000
                performance_logger.log_metric(
                    operation=operation,
                    duration_ms=duration_ms,
                    details={"error": str(e)},
                )
                raise

        return wrapper
    return decorator


class LoggingHelper:
    """Helper class for easy logging integration."""

    def __init__(self):
        """Initialize logging helper."""
        self.user_logger = get_logger("user")
        self.system_logger = get_logger("system")
        self.tool_logger = get_logger("tool")
        self.llm_logger = get_logger("llm")
        self.security_logger = get_logger("security")
        self.performance_logger = get_logger("performance")

    def log_user_message(
        self,
        user_input: str,
        response: str,
        tool_calls: list[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> None:
        """Log user interaction."""
        self.user_logger.log_interaction(
            user_input=user_input,
            response=response,
            tool_calls=tool_calls,
            success=success,
            error=error,
            duration_ms=duration_ms,
        )

    def log_llm_request(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Log LLM API call."""
        self.llm_logger.log_call(
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration_ms=duration_ms,
            success=success,
            error=error,
        )

    def log_tool_call(
        self,
        tool_name: str,
        server: str,
        parameters: dict[str, Any],
        result: Any,
        success: bool = True,
        error: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> None:
        """Log tool execution."""
        self.tool_logger.log_execution(
            tool_name=tool_name,
            tool_server=server,
            parameters=parameters,
            result=result,
            success=success,
            error=error,
            duration_ms=duration_ms,
        )

    def log_startup(self, component: str, details: dict[str, Any] = None) -> None:
        """Log component startup."""
        self.system_logger.log_startup(component, details)

    def log_shutdown(self, component: str, details: dict[str, Any] = None) -> None:
        """Log component shutdown."""
        self.system_logger.log_shutdown(component, details)

    def log_error(self, component: str, error: str, details: dict[str, Any] = None) -> None:
        """Log system error."""
        self.system_logger.log_error(component, error, details)

    def log_warning(self, component: str, warning: str, details: dict[str, Any] = None) -> None:
        """Log system warning."""
        self.system_logger.log_warning(component, warning, details)

    def log_security_event(
        self,
        event_type: str,
        resource: str,
        action: str,
        allowed: bool,
        reason: str = "",
    ) -> None:
        """Log security event."""
        self.security_logger.log_event(
            event_type=event_type,
            resource=resource,
            action=action,
            allowed=allowed,
            reason=reason,
        )


# Global logging helper instance
_logging_helper: Optional[LoggingHelper] = None


def get_logging_helper() -> LoggingHelper:
    """Get global logging helper instance."""
    global _logging_helper
    if _logging_helper is None:
        _logging_helper = LoggingHelper()
    return _logging_helper


__all__ = [
    "log_user_interaction",
    "log_llm_call",
    "log_tool_execution",
    "log_performance",
    "LoggingHelper",
    "get_logging_helper",
]
