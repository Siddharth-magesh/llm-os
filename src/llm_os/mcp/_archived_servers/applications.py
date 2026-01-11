"""
Applications MCP Server

Provides application management capabilities for LLM-OS.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types.tools import ToolResult


logger = logging.getLogger(__name__)


@dataclass
class ApplicationInfo:
    """Information about an installed application."""
    name: str
    command: str
    description: str = ""
    category: str = "other"
    icon: str | None = None
    desktop_file: str | None = None
    version: str | None = None
    installed: bool = True


# Common Linux applications with their commands and categories
KNOWN_APPLICATIONS = {
    # Browsers
    "firefox": ApplicationInfo("Firefox", "firefox", "Web browser", "browser"),
    "chromium": ApplicationInfo("Chromium", "chromium-browser", "Web browser", "browser"),
    "google-chrome": ApplicationInfo("Google Chrome", "google-chrome", "Web browser", "browser"),
    "brave": ApplicationInfo("Brave", "brave-browser", "Web browser", "browser"),

    # Editors & IDEs
    "code": ApplicationInfo("Visual Studio Code", "code", "Code editor", "development"),
    "vscode": ApplicationInfo("Visual Studio Code", "code", "Code editor", "development"),
    "vim": ApplicationInfo("Vim", "vim", "Text editor", "editor"),
    "nvim": ApplicationInfo("Neovim", "nvim", "Text editor", "editor"),
    "nano": ApplicationInfo("Nano", "nano", "Text editor", "editor"),
    "gedit": ApplicationInfo("Gedit", "gedit", "Text editor", "editor"),
    "sublime": ApplicationInfo("Sublime Text", "subl", "Code editor", "development"),
    "atom": ApplicationInfo("Atom", "atom", "Code editor", "development"),

    # Terminals
    "gnome-terminal": ApplicationInfo("GNOME Terminal", "gnome-terminal", "Terminal", "terminal"),
    "konsole": ApplicationInfo("Konsole", "konsole", "Terminal", "terminal"),
    "alacritty": ApplicationInfo("Alacritty", "alacritty", "Terminal", "terminal"),
    "kitty": ApplicationInfo("Kitty", "kitty", "Terminal", "terminal"),
    "tilix": ApplicationInfo("Tilix", "tilix", "Terminal", "terminal"),

    # File Managers
    "nautilus": ApplicationInfo("Files (Nautilus)", "nautilus", "File manager", "filemanager"),
    "dolphin": ApplicationInfo("Dolphin", "dolphin", "File manager", "filemanager"),
    "thunar": ApplicationInfo("Thunar", "thunar", "File manager", "filemanager"),
    "pcmanfm": ApplicationInfo("PCManFM", "pcmanfm", "File manager", "filemanager"),
    "ranger": ApplicationInfo("Ranger", "ranger", "File manager (CLI)", "filemanager"),

    # Media Players
    "vlc": ApplicationInfo("VLC", "vlc", "Media player", "media"),
    "mpv": ApplicationInfo("MPV", "mpv", "Media player", "media"),
    "rhythmbox": ApplicationInfo("Rhythmbox", "rhythmbox", "Music player", "media"),
    "spotify": ApplicationInfo("Spotify", "spotify", "Music streaming", "media"),
    "audacity": ApplicationInfo("Audacity", "audacity", "Audio editor", "media"),

    # Graphics
    "gimp": ApplicationInfo("GIMP", "gimp", "Image editor", "graphics"),
    "inkscape": ApplicationInfo("Inkscape", "inkscape", "Vector graphics", "graphics"),
    "blender": ApplicationInfo("Blender", "blender", "3D modeling", "graphics"),
    "krita": ApplicationInfo("Krita", "krita", "Digital painting", "graphics"),

    # Office
    "libreoffice": ApplicationInfo("LibreOffice", "libreoffice", "Office suite", "office"),
    "writer": ApplicationInfo("LibreOffice Writer", "libreoffice --writer", "Word processor", "office"),
    "calc": ApplicationInfo("LibreOffice Calc", "libreoffice --calc", "Spreadsheet", "office"),
    "evince": ApplicationInfo("Document Viewer", "evince", "PDF viewer", "office"),
    "okular": ApplicationInfo("Okular", "okular", "Document viewer", "office"),

    # Communication
    "discord": ApplicationInfo("Discord", "discord", "Chat", "communication"),
    "slack": ApplicationInfo("Slack", "slack", "Team communication", "communication"),
    "telegram": ApplicationInfo("Telegram", "telegram-desktop", "Messaging", "communication"),
    "thunderbird": ApplicationInfo("Thunderbird", "thunderbird", "Email client", "communication"),

    # System
    "htop": ApplicationInfo("htop", "htop", "Process viewer", "system"),
    "btop": ApplicationInfo("btop", "btop", "System monitor", "system"),
    "gnome-system-monitor": ApplicationInfo("System Monitor", "gnome-system-monitor", "System monitor", "system"),

    # Development Tools
    "docker": ApplicationInfo("Docker", "docker", "Container platform", "development"),
    "git": ApplicationInfo("Git", "git", "Version control", "development"),
    "python3": ApplicationInfo("Python", "python3", "Programming language", "development"),
    "node": ApplicationInfo("Node.js", "node", "JavaScript runtime", "development"),
}


class ApplicationsServer(BaseMCPServer):
    """
    MCP server for application management.

    Provides tools for:
    - Launching applications
    - Listing installed applications
    - Checking application availability
    - Managing application windows (limited)
    """

    server_id = "applications"
    server_name = "Applications Server"
    server_version = "1.0.0"
    server_description = "Application management and launching"

    def __init__(self):
        """Initialize applications server."""
        super().__init__()
        self._running_apps: dict[str, subprocess.Popen] = {}
        self._app_cache: dict[str, ApplicationInfo] = {}
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all application tools."""

        # Launch application
        self.register_tool(
            name="launch_app",
            description="Launch an application by name. Supports common Linux applications.",
            handler=self._launch_app,
            parameters=[
                self.string_param(
                    "name",
                    "Application name or command (e.g., 'firefox', 'code', 'vlc')",
                ),
                self.array_param(
                    "args",
                    "Command line arguments to pass to the application",
                    required=False,
                ),
                self.boolean_param(
                    "wait",
                    "Wait for application to exit",
                    required=False,
                    default=False,
                ),
            ],
            requires_confirmation=True,
            permission_level="execute",
        )

        # Close application
        self.register_tool(
            name="close_app",
            description="Close a running application by name or PID.",
            handler=self._close_app,
            parameters=[
                self.string_param(
                    "name",
                    "Application name or PID to close",
                ),
                self.boolean_param(
                    "force",
                    "Force kill the application",
                    required=False,
                    default=False,
                ),
            ],
            requires_confirmation=True,
            permission_level="execute",
        )

        # List installed applications
        self.register_tool(
            name="list_apps",
            description="List installed applications, optionally filtered by category.",
            handler=self._list_apps,
            parameters=[
                self.string_param(
                    "category",
                    "Filter by category (browser, editor, media, etc.)",
                    required=False,
                    enum=["browser", "development", "editor", "terminal", "filemanager",
                          "media", "graphics", "office", "communication", "system", "other"],
                ),
                self.boolean_param(
                    "all",
                    "Show all known applications including not installed",
                    required=False,
                    default=False,
                ),
            ],
            permission_level="read",
        )

        # Check if application is installed
        self.register_tool(
            name="app_installed",
            description="Check if an application is installed.",
            handler=self._app_installed,
            parameters=[
                self.string_param(
                    "name",
                    "Application name to check",
                ),
            ],
            permission_level="read",
        )

        # Get application info
        self.register_tool(
            name="app_info",
            description="Get information about an application.",
            handler=self._app_info,
            parameters=[
                self.string_param(
                    "name",
                    "Application name",
                ),
            ],
            permission_level="read",
        )

        # List running applications
        self.register_tool(
            name="running_apps",
            description="List currently running applications.",
            handler=self._running_apps_list,
            parameters=[],
            permission_level="read",
        )

        # Open file with default application
        self.register_tool(
            name="open_with_default",
            description="Open a file with its default application.",
            handler=self._open_with_default,
            parameters=[
                self.string_param(
                    "path",
                    "Path to the file to open",
                ),
            ],
            requires_confirmation=True,
            permission_level="execute",
        )

        # Open URL in browser
        self.register_tool(
            name="open_url",
            description="Open a URL in the default web browser.",
            handler=self._open_url,
            parameters=[
                self.string_param(
                    "url",
                    "URL to open",
                ),
                self.string_param(
                    "browser",
                    "Specific browser to use (optional)",
                    required=False,
                ),
            ],
            requires_confirmation=True,
            permission_level="execute",
        )

    def _is_installed(self, command: str) -> bool:
        """Check if a command is available."""
        # Handle commands with arguments
        cmd = command.split()[0]
        return shutil.which(cmd) is not None

    def _get_app_info(self, name: str) -> ApplicationInfo | None:
        """Get application info by name."""
        name_lower = name.lower()

        # Check known applications
        if name_lower in KNOWN_APPLICATIONS:
            app = KNOWN_APPLICATIONS[name_lower]
            app.installed = self._is_installed(app.command)
            return app

        # Check if it's a direct command
        if self._is_installed(name):
            return ApplicationInfo(
                name=name,
                command=name,
                description="",
                category="other",
                installed=True,
            )

        return None

    async def _launch_app(
        self,
        name: str,
        args: list[str] | None = None,
        wait: bool = False,
    ) -> ToolResult:
        """Launch an application."""
        try:
            app_info = self._get_app_info(name)

            if not app_info:
                return ToolResult.error_result(
                    f"Application '{name}' not found. "
                    "Use list_apps to see available applications."
                )

            if not app_info.installed:
                return ToolResult.error_result(
                    f"Application '{name}' is not installed."
                )

            # Build command
            cmd_parts = app_info.command.split()
            if args:
                cmd_parts.extend(args)

            logger.info(f"Launching: {' '.join(cmd_parts)}")

            # Launch process
            if wait:
                # Run and wait
                result = await asyncio.to_thread(
                    subprocess.run,
                    cmd_parts,
                    capture_output=True,
                    text=True,
                )
                return ToolResult.success_result(
                    f"Application '{app_info.name}' exited with code {result.returncode}",
                    exit_code=result.returncode,
                    stdout=result.stdout[:1000] if result.stdout else "",
                    stderr=result.stderr[:1000] if result.stderr else "",
                )
            else:
                # Run in background
                env = os.environ.copy()
                # Suppress GTK warnings
                env["GTK_MODULES"] = ""

                proc = subprocess.Popen(
                    cmd_parts,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=env,
                    start_new_session=True,
                )

                self._running_apps[name] = proc

                return ToolResult.success_result(
                    f"Launched {app_info.name} (PID: {proc.pid})",
                    name=app_info.name,
                    pid=proc.pid,
                    command=app_info.command,
                )

        except FileNotFoundError:
            return ToolResult.error_result(f"Command not found: {name}")
        except PermissionError:
            return ToolResult.error_result(f"Permission denied launching {name}")
        except Exception as e:
            return ToolResult.error_result(f"Error launching application: {e}")

    async def _close_app(
        self,
        name: str,
        force: bool = False,
    ) -> ToolResult:
        """Close an application."""
        try:
            import signal

            # Check if it's a PID
            try:
                pid = int(name)
            except ValueError:
                pid = None

            if pid:
                # Kill by PID
                sig = signal.SIGKILL if force else signal.SIGTERM
                os.kill(pid, sig)
                return ToolResult.success_result(
                    f"Sent {'SIGKILL' if force else 'SIGTERM'} to PID {pid}",
                    pid=pid,
                )

            # Check if we launched it
            if name in self._running_apps:
                proc = self._running_apps[name]
                if force:
                    proc.kill()
                else:
                    proc.terminate()
                del self._running_apps[name]
                return ToolResult.success_result(
                    f"Closed {name}",
                    name=name,
                )

            # Try to find and kill by process name
            result = await asyncio.to_thread(
                subprocess.run,
                ["pkill", "-9" if force else "", "-f", name],
                capture_output=True,
            )

            if result.returncode == 0:
                return ToolResult.success_result(
                    f"Closed processes matching '{name}'",
                    name=name,
                )
            else:
                return ToolResult.error_result(
                    f"No running processes found matching '{name}'"
                )

        except ProcessLookupError:
            return ToolResult.error_result(f"Process not found: {name}")
        except PermissionError:
            return ToolResult.error_result(f"Permission denied closing {name}")
        except Exception as e:
            return ToolResult.error_result(f"Error closing application: {e}")

    async def _list_apps(
        self,
        category: str | None = None,
        all: bool = False,
    ) -> ToolResult:
        """List available applications."""
        try:
            apps = []

            for name, app in KNOWN_APPLICATIONS.items():
                app.installed = self._is_installed(app.command)

                if not all and not app.installed:
                    continue

                if category and app.category != category:
                    continue

                apps.append(app)

            if not apps:
                return ToolResult.success_result(
                    f"No applications found" +
                    (f" in category '{category}'" if category else "")
                )

            # Group by category
            by_category: dict[str, list[ApplicationInfo]] = {}
            for app in apps:
                if app.category not in by_category:
                    by_category[app.category] = []
                by_category[app.category].append(app)

            lines = ["Available Applications:", ""]

            for cat, cat_apps in sorted(by_category.items()):
                lines.append(f"  {cat.upper()}:")
                for app in sorted(cat_apps, key=lambda a: a.name):
                    status = "✓" if app.installed else "✗"
                    lines.append(f"    {status} {app.name} ({app.command})")
                lines.append("")

            return ToolResult.success_result(
                "\n".join(lines),
                count=len(apps),
                categories=list(by_category.keys()),
            )

        except Exception as e:
            return ToolResult.error_result(f"Error listing applications: {e}")

    async def _app_installed(self, name: str) -> ToolResult:
        """Check if application is installed."""
        app_info = self._get_app_info(name)

        if app_info and app_info.installed:
            return ToolResult.success_result(
                f"Yes, '{name}' is installed ({app_info.command})",
                installed=True,
                name=app_info.name,
                command=app_info.command,
            )
        else:
            return ToolResult.success_result(
                f"No, '{name}' is not installed",
                installed=False,
            )

    async def _app_info(self, name: str) -> ToolResult:
        """Get application information."""
        app_info = self._get_app_info(name)

        if not app_info:
            return ToolResult.error_result(f"Application '{name}' not found")

        lines = [
            f"Application: {app_info.name}",
            f"  Command: {app_info.command}",
            f"  Category: {app_info.category}",
            f"  Installed: {'Yes' if app_info.installed else 'No'}",
        ]

        if app_info.description:
            lines.append(f"  Description: {app_info.description}")

        # Try to get version
        if app_info.installed:
            version = await self._get_version(app_info.command)
            if version:
                lines.append(f"  Version: {version}")

        return ToolResult.success_result(
            "\n".join(lines),
            name=app_info.name,
            command=app_info.command,
            category=app_info.category,
            installed=app_info.installed,
        )

    async def _get_version(self, command: str) -> str | None:
        """Try to get application version."""
        cmd = command.split()[0]

        for flag in ["--version", "-v", "-V", "version"]:
            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    [cmd, flag],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout:
                    # Get first line
                    return result.stdout.split("\n")[0].strip()[:100]
            except Exception:
                continue

        return None

    async def _running_apps_list(self) -> ToolResult:
        """List running applications."""
        try:
            # Get list of running processes
            result = await asyncio.to_thread(
                subprocess.run,
                ["ps", "aux"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return ToolResult.error_result("Failed to list processes")

            # Parse output
            lines = result.stdout.strip().split("\n")
            header = lines[0]

            # Find known applications in process list
            running = []
            for line in lines[1:]:
                for name, app in KNOWN_APPLICATIONS.items():
                    cmd = app.command.split()[0]
                    if cmd in line and "defunct" not in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            running.append({
                                "name": app.name,
                                "command": cmd,
                                "pid": parts[1],
                            })
                        break

            if not running:
                return ToolResult.success_result(
                    "No known applications currently running",
                    running=[],
                )

            # Format output
            output_lines = ["Running Applications:", ""]
            seen = set()
            for app in running:
                key = app["command"]
                if key not in seen:
                    output_lines.append(f"  {app['name']} (PID: {app['pid']})")
                    seen.add(key)

            return ToolResult.success_result(
                "\n".join(output_lines),
                running=running,
                count=len(seen),
            )

        except Exception as e:
            return ToolResult.error_result(f"Error listing running apps: {e}")

    async def _open_with_default(self, path: str) -> ToolResult:
        """Open file with default application."""
        try:
            resolved = Path(path).expanduser().resolve()

            if not resolved.exists():
                return ToolResult.error_result(f"File not found: {path}")

            # Use xdg-open on Linux
            result = await asyncio.to_thread(
                subprocess.run,
                ["xdg-open", str(resolved)],
                capture_output=True,
            )

            if result.returncode == 0:
                return ToolResult.success_result(
                    f"Opened {resolved.name} with default application",
                    path=str(resolved),
                )
            else:
                return ToolResult.error_result(
                    f"Failed to open file: {result.stderr.decode()}"
                )

        except FileNotFoundError:
            return ToolResult.error_result(
                "xdg-open not found. Install xdg-utils."
            )
        except Exception as e:
            return ToolResult.error_result(f"Error opening file: {e}")

    async def _open_url(
        self,
        url: str,
        browser: str | None = None,
    ) -> ToolResult:
        """Open URL in browser."""
        try:
            # Validate URL
            if not url.startswith(("http://", "https://", "file://")):
                url = "https://" + url

            if browser:
                app_info = self._get_app_info(browser)
                if not app_info or not app_info.installed:
                    return ToolResult.error_result(
                        f"Browser '{browser}' not found or not installed"
                    )
                cmd = [app_info.command.split()[0], url]
            else:
                cmd = ["xdg-open", url]

            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
            )

            if result.returncode == 0:
                return ToolResult.success_result(
                    f"Opened {url}" + (f" in {browser}" if browser else ""),
                    url=url,
                    browser=browser,
                )
            else:
                return ToolResult.error_result(
                    f"Failed to open URL: {result.stderr.decode()}"
                )

        except Exception as e:
            return ToolResult.error_result(f"Error opening URL: {e}")

    async def shutdown(self) -> None:
        """Shutdown server and clean up."""
        # Terminate any apps we launched
        for name, proc in self._running_apps.items():
            try:
                proc.terminate()
            except Exception:
                pass

        self._running_apps.clear()
        await super().shutdown()
