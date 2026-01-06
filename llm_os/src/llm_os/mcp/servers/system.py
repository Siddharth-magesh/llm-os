"""
System MCP Server

Provides system information and management capabilities for LLM-OS.
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types.tools import ToolResult


logger = logging.getLogger(__name__)


class SystemServer(BaseMCPServer):
    """
    MCP server for system operations.

    Provides tools for:
    - System information (CPU, memory, disk, network)
    - System monitoring
    - User information
    - Date/time operations
    - Audio/display control (where available)
    """

    server_id = "system"
    server_name = "System Server"
    server_version = "1.0.0"
    server_description = "System information and management"

    def __init__(self):
        """Initialize system server."""
        super().__init__()
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all system tools."""

        # Get system information
        self.register_tool(
            name="system_info",
            description="Get comprehensive system information including OS, CPU, memory, and disk.",
            handler=self._system_info,
            parameters=[],
            permission_level="read",
        )

        # Get CPU information
        self.register_tool(
            name="cpu_info",
            description="Get detailed CPU information and current usage.",
            handler=self._cpu_info,
            parameters=[],
            permission_level="read",
        )

        # Get memory information
        self.register_tool(
            name="memory_info",
            description="Get memory (RAM) usage information.",
            handler=self._memory_info,
            parameters=[],
            permission_level="read",
        )

        # Get disk information
        self.register_tool(
            name="disk_info",
            description="Get disk space usage information.",
            handler=self._disk_info,
            parameters=[
                self.string_param(
                    "path",
                    "Path to check disk usage for (default: /)",
                    required=False,
                    default="/",
                ),
            ],
            permission_level="read",
        )

        # Get network information
        self.register_tool(
            name="network_info",
            description="Get network interface information.",
            handler=self._network_info,
            parameters=[],
            permission_level="read",
        )

        # Get current date/time
        self.register_tool(
            name="get_datetime",
            description="Get current date and time.",
            handler=self._get_datetime,
            parameters=[
                self.string_param(
                    "format",
                    "Output format (iso, human, unix)",
                    required=False,
                    default="human",
                    enum=["iso", "human", "unix"],
                ),
                self.string_param(
                    "timezone",
                    "Timezone (e.g., 'UTC', 'America/New_York')",
                    required=False,
                ),
            ],
            permission_level="read",
        )

        # Get uptime
        self.register_tool(
            name="uptime",
            description="Get system uptime and load averages.",
            handler=self._uptime,
            parameters=[],
            permission_level="read",
        )

        # Get user information
        self.register_tool(
            name="user_info",
            description="Get current user information.",
            handler=self._user_info,
            parameters=[],
            permission_level="read",
        )

        # Get logged in users
        self.register_tool(
            name="logged_users",
            description="Get list of logged in users.",
            handler=self._logged_users,
            parameters=[],
            permission_level="read",
        )

        # Set volume
        self.register_tool(
            name="set_volume",
            description="Set system audio volume (0-100).",
            handler=self._set_volume,
            parameters=[
                self.integer_param(
                    "level",
                    "Volume level (0-100)",
                ),
                self.boolean_param(
                    "mute",
                    "Mute audio instead of setting level",
                    required=False,
                    default=False,
                ),
            ],
            permission_level="write",
        )

        # Get volume
        self.register_tool(
            name="get_volume",
            description="Get current system volume level.",
            handler=self._get_volume,
            parameters=[],
            permission_level="read",
        )

        # Set brightness
        self.register_tool(
            name="set_brightness",
            description="Set display brightness (0-100).",
            handler=self._set_brightness,
            parameters=[
                self.integer_param(
                    "level",
                    "Brightness level (0-100)",
                ),
            ],
            permission_level="write",
        )

        # Get battery info
        self.register_tool(
            name="battery_info",
            description="Get battery status (for laptops).",
            handler=self._battery_info,
            parameters=[],
            permission_level="read",
        )

        # Shutdown/reboot
        self.register_tool(
            name="power_control",
            description="Shutdown, reboot, or suspend the system.",
            handler=self._power_control,
            parameters=[
                self.string_param(
                    "action",
                    "Power action to perform",
                    enum=["shutdown", "reboot", "suspend", "hibernate"],
                ),
                self.integer_param(
                    "delay",
                    "Delay in seconds before action",
                    required=False,
                    default=0,
                ),
            ],
            requires_confirmation=True,
            permission_level="dangerous",
        )

        # Get installed packages
        self.register_tool(
            name="list_packages",
            description="List installed packages (apt/dpkg).",
            handler=self._list_packages,
            parameters=[
                self.string_param(
                    "filter",
                    "Filter packages by name",
                    required=False,
                ),
                self.integer_param(
                    "limit",
                    "Maximum packages to show",
                    required=False,
                    default=50,
                ),
            ],
            permission_level="read",
        )

        # Get system logs
        self.register_tool(
            name="system_logs",
            description="Get recent system logs.",
            handler=self._system_logs,
            parameters=[
                self.integer_param(
                    "lines",
                    "Number of log lines to retrieve",
                    required=False,
                    default=50,
                ),
                self.string_param(
                    "unit",
                    "Systemd unit to filter logs",
                    required=False,
                ),
                self.string_param(
                    "priority",
                    "Log priority filter (emerg, alert, crit, err, warning, notice, info, debug)",
                    required=False,
                    enum=["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug"],
                ),
            ],
            permission_level="read",
        )

    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"

    async def _system_info(self) -> ToolResult:
        """Get comprehensive system information."""
        try:
            info = {
                "hostname": platform.node(),
                "os": platform.system(),
                "os_release": platform.release(),
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor() or "Unknown",
                "python_version": platform.python_version(),
            }

            # Get distribution info on Linux
            if platform.system() == "Linux":
                try:
                    result = await asyncio.to_thread(
                        subprocess.run,
                        ["lsb_release", "-d", "-s"],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        info["distribution"] = result.stdout.strip()
                except Exception:
                    pass

            # Get kernel info
            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    ["uname", "-r"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    info["kernel"] = result.stdout.strip()
            except Exception:
                pass

            lines = ["System Information:", ""]
            for key, value in info.items():
                lines.append(f"  {key.replace('_', ' ').title()}: {value}")

            return ToolResult.success_result(
                "\n".join(lines),
                **info,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting system info: {e}")

    async def _cpu_info(self) -> ToolResult:
        """Get CPU information."""
        try:
            info: dict[str, Any] = {}

            # Get CPU model
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("model name"):
                            info["model"] = line.split(":")[1].strip()
                            break
            except Exception:
                info["model"] = platform.processor() or "Unknown"

            # Get CPU count
            info["cores"] = os.cpu_count() or 1

            # Get CPU usage
            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    ["grep", "cpu ", "/proc/stat"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    # Parse CPU stats
                    parts = result.stdout.split()
                    if len(parts) >= 5:
                        user = int(parts[1])
                        nice = int(parts[2])
                        system = int(parts[3])
                        idle = int(parts[4])
                        total = user + nice + system + idle
                        usage = ((total - idle) / total) * 100
                        info["usage_percent"] = round(usage, 1)
            except Exception:
                pass

            # Get load averages
            try:
                load1, load5, load15 = os.getloadavg()
                info["load_1min"] = round(load1, 2)
                info["load_5min"] = round(load5, 2)
                info["load_15min"] = round(load15, 2)
            except Exception:
                pass

            # Get CPU frequency
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("cpu MHz"):
                            info["frequency_mhz"] = float(line.split(":")[1].strip())
                            break
            except Exception:
                pass

            lines = ["CPU Information:", ""]
            lines.append(f"  Model: {info.get('model', 'Unknown')}")
            lines.append(f"  Cores: {info.get('cores', 'Unknown')}")
            if "usage_percent" in info:
                lines.append(f"  Usage: {info['usage_percent']}%")
            if "frequency_mhz" in info:
                lines.append(f"  Frequency: {info['frequency_mhz']:.0f} MHz")
            if "load_1min" in info:
                lines.append(f"  Load Average: {info['load_1min']}, {info['load_5min']}, {info['load_15min']}")

            return ToolResult.success_result(
                "\n".join(lines),
                **info,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting CPU info: {e}")

    async def _memory_info(self) -> ToolResult:
        """Get memory information."""
        try:
            info: dict[str, Any] = {}

            # Read /proc/meminfo
            with open("/proc/meminfo", "r") as f:
                meminfo = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip().split()[0]  # Get numeric part
                        try:
                            meminfo[key] = int(value) * 1024  # Convert KB to bytes
                        except ValueError:
                            pass

            total = meminfo.get("MemTotal", 0)
            available = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
            used = total - available
            swap_total = meminfo.get("SwapTotal", 0)
            swap_free = meminfo.get("SwapFree", 0)
            swap_used = swap_total - swap_free

            info = {
                "total": total,
                "total_human": self._format_bytes(total),
                "used": used,
                "used_human": self._format_bytes(used),
                "available": available,
                "available_human": self._format_bytes(available),
                "percent_used": round((used / total) * 100, 1) if total > 0 else 0,
                "swap_total": swap_total,
                "swap_total_human": self._format_bytes(swap_total),
                "swap_used": swap_used,
                "swap_used_human": self._format_bytes(swap_used),
            }

            lines = [
                "Memory Information:",
                "",
                f"  Total: {info['total_human']}",
                f"  Used: {info['used_human']} ({info['percent_used']}%)",
                f"  Available: {info['available_human']}",
                "",
                f"  Swap Total: {info['swap_total_human']}",
                f"  Swap Used: {info['swap_used_human']}",
            ]

            return ToolResult.success_result(
                "\n".join(lines),
                **info,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting memory info: {e}")

    async def _disk_info(self, path: str = "/") -> ToolResult:
        """Get disk usage information."""
        try:
            # Get disk usage for specified path
            result = await asyncio.to_thread(
                subprocess.run,
                ["df", "-B1", path],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return ToolResult.error_result(f"Failed to get disk info: {result.stderr}")

            lines = result.stdout.strip().split("\n")
            if len(lines) < 2:
                return ToolResult.error_result("No disk information available")

            # Parse the output
            parts = lines[1].split()
            if len(parts) < 6:
                return ToolResult.error_result("Invalid disk info format")

            total = int(parts[1])
            used = int(parts[2])
            available = int(parts[3])
            percent_str = parts[4].rstrip("%")
            mount_point = parts[5]

            info = {
                "filesystem": parts[0],
                "mount_point": mount_point,
                "total": total,
                "total_human": self._format_bytes(total),
                "used": used,
                "used_human": self._format_bytes(used),
                "available": available,
                "available_human": self._format_bytes(available),
                "percent_used": int(percent_str) if percent_str.isdigit() else 0,
            }

            # Get all mount points
            all_result = await asyncio.to_thread(
                subprocess.run,
                ["df", "-h", "--type=ext4", "--type=xfs", "--type=btrfs", "--type=ntfs", "--type=vfat"],
                capture_output=True,
                text=True,
            )

            output_lines = [
                f"Disk Information for {path}:",
                "",
                f"  Filesystem: {info['filesystem']}",
                f"  Mount Point: {info['mount_point']}",
                f"  Total: {info['total_human']}",
                f"  Used: {info['used_human']} ({info['percent_used']}%)",
                f"  Available: {info['available_human']}",
            ]

            if all_result.returncode == 0:
                output_lines.extend(["", "All Filesystems:", all_result.stdout])

            return ToolResult.success_result(
                "\n".join(output_lines),
                **info,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting disk info: {e}")

    async def _network_info(self) -> ToolResult:
        """Get network information."""
        try:
            # Get interface info using ip command
            result = await asyncio.to_thread(
                subprocess.run,
                ["ip", "-br", "addr"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return ToolResult.error_result("Failed to get network info")

            interfaces = []
            for line in result.stdout.strip().split("\n"):
                parts = line.split()
                if len(parts) >= 2:
                    iface = {
                        "name": parts[0],
                        "status": parts[1],
                        "addresses": parts[2:] if len(parts) > 2 else [],
                    }
                    interfaces.append(iface)

            # Get default gateway
            gateway_result = await asyncio.to_thread(
                subprocess.run,
                ["ip", "route", "show", "default"],
                capture_output=True,
                text=True,
            )

            gateway = None
            if gateway_result.returncode == 0 and gateway_result.stdout:
                parts = gateway_result.stdout.split()
                if "via" in parts:
                    idx = parts.index("via")
                    if idx + 1 < len(parts):
                        gateway = parts[idx + 1]

            lines = ["Network Interfaces:", ""]
            for iface in interfaces:
                lines.append(f"  {iface['name']}: {iface['status']}")
                for addr in iface["addresses"]:
                    lines.append(f"    {addr}")

            if gateway:
                lines.extend(["", f"Default Gateway: {gateway}"])

            return ToolResult.success_result(
                "\n".join(lines),
                interfaces=interfaces,
                gateway=gateway,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting network info: {e}")

    async def _get_datetime(
        self,
        format: str = "human",
        timezone: str | None = None,
    ) -> ToolResult:
        """Get current date and time."""
        try:
            now = datetime.now()

            if timezone:
                try:
                    import zoneinfo
                    tz = zoneinfo.ZoneInfo(timezone)
                    now = datetime.now(tz)
                except Exception:
                    return ToolResult.error_result(f"Invalid timezone: {timezone}")

            if format == "iso":
                formatted = now.isoformat()
            elif format == "unix":
                formatted = str(int(now.timestamp()))
            else:  # human
                formatted = now.strftime("%A, %B %d, %Y at %I:%M:%S %p")

            return ToolResult.success_result(
                formatted,
                datetime=now.isoformat(),
                timestamp=int(now.timestamp()),
                timezone=timezone or "local",
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting datetime: {e}")

    async def _uptime(self) -> ToolResult:
        """Get system uptime."""
        try:
            # Read uptime from /proc
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.read().split()[0])

            # Calculate days, hours, minutes
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)

            if days > 0:
                uptime_str = f"{days} days, {hours} hours, {minutes} minutes"
            elif hours > 0:
                uptime_str = f"{hours} hours, {minutes} minutes"
            else:
                uptime_str = f"{minutes} minutes"

            # Get load averages
            load1, load5, load15 = os.getloadavg()

            lines = [
                "System Uptime:",
                "",
                f"  Uptime: {uptime_str}",
                f"  Load Average: {load1:.2f}, {load5:.2f}, {load15:.2f}",
            ]

            return ToolResult.success_result(
                "\n".join(lines),
                uptime_seconds=uptime_seconds,
                uptime_human=uptime_str,
                load_1min=load1,
                load_5min=load5,
                load_15min=load15,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting uptime: {e}")

    async def _user_info(self) -> ToolResult:
        """Get current user information."""
        try:
            import pwd

            uid = os.getuid()
            gid = os.getgid()
            user_info = pwd.getpwuid(uid)

            info = {
                "username": user_info.pw_name,
                "uid": uid,
                "gid": gid,
                "home": user_info.pw_dir,
                "shell": user_info.pw_shell,
                "gecos": user_info.pw_gecos,
            }

            # Get groups
            groups_result = await asyncio.to_thread(
                subprocess.run,
                ["groups"],
                capture_output=True,
                text=True,
            )
            if groups_result.returncode == 0:
                info["groups"] = groups_result.stdout.strip().split()

            lines = [
                "User Information:",
                "",
                f"  Username: {info['username']}",
                f"  UID: {info['uid']}",
                f"  GID: {info['gid']}",
                f"  Home: {info['home']}",
                f"  Shell: {info['shell']}",
            ]
            if "groups" in info:
                lines.append(f"  Groups: {', '.join(info['groups'])}")

            return ToolResult.success_result(
                "\n".join(lines),
                **info,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting user info: {e}")

    async def _logged_users(self) -> ToolResult:
        """Get logged in users."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["who"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return ToolResult.error_result("Failed to get logged users")

            if not result.stdout.strip():
                return ToolResult.success_result(
                    "No users currently logged in",
                    users=[],
                )

            lines = ["Logged In Users:", "", result.stdout.strip()]

            return ToolResult.success_result(
                "\n".join(lines),
                users=result.stdout.strip().split("\n"),
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting logged users: {e}")

    async def _set_volume(
        self,
        level: int,
        mute: bool = False,
    ) -> ToolResult:
        """Set system volume."""
        try:
            if mute:
                cmd = ["amixer", "-q", "set", "Master", "mute"]
            else:
                # Clamp level
                level = max(0, min(100, level))
                cmd = ["amixer", "-q", "set", "Master", f"{level}%", "unmute"]

            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
            )

            if result.returncode != 0:
                # Try pactl as fallback
                if mute:
                    cmd = ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"]
                else:
                    cmd = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"]

                result = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                )

            if result.returncode == 0:
                if mute:
                    return ToolResult.success_result("Audio muted")
                else:
                    return ToolResult.success_result(f"Volume set to {level}%")
            else:
                return ToolResult.error_result("Failed to set volume. Audio system may not be available.")

        except Exception as e:
            return ToolResult.error_result(f"Error setting volume: {e}")

    async def _get_volume(self) -> ToolResult:
        """Get current volume level."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["amixer", "get", "Master"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Parse output for volume
                import re
                match = re.search(r"\[(\d+)%\]", result.stdout)
                if match:
                    volume = int(match.group(1))
                    muted = "[off]" in result.stdout

                    return ToolResult.success_result(
                        f"Volume: {volume}%" + (" (muted)" if muted else ""),
                        volume=volume,
                        muted=muted,
                    )

            return ToolResult.error_result("Could not get volume level")

        except Exception as e:
            return ToolResult.error_result(f"Error getting volume: {e}")

    async def _set_brightness(self, level: int) -> ToolResult:
        """Set display brightness."""
        try:
            level = max(1, min(100, level))  # Clamp between 1-100

            # Try xbacklight first
            result = await asyncio.to_thread(
                subprocess.run,
                ["xbacklight", "-set", str(level)],
                capture_output=True,
            )

            if result.returncode == 0:
                return ToolResult.success_result(f"Brightness set to {level}%")

            # Try brightnessctl as fallback
            result = await asyncio.to_thread(
                subprocess.run,
                ["brightnessctl", "set", f"{level}%"],
                capture_output=True,
            )

            if result.returncode == 0:
                return ToolResult.success_result(f"Brightness set to {level}%")

            return ToolResult.error_result(
                "Failed to set brightness. Install xbacklight or brightnessctl."
            )

        except Exception as e:
            return ToolResult.error_result(f"Error setting brightness: {e}")

    async def _battery_info(self) -> ToolResult:
        """Get battery status."""
        try:
            # Check for battery
            battery_path = Path("/sys/class/power_supply")
            batteries = list(battery_path.glob("BAT*"))

            if not batteries:
                return ToolResult.success_result(
                    "No battery detected (desktop system)",
                    has_battery=False,
                )

            bat = batteries[0]
            info: dict[str, Any] = {"has_battery": True}

            # Read battery info
            try:
                capacity = (bat / "capacity").read_text().strip()
                info["percent"] = int(capacity)
            except Exception:
                pass

            try:
                status = (bat / "status").read_text().strip()
                info["status"] = status
            except Exception:
                pass

            # AC adapter status
            ac_paths = list(battery_path.glob("AC*")) + list(battery_path.glob("ADP*"))
            if ac_paths:
                try:
                    online = (ac_paths[0] / "online").read_text().strip()
                    info["ac_connected"] = online == "1"
                except Exception:
                    pass

            lines = [
                "Battery Information:",
                "",
                f"  Level: {info.get('percent', 'Unknown')}%",
                f"  Status: {info.get('status', 'Unknown')}",
                f"  AC Power: {'Connected' if info.get('ac_connected') else 'Disconnected'}",
            ]

            return ToolResult.success_result(
                "\n".join(lines),
                **info,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting battery info: {e}")

    async def _power_control(
        self,
        action: str,
        delay: int = 0,
    ) -> ToolResult:
        """Control system power state."""
        try:
            commands = {
                "shutdown": ["systemctl", "poweroff"],
                "reboot": ["systemctl", "reboot"],
                "suspend": ["systemctl", "suspend"],
                "hibernate": ["systemctl", "hibernate"],
            }

            if action not in commands:
                return ToolResult.error_result(f"Unknown action: {action}")

            if delay > 0:
                await asyncio.sleep(delay)

            result = await asyncio.to_thread(
                subprocess.run,
                commands[action],
                capture_output=True,
            )

            if result.returncode == 0:
                return ToolResult.success_result(f"Initiated {action}")
            else:
                return ToolResult.error_result(
                    f"Failed to {action}: {result.stderr.decode()}"
                )

        except Exception as e:
            return ToolResult.error_result(f"Error with power control: {e}")

    async def _list_packages(
        self,
        filter: str | None = None,
        limit: int = 50,
    ) -> ToolResult:
        """List installed packages."""
        try:
            # Try dpkg first (Debian/Ubuntu)
            result = await asyncio.to_thread(
                subprocess.run,
                ["dpkg", "--get-selections"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                packages = []
                for line in result.stdout.strip().split("\n"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "install":
                        pkg_name = parts[0]
                        if filter is None or filter.lower() in pkg_name.lower():
                            packages.append(pkg_name)

                packages = packages[:limit]

                lines = [f"Installed Packages ({len(packages)} shown):", ""]
                lines.extend(f"  {pkg}" for pkg in packages)

                return ToolResult.success_result(
                    "\n".join(lines),
                    count=len(packages),
                    packages=packages,
                )

            # Try rpm as fallback
            result = await asyncio.to_thread(
                subprocess.run,
                ["rpm", "-qa"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                packages = result.stdout.strip().split("\n")
                if filter:
                    packages = [p for p in packages if filter.lower() in p.lower()]
                packages = packages[:limit]

                lines = [f"Installed Packages ({len(packages)} shown):", ""]
                lines.extend(f"  {pkg}" for pkg in packages)

                return ToolResult.success_result(
                    "\n".join(lines),
                    count=len(packages),
                    packages=packages,
                )

            return ToolResult.error_result("No supported package manager found")

        except Exception as e:
            return ToolResult.error_result(f"Error listing packages: {e}")

    async def _system_logs(
        self,
        lines: int = 50,
        unit: str | None = None,
        priority: str | None = None,
    ) -> ToolResult:
        """Get system logs."""
        try:
            cmd = ["journalctl", "-n", str(lines), "--no-pager"]

            if unit:
                cmd.extend(["-u", unit])

            if priority:
                cmd.extend(["-p", priority])

            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return ToolResult.error_result(
                    f"Failed to get logs: {result.stderr}"
                )

            return ToolResult.success_result(
                f"System Logs (last {lines} entries):\n\n{result.stdout}",
                lines_returned=len(result.stdout.split("\n")),
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting system logs: {e}")
