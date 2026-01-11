"""
Process MCP Server

Provides process and shell command execution capabilities for LLM-OS.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shlex
import signal
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types.tools import ToolResult


logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a process."""
    pid: int
    name: str
    status: str
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    user: str = ""
    command: str = ""
    started: datetime | None = None


@dataclass
class CommandResult:
    """Result of a shell command."""
    command: str
    return_code: int
    stdout: str
    stderr: str
    duration_ms: float


class ProcessServer(BaseMCPServer):
    """
    MCP server for process and shell operations.

    Provides tools for:
    - Running shell commands
    - Process listing and monitoring
    - Process management (kill, etc.)
    - Environment variable management
    """

    server_id = "process"
    server_name = "Process Server"
    server_version = "1.0.0"
    server_description = "Process and shell command operations"

    # Commands that are blocked for safety
    BLOCKED_COMMANDS = {
        "rm -rf /",
        "rm -rf /*",
        "dd if=/dev/zero",
        "dd if=/dev/random of=/dev/sda",
        "mkfs.",
        ":(){ :|:& };:",  # Fork bomb
        "> /dev/sda",
        "chmod -R 777 /",
        "chown -R",
        "mv /* /dev/null",
    }

    # Maximum output size to capture
    MAX_OUTPUT_SIZE = 100_000  # 100KB

    def __init__(
        self,
        shell: str = "/bin/bash",
        timeout: float = 60.0,
        working_dir: str | None = None,
    ):
        """
        Initialize process server.

        Args:
            shell: Shell to use for command execution
            timeout: Default command timeout in seconds
            working_dir: Default working directory
        """
        super().__init__()
        self.shell = shell
        self.default_timeout = timeout
        self.working_dir = working_dir or os.getcwd()
        self._background_processes: dict[str, asyncio.subprocess.Process] = {}
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all process tools."""

        # Run shell command
        self.register_tool(
            name="run_command",
            description="Execute a shell command and return the output. Use for system commands, scripts, etc.",
            handler=self._run_command,
            parameters=[
                self.string_param(
                    "command",
                    "The shell command to execute",
                ),
                self.number_param(
                    "timeout",
                    "Command timeout in seconds (default: 60)",
                    required=False,
                    default=60.0,
                ),
                self.string_param(
                    "working_dir",
                    "Working directory for the command",
                    required=False,
                ),
                self.boolean_param(
                    "capture_output",
                    "Capture stdout/stderr (default: true)",
                    required=False,
                    default=True,
                ),
            ],
            requires_confirmation=True,
            permission_level="execute",
        )

        # Run command in background
        self.register_tool(
            name="run_background",
            description="Run a command in the background. Returns a process ID to monitor later.",
            handler=self._run_background,
            parameters=[
                self.string_param(
                    "command",
                    "The shell command to execute",
                ),
                self.string_param(
                    "name",
                    "Name to identify this background process",
                    required=False,
                ),
            ],
            requires_confirmation=True,
            permission_level="execute",
        )

        # Check background process
        self.register_tool(
            name="check_background",
            description="Check the status of a background process.",
            handler=self._check_background,
            parameters=[
                self.string_param(
                    "name",
                    "Name or PID of the background process",
                ),
            ],
            permission_level="read",
        )

        # List processes
        self.register_tool(
            name="list_processes",
            description="List running processes, optionally filtered by name or user.",
            handler=self._list_processes,
            parameters=[
                self.string_param(
                    "filter",
                    "Filter by process name or command",
                    required=False,
                ),
                self.string_param(
                    "user",
                    "Filter by username",
                    required=False,
                ),
                self.integer_param(
                    "limit",
                    "Maximum number of processes to return",
                    required=False,
                    default=50,
                ),
                self.string_param(
                    "sort_by",
                    "Sort by: cpu, memory, pid, name",
                    required=False,
                    default="cpu",
                    enum=["cpu", "memory", "pid", "name"],
                ),
            ],
            permission_level="read",
        )

        # Get process info
        self.register_tool(
            name="process_info",
            description="Get detailed information about a specific process.",
            handler=self._process_info,
            parameters=[
                self.integer_param(
                    "pid",
                    "Process ID",
                ),
            ],
            permission_level="read",
        )

        # Kill process
        self.register_tool(
            name="kill_process",
            description="Terminate a process by PID.",
            handler=self._kill_process,
            parameters=[
                self.integer_param(
                    "pid",
                    "Process ID to kill",
                ),
                self.string_param(
                    "signal",
                    "Signal to send (TERM, KILL, HUP, etc.)",
                    required=False,
                    default="TERM",
                    enum=["TERM", "KILL", "HUP", "INT", "QUIT", "USR1", "USR2"],
                ),
            ],
            requires_confirmation=True,
            permission_level="system",
        )

        # Get environment variable
        self.register_tool(
            name="get_env",
            description="Get the value of an environment variable.",
            handler=self._get_env,
            parameters=[
                self.string_param(
                    "name",
                    "Environment variable name",
                ),
            ],
            permission_level="read",
        )

        # Set environment variable
        self.register_tool(
            name="set_env",
            description="Set an environment variable for this session.",
            handler=self._set_env,
            parameters=[
                self.string_param(
                    "name",
                    "Environment variable name",
                ),
                self.string_param(
                    "value",
                    "Value to set",
                ),
            ],
            permission_level="write",
        )

        # List environment variables
        self.register_tool(
            name="list_env",
            description="List all environment variables.",
            handler=self._list_env,
            parameters=[
                self.string_param(
                    "filter",
                    "Filter by name prefix",
                    required=False,
                ),
            ],
            permission_level="read",
        )

        # Which command
        self.register_tool(
            name="which",
            description="Find the location of a command/executable.",
            handler=self._which,
            parameters=[
                self.string_param(
                    "command",
                    "Command name to locate",
                ),
            ],
            permission_level="read",
        )

    def _is_command_safe(self, command: str) -> tuple[bool, str]:
        """Check if a command is safe to execute."""
        command_lower = command.lower().strip()

        # Check blocked commands
        for blocked in self.BLOCKED_COMMANDS:
            if blocked.lower() in command_lower:
                return False, f"Blocked command pattern: {blocked}"

        # Check for dangerous patterns
        dangerous_patterns = [
            (r"rm\s+-[rf]+\s+/(?!\w)", "Dangerous rm command on root"),
            (r"dd\s+.*of=/dev/sd", "Writing to block device"),
            (r"mkfs\.", "Filesystem formatting"),
            (r">\s*/dev/sd", "Writing to block device"),
            (r"\|\s*sh\b", "Piping to shell"),
            (r"curl.*\|\s*bash", "Remote code execution"),
            (r"wget.*\|\s*bash", "Remote code execution"),
            (r"sudo\s+rm", "Sudo with rm"),
        ]

        import re
        for pattern, reason in dangerous_patterns:
            if re.search(pattern, command_lower):
                return False, reason

        return True, ""

    async def _run_command(
        self,
        command: str,
        timeout: float = 60.0,
        working_dir: str | None = None,
        capture_output: bool = True,
    ) -> ToolResult:
        """Execute a shell command."""
        try:
            # Safety check
            is_safe, reason = self._is_command_safe(command)
            if not is_safe:
                return ToolResult.error_result(
                    f"Command blocked for safety: {reason}"
                )

            work_dir = working_dir or self.working_dir
            start_time = datetime.now()

            logger.info(f"Executing command: {command}")

            # Run the command
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
                cwd=work_dir,
                env=os.environ.copy(),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                proc.kill()
                return ToolResult.error_result(
                    f"Command timed out after {timeout} seconds"
                )

            duration = (datetime.now() - start_time).total_seconds() * 1000

            # Process output
            stdout_str = ""
            stderr_str = ""

            if capture_output:
                stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
                stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

                # Truncate if too large
                if len(stdout_str) > self.MAX_OUTPUT_SIZE:
                    stdout_str = stdout_str[:self.MAX_OUTPUT_SIZE] + "\n... (truncated)"
                if len(stderr_str) > self.MAX_OUTPUT_SIZE:
                    stderr_str = stderr_str[:self.MAX_OUTPUT_SIZE] + "\n... (truncated)"

            # Format result
            result_lines = []

            if proc.returncode == 0:
                result_lines.append(f"Command completed successfully (exit code: 0)")
            else:
                result_lines.append(f"Command exited with code: {proc.returncode}")

            if stdout_str:
                result_lines.append("\nOutput:")
                result_lines.append(stdout_str)

            if stderr_str:
                result_lines.append("\nErrors/Warnings:")
                result_lines.append(stderr_str)

            return ToolResult.success_result(
                "\n".join(result_lines),
                command=command,
                return_code=proc.returncode,
                duration_ms=duration,
            )

        except Exception as e:
            logger.error(f"Command execution error: {e}", exc_info=True)
            return ToolResult.error_result(f"Execution error: {e}")

    async def _run_background(
        self,
        command: str,
        name: str | None = None,
    ) -> ToolResult:
        """Run a command in the background."""
        try:
            # Safety check
            is_safe, reason = self._is_command_safe(command)
            if not is_safe:
                return ToolResult.error_result(
                    f"Command blocked for safety: {reason}"
                )

            # Generate name if not provided
            if not name:
                name = f"bg_{datetime.now().strftime('%H%M%S')}"

            # Start process
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
                env=os.environ.copy(),
            )

            self._background_processes[name] = proc

            return ToolResult.success_result(
                f"Started background process '{name}' (PID: {proc.pid})",
                name=name,
                pid=proc.pid,
                command=command,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error starting background process: {e}")

    async def _check_background(self, name: str) -> ToolResult:
        """Check a background process."""
        try:
            # Check if it's a PID
            try:
                pid = int(name)
                # Find by PID
                for proc_name, proc in self._background_processes.items():
                    if proc.pid == pid:
                        name = proc_name
                        break
            except ValueError:
                pass

            if name not in self._background_processes:
                return ToolResult.error_result(
                    f"Background process '{name}' not found"
                )

            proc = self._background_processes[name]

            if proc.returncode is None:
                # Still running
                return ToolResult.success_result(
                    f"Process '{name}' is still running (PID: {proc.pid})",
                    name=name,
                    pid=proc.pid,
                    status="running",
                )
            else:
                # Completed - get output
                stdout, stderr = await proc.communicate()

                stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
                stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

                # Clean up
                del self._background_processes[name]

                lines = [f"Process '{name}' completed (exit code: {proc.returncode})"]
                if stdout_str:
                    lines.append("\nOutput:")
                    lines.append(stdout_str[:5000])
                if stderr_str:
                    lines.append("\nErrors:")
                    lines.append(stderr_str[:2000])

                return ToolResult.success_result(
                    "\n".join(lines),
                    name=name,
                    status="completed",
                    return_code=proc.returncode,
                )

        except Exception as e:
            return ToolResult.error_result(f"Error checking process: {e}")

    async def _list_processes(
        self,
        filter: str | None = None,
        user: str | None = None,
        limit: int = 50,
        sort_by: str = "cpu",
    ) -> ToolResult:
        """List running processes."""
        try:
            # Use ps command
            cmd = ["ps", "aux", "--sort", f"-{sort_by}%" if sort_by in ["cpu", "memory"] else sort_by]

            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return ToolResult.error_result(f"Failed to list processes: {result.stderr}")

            lines = result.stdout.strip().split("\n")
            header = lines[0]
            processes = lines[1:]

            # Filter
            if filter:
                filter_lower = filter.lower()
                processes = [p for p in processes if filter_lower in p.lower()]

            if user:
                processes = [p for p in processes if p.split()[0] == user]

            # Limit
            processes = processes[:limit]

            # Format output
            output_lines = [
                f"Running Processes ({len(processes)} shown):",
                "",
                header,
                "-" * 80,
            ]
            output_lines.extend(processes)

            return ToolResult.success_result(
                "\n".join(output_lines),
                count=len(processes),
            )

        except Exception as e:
            return ToolResult.error_result(f"Error listing processes: {e}")

    async def _process_info(self, pid: int) -> ToolResult:
        """Get detailed process information."""
        try:
            # Check if process exists
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return ToolResult.error_result(f"Process {pid} not found")
            except PermissionError:
                pass  # Process exists but we can't signal it

            # Get process info using ps
            result = await asyncio.to_thread(
                subprocess.run,
                ["ps", "-p", str(pid), "-o", "pid,ppid,user,%cpu,%mem,vsz,rss,stat,start,time,comm,args"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return ToolResult.error_result(f"Failed to get process info: {result.stderr}")

            lines = result.stdout.strip().split("\n")
            if len(lines) < 2:
                return ToolResult.error_result(f"Process {pid} not found")

            # Parse info
            header = lines[0].split()
            values = lines[1].split(None, len(header) - 1)

            info = dict(zip(header, values))

            output_lines = [
                f"Process Information (PID: {pid})",
                "",
                f"  Command: {info.get('COMM', 'N/A')}",
                f"  Arguments: {info.get('ARGS', 'N/A')}",
                f"  User: {info.get('USER', 'N/A')}",
                f"  Parent PID: {info.get('PPID', 'N/A')}",
                f"  Status: {info.get('STAT', 'N/A')}",
                f"  CPU %: {info.get('%CPU', 'N/A')}",
                f"  Memory %: {info.get('%MEM', 'N/A')}",
                f"  Virtual Memory: {info.get('VSZ', 'N/A')} KB",
                f"  Resident Memory: {info.get('RSS', 'N/A')} KB",
                f"  Start Time: {info.get('START', 'N/A')}",
                f"  CPU Time: {info.get('TIME', 'N/A')}",
            ]

            # Try to get additional info from /proc
            try:
                # Read cmdline
                cmdline_path = f"/proc/{pid}/cmdline"
                if os.path.exists(cmdline_path):
                    with open(cmdline_path, "r") as f:
                        cmdline = f.read().replace("\0", " ").strip()
                        if cmdline:
                            output_lines.append(f"  Full Command: {cmdline[:200]}")

                # Read cwd
                cwd_path = f"/proc/{pid}/cwd"
                if os.path.exists(cwd_path):
                    cwd = os.readlink(cwd_path)
                    output_lines.append(f"  Working Directory: {cwd}")

            except (PermissionError, OSError):
                pass

            return ToolResult.success_result(
                "\n".join(output_lines),
                pid=pid,
                **{k.lower(): v for k, v in info.items()},
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting process info: {e}")

    async def _kill_process(
        self,
        pid: int,
        signal: str = "TERM",
    ) -> ToolResult:
        """Kill a process."""
        try:
            # Map signal name to number
            signal_map = {
                "TERM": 15,
                "KILL": 9,
                "HUP": 1,
                "INT": 2,
                "QUIT": 3,
                "USR1": 10,
                "USR2": 12,
            }

            sig_num = signal_map.get(signal.upper(), 15)

            os.kill(pid, sig_num)

            return ToolResult.success_result(
                f"Sent signal {signal} to process {pid}",
                pid=pid,
                signal=signal,
            )

        except ProcessLookupError:
            return ToolResult.error_result(f"Process {pid} not found")
        except PermissionError:
            return ToolResult.error_result(f"Permission denied to kill process {pid}")
        except Exception as e:
            return ToolResult.error_result(f"Error killing process: {e}")

    async def _get_env(self, name: str) -> ToolResult:
        """Get environment variable."""
        value = os.environ.get(name)

        if value is not None:
            return ToolResult.success_result(
                f"{name}={value}",
                name=name,
                value=value,
            )
        else:
            return ToolResult.success_result(
                f"Environment variable '{name}' is not set",
                name=name,
                value=None,
            )

    async def _set_env(self, name: str, value: str) -> ToolResult:
        """Set environment variable."""
        try:
            os.environ[name] = value

            return ToolResult.success_result(
                f"Set {name}={value}",
                name=name,
                value=value,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error setting environment variable: {e}")

    async def _list_env(self, filter: str | None = None) -> ToolResult:
        """List environment variables."""
        try:
            env_vars = dict(os.environ)

            if filter:
                filter_upper = filter.upper()
                env_vars = {k: v for k, v in env_vars.items() if k.upper().startswith(filter_upper)}

            # Sort by name
            sorted_vars = sorted(env_vars.items())

            lines = ["Environment Variables:", ""]
            for name, value in sorted_vars:
                # Truncate long values
                if len(value) > 100:
                    value = value[:97] + "..."
                lines.append(f"  {name}={value}")

            return ToolResult.success_result(
                "\n".join(lines),
                count=len(sorted_vars),
            )

        except Exception as e:
            return ToolResult.error_result(f"Error listing environment: {e}")

    async def _which(self, command: str) -> ToolResult:
        """Find command location."""
        try:
            import shutil

            location = shutil.which(command)

            if location:
                return ToolResult.success_result(
                    f"{command}: {location}",
                    command=command,
                    location=location,
                )
            else:
                return ToolResult.success_result(
                    f"{command} not found in PATH",
                    command=command,
                    location=None,
                )

        except Exception as e:
            return ToolResult.error_result(f"Error finding command: {e}")

    async def shutdown(self) -> None:
        """Shutdown server and clean up background processes."""
        # Kill background processes
        for name, proc in self._background_processes.items():
            try:
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

        self._background_processes.clear()
        await super().shutdown()
