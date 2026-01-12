"""
LLM-OS Core

The main orchestration layer that integrates LLM, MCP, and UI components.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator

from config import Config, get_config
from llm_os.llm.base import Message, ToolCall
from llm_os.llm.router import LLMRouter, RouterConfig
from llm_os.llm.context import ContextManager
from llm_os.llm.classifier import TaskType
from llm_os.mcp import (
    MCPOrchestrator,
    Tool,
    ToolResult,
)
from llm_os.mcp.orchestrator import OrchestratorConfig, ExternalServerSettings
from llm_os.mcp.orchestrator.security import SecurityPolicy
from llm_os.mcp.client import ExternalServerConfig as ExtServerConfig


logger = logging.getLogger(__name__)


# System prompt for the LLM
DEFAULT_SYSTEM_PROMPT = """You are LLM-OS, an intelligent assistant that helps users interact with their computer using natural language.

**CRITICAL INSTRUCTIONS:**
1. You have access to MCP tools for file operations
2. ALWAYS use the available tools - NEVER guess or make up information
3. When asked about files or directories, ALWAYS use list_directory or read_file tools
4. NEVER hallucinate file contents, paths, or system information
5. If you don't have a tool for something, say so clearly

**Available Tools:**

You have MCP Filesystem tools:
- list_directory: List files and directories (use this for "list files", "show files", etc.)
- read_file / read_text_file: Read file contents
- write_file: Create or overwrite files
- edit_file: Make line-based edits
- create_directory: Create directories
- directory_tree: Get recursive directory structure
- search_files: Search for files by name pattern
- get_file_info: Get detailed file information
- move_file: Move or rename files

**How to respond to common requests:**
- "list files" → Use list_directory tool on current directory
- "what's in this folder" → Use list_directory tool
- "read file.txt" → Use read_text_file tool
- "show directory structure" → Use directory_tree tool
- "find all .py files" → Use search_files tool

**IMPORTANT:**
- Current working directory: {cwd}
- Current OS: {os_name}
- ALWAYS call the appropriate tool instead of guessing
- Report exactly what the tool returns
- If a tool fails, report the error clearly

When users ask questions:
1. Identify which tool to use
2. Call the tool with correct parameters
3. Return the tool's result to the user
4. Do NOT make up or assume information
"""


@dataclass
class LLMOSConfig:
    """Configuration for LLM-OS."""
    # LLM settings
    default_provider: str = "ollama"
    default_model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096

    # Context settings
    max_context_tokens: int = 8000
    max_messages: int = 100
    persist_history: bool = True
    history_path: Path | None = None

    # MCP settings
    auto_start_servers: bool = True
    security_policy: SecurityPolicy = field(default_factory=SecurityPolicy)

    # External MCP server settings
    # Set to False for Windows testing (requires Node.js/npx)
    # Set to True for Linux production (with MCP servers installed)
    use_external_servers: bool = False  # Enable external MCP servers (Node.js)
    external_servers_enabled: list[str] = field(default_factory=lambda: [
        "filesystem", "git", "fetch", "memory"
    ])

    # UI settings
    show_tool_calls: bool = True
    stream_responses: bool = True


class LLMOS:
    """
    Main LLM-OS orchestration class.

    Integrates:
    - LLM providers (Ollama, Groq)
    - MCP servers (filesystem, applications, process, system, git)
    - Context management
    - Tool execution
    """

    def __init__(
        self,
        config: LLMOSConfig | None = None,
        system_config: Config | None = None,
    ):
        """
        Initialize LLM-OS.

        Args:
            config: LLM-OS specific configuration
            system_config: Full system configuration
        """
        self.config = config or LLMOSConfig()
        self.system_config = system_config or get_config()

        # Initialize components
        self._llm_router: LLMRouter | None = None
        self._mcp_orchestrator: MCPOrchestrator | None = None
        self._context_manager: ContextManager | None = None

        # State
        self._initialized = False
        self._current_provider = self.config.default_provider
        self._current_model = self.config.default_model

        # Callbacks
        self._tool_callback: callable | None = None
        self._confirmation_callback: callable | None = None

    async def initialize(self) -> None:
        """Initialize all components."""
        if self._initialized:
            return

        logger.info("Initializing LLM-OS...")

        # Initialize LLM router
        router_config = RouterConfig(
            default_provider=self.config.default_provider,
            local_first=True,
            cost_optimization=True,
            groq_api_key=self.system_config.groq.api_key,
        )
        self._llm_router = LLMRouter(config=router_config)
        await self._llm_router.initialize()

        # Initialize MCP orchestrator with external server settings
        external_settings = ExternalServerSettings(
            enabled_official=self.config.external_servers_enabled if self.config.use_external_servers else [],
            use_official_filesystem=self.config.use_external_servers and "filesystem" in self.config.external_servers_enabled,
            use_official_git=self.config.use_external_servers and "git" in self.config.external_servers_enabled,
        )

        orchestrator_config = OrchestratorConfig(
            auto_start_servers=self.config.auto_start_servers,
            security_policy=self.config.security_policy,
            external_servers=external_settings,
        )
        self._mcp_orchestrator = MCPOrchestrator(
            config=orchestrator_config,
            confirmation_handler=self._handle_confirmation,
        )
        # Skip builtin servers - using only filesystem MCP
        # self._mcp_orchestrator.register_builtin_servers()
        await self._mcp_orchestrator.initialize()

        # Initialize context manager
        history_path = self.config.history_path
        if history_path is None and self.config.persist_history:
            history_path = Path.home() / ".llm_os" / "history.json"

        self._context_manager = ContextManager(
            max_tokens=self.config.max_context_tokens,
            max_messages=self.config.max_messages,
            system_prompt=self._build_system_prompt(),
            persist_path=history_path,
        )

        self._initialized = True
        logger.info("LLM-OS initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown all components."""
        logger.info("Shutting down LLM-OS...")

        if self._mcp_orchestrator:
            await self._mcp_orchestrator.shutdown()

        if self._llm_router:
            await self._llm_router.close()

        self._initialized = False
        logger.info("LLM-OS shutdown complete")

    def _build_system_prompt(self) -> str:
        """Build the system prompt with current context."""
        import platform
        cwd = Path.cwd()
        os_name = platform.system()
        return DEFAULT_SYSTEM_PROMPT.format(cwd=cwd, os_name=os_name)

    async def process_message(
        self,
        user_input: str,
        stream: bool = False,
    ) -> str:
        """
        Process a user message and return the response.

        Args:
            user_input: The user's input message
            stream: Whether to stream the response

        Returns:
            The assistant's response
        """
        if not self._initialized:
            await self.initialize()

        # Add user message to context
        self._context_manager.add_user_message(user_input)

        # Resolve references in user input
        resolved_input = self._context_manager.resolve_references(user_input)

        # Get messages for LLM
        messages = self._context_manager.get_messages_for_llm()

        # Get available tools
        tools = self._mcp_orchestrator.get_tools_for_llm()

        # Classify task for routing
        classification = self._llm_router.classify_task(user_input)
        task_type = classification.task_type

        logger.debug(f"Task classified as: {task_type.value}")

        # Get response from LLM
        response = await self._llm_router.complete(
            messages=messages,
            tools=tools if tools else None,
            task_type=task_type,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        # Track provider and model used
        self._current_provider = response.provider
        self._current_model = response.model

        # Handle tool calls if present
        if response.tool_calls:
            response_text = await self._execute_tool_calls(
                response.tool_calls,
                messages,
                tools,
                task_type,
            )
        else:
            response_text = response.content

        # Add assistant response to context
        self._context_manager.add_assistant_message(response_text)

        return response_text

    async def _execute_tool_calls(
        self,
        tool_calls: list[ToolCall],
        messages: list[Message],
        tools: list[dict],
        task_type: TaskType,
    ) -> str:
        """Execute tool calls and get final response."""
        # Notify callback
        if self._tool_callback:
            for tc in tool_calls:
                await self._tool_callback(tc.name, "starting")

        # Execute tools
        results = await self._mcp_orchestrator.execute_tools(
            [ToolCall(
                id=tc.id,
                name=tc.name,
                arguments=tc.arguments,
            ) for tc in tool_calls]
        )

        # Notify completion
        if self._tool_callback:
            for tc in tool_calls:
                result = results.get(tc.id)
                success = result.success if result else False
                await self._tool_callback(tc.name, "complete", success)

        # Add tool results to context
        for tc in tool_calls:
            result = results.get(tc.id)
            if result:
                self._context_manager.add_tool_result(
                    tc.id,
                    result.get_text(),
                    tc.name,
                    not result.success,
                )

        # Get follow-up response from LLM
        messages = self._context_manager.get_messages_for_llm()

        follow_up = await self._llm_router.complete(
            messages=messages,
            tools=tools,
            task_type=task_type,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        # Handle recursive tool calls (with limit)
        if follow_up.tool_calls:
            # Limit recursion depth
            return await self._execute_tool_calls(
                follow_up.tool_calls,
                messages,
                tools,
                task_type,
            )

        return follow_up.content

    async def _handle_confirmation(
        self,
        tool_name: str,
        message: str,
    ) -> bool:
        """Handle tool confirmation requests."""
        if self._confirmation_callback:
            return await self._confirmation_callback(tool_name, message)

        # Default: always confirm
        logger.warning(f"Auto-confirming: {tool_name}")
        return True

    async def stream_message(
        self,
        user_input: str,
    ) -> AsyncIterator[str]:
        """
        Stream a response to a user message.

        Args:
            user_input: The user's input message

        Yields:
            Response chunks as they arrive
        """
        if not self._initialized:
            await self.initialize()

        # Add user message to context
        self._context_manager.add_user_message(user_input)

        # Get messages for LLM
        messages = self._context_manager.get_messages_for_llm()

        # Get available tools
        tools = self._mcp_orchestrator.get_tools_for_llm()

        # Classify task
        classification = self._llm_router.classify_task(user_input)

        # Stream response
        full_response = ""
        async for chunk in self._llm_router.stream(
            messages=messages,
            tools=tools if tools else None,
            task_type=classification.task_type,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        ):
            if chunk.content:
                full_response += chunk.content
                yield chunk.content

        # Add to context
        self._context_manager.add_assistant_message(full_response)

    def set_tool_callback(
        self,
        callback: callable,
    ) -> None:
        """Set callback for tool execution events."""
        self._tool_callback = callback

    def set_confirmation_callback(
        self,
        callback: callable,
    ) -> None:
        """Set callback for confirmation requests."""
        self._confirmation_callback = callback

    def clear_context(self) -> None:
        """Clear conversation context."""
        if self._context_manager:
            self._context_manager.clear()

    @property
    def current_provider(self) -> str:
        """Get the current LLM provider."""
        return self._current_provider

    @property
    def current_model(self) -> str | None:
        """Get the current LLM model."""
        return self._current_model

    @property
    def available_providers(self) -> list[str]:
        """Get available LLM providers."""
        if self._llm_router:
            return self._llm_router.available_providers
        return []

    @property
    def available_tools(self) -> list[Tool]:
        """Get available tools."""
        if self._mcp_orchestrator:
            return self._mcp_orchestrator.get_tools()
        return []

    def get_status(self) -> dict[str, Any]:
        """Get current system status."""
        status = {
            "initialized": self._initialized,
            "provider": self._current_provider,
            "model": self._current_model,
        }

        if self._llm_router:
            status["available_providers"] = self._llm_router.available_providers

        if self._mcp_orchestrator:
            mcp_status = self._mcp_orchestrator.get_status()
            status["mcp"] = mcp_status

        if self._context_manager:
            status["context"] = self._context_manager.get_summary()

        return status

    async def __aenter__(self) -> LLMOS:
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.shutdown()


async def create_llmos(
    config: LLMOSConfig | None = None,
    auto_initialize: bool = True,
) -> LLMOS:
    """
    Factory function to create and optionally initialize LLM-OS.

    Args:
        config: LLM-OS configuration
        auto_initialize: Whether to initialize immediately

    Returns:
        Configured LLMOS instance
    """
    llmos = LLMOS(config=config)

    if auto_initialize:
        await llmos.initialize()

    return llmos
