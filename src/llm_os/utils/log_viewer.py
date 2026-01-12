"""
LLM-OS Log Viewer

Utility for viewing and analyzing LLM-OS logs.

Features:
- View logs by category
- Filter by level, time range, keywords
- Search across all logs
- Generate statistics and summaries
- Export filtered logs
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# Default log directory
DEFAULT_LOG_DIR = Path.home() / ".llm_os" / "logs"

# ANSI color codes for output
COLORS = {
    "DEBUG": "\033[36m",      # Cyan
    "INFO": "\033[32m",       # Green
    "WARNING": "\033[33m",    # Yellow
    "ERROR": "\033[31m",      # Red
    "CRITICAL": "\033[35m",   # Magenta
    "RESET": "\033[0m",       # Reset
    "BOLD": "\033[1m",        # Bold
}


class LogViewer:
    """Log viewer and analyzer."""

    def __init__(self, log_dir: Path = DEFAULT_LOG_DIR):
        """
        Initialize log viewer.

        Args:
            log_dir: Directory containing log files
        """
        self.log_dir = Path(log_dir)
        if not self.log_dir.exists():
            print(f"Error: Log directory not found: {self.log_dir}")
            sys.exit(1)

    def list_log_files(self) -> list[Path]:
        """List all log files."""
        return sorted(self.log_dir.glob("*.log"))

    def read_log_file(self, log_file: Path) -> list[dict[str, Any]]:
        """
        Read and parse log file.

        Args:
            log_file: Path to log file

        Returns:
            List of log entries (as dicts)
        """
        entries = []
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
        return entries

    def filter_entries(
        self,
        entries: list[dict[str, Any]],
        level: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        keyword: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Filter log entries.

        Args:
            entries: List of log entries
            level: Filter by log level
            since: Filter by start time
            until: Filter by end time
            keyword: Filter by keyword in message

        Returns:
            Filtered list of entries
        """
        filtered = entries

        # Filter by level
        if level:
            filtered = [e for e in filtered if e.get("level") == level.upper()]

        # Filter by time range
        if since:
            filtered = [
                e for e in filtered
                if datetime.fromisoformat(e.get("timestamp", "")) >= since
            ]

        if until:
            filtered = [
                e for e in filtered
                if datetime.fromisoformat(e.get("timestamp", "")) <= until
            ]

        # Filter by keyword
        if keyword:
            keyword_lower = keyword.lower()
            filtered = [
                e for e in filtered
                if keyword_lower in e.get("message", "").lower()
                or keyword_lower in json.dumps(e).lower()
            ]

        return filtered

    def format_entry(self, entry: dict[str, Any], color: bool = True) -> str:
        """
        Format log entry for display.

        Args:
            entry: Log entry
            color: Whether to use colors

        Returns:
            Formatted string
        """
        # Extract fields
        timestamp = entry.get("timestamp", "")
        level = entry.get("level", "INFO")
        category = entry.get("category", "unknown")
        message = entry.get("message", "")

        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            timestamp_str = timestamp

        # Add color
        if color:
            level_color = COLORS.get(level, "")
            reset = COLORS["RESET"]
            bold = COLORS["BOLD"]
        else:
            level_color = reset = bold = ""

        # Format main line
        output = f"{level_color}[{timestamp_str}] {level:8s} [{category:12s}]{reset} {message}"

        # Add category-specific details
        if category == "user":
            if "user_input" in entry:
                output += f"\n  {bold}Input:{reset} {self._truncate(entry['user_input'], 80)}"
            if "response_summary" in entry:
                output += f"\n  {bold}Response:{reset} {self._truncate(entry['response_summary'], 80)}"
            if entry.get("tool_calls"):
                output += f"\n  {bold}Tools:{reset} {', '.join(entry['tool_calls'])}"
            if "duration_ms" in entry:
                output += f"\n  {bold}Duration:{reset} {entry['duration_ms']:.2f}ms"

        elif category == "tool":
            if "tool_name" in entry:
                output += f"\n  {bold}Tool:{reset} {entry['tool_name']} ({entry.get('tool_server', 'unknown')})"
            if "parameters" in entry:
                output += f"\n  {bold}Params:{reset} {self._truncate(str(entry['parameters']), 100)}"
            if "duration_ms" in entry:
                output += f"\n  {bold}Duration:{reset} {entry['duration_ms']:.2f}ms"

        elif category == "llm":
            if "provider" in entry and "model" in entry:
                output += f"\n  {bold}Provider:{reset} {entry['provider']}, {bold}Model:{reset} {entry['model']}"
            if "total_tokens" in entry:
                output += f"\n  {bold}Tokens:{reset} {entry['total_tokens']} ({entry.get('prompt_tokens', 0)}+{entry.get('completion_tokens', 0)})"
            if "duration_ms" in entry:
                output += f"\n  {bold}Duration:{reset} {entry['duration_ms']:.2f}ms"

        elif category == "system":
            if "event_type" in entry:
                output += f"\n  {bold}Event:{reset} {entry['event_type']}"
            if "component" in entry:
                output += f"\n  {bold}Component:{reset} {entry['component']}"

        elif category == "security":
            if "event_type" in entry:
                output += f"\n  {bold}Event:{reset} {entry['event_type']}"
            if "resource" in entry:
                output += f"\n  {bold}Resource:{reset} {entry['resource']}"
            if "allowed" in entry:
                allowed_str = "✓ Allowed" if entry["allowed"] else "✗ Denied"
                output += f"\n  {bold}Result:{reset} {allowed_str}"

        elif category == "performance":
            if "operation" in entry:
                output += f"\n  {bold}Operation:{reset} {entry['operation']}"
            if "duration_ms" in entry:
                output += f"\n  {bold}Duration:{reset} {entry['duration_ms']:.2f}ms"

        return output

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text to max length."""
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."

    def view_logs(
        self,
        category: Optional[str] = None,
        level: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        keyword: Optional[str] = None,
        tail: Optional[int] = None,
        color: bool = True,
    ) -> None:
        """
        View logs with filters.

        Args:
            category: Log category to view (None for all)
            level: Filter by log level
            since: Filter by start time
            until: Filter by end time
            keyword: Filter by keyword
            tail: Show only last N entries
            color: Whether to use colors
        """
        # Determine which log files to read
        if category:
            log_files = [self.log_dir / f"{category}.log"]
            # Handle different naming conventions
            if not log_files[0].exists():
                possible_names = [
                    f"{category}_interactions.log",
                    f"{category}_health.log",
                    f"{category}_executions.log",
                    f"{category}_calls.log",
                ]
                for name in possible_names:
                    file_path = self.log_dir / name
                    if file_path.exists():
                        log_files = [file_path]
                        break
        else:
            log_files = self.list_log_files()

        # Read and filter entries from all files
        all_entries = []
        for log_file in log_files:
            if not log_file.exists():
                continue
            entries = self.read_log_file(log_file)
            filtered = self.filter_entries(entries, level, since, until, keyword)
            all_entries.extend(filtered)

        # Sort by timestamp
        all_entries.sort(key=lambda e: e.get("timestamp", ""))

        # Apply tail limit
        if tail:
            all_entries = all_entries[-tail:]

        # Display entries
        if not all_entries:
            print("No log entries found matching criteria.")
            return

        print(f"\n{COLORS['BOLD']}Showing {len(all_entries)} log entries{COLORS['RESET']}\n")

        for entry in all_entries:
            print(self.format_entry(entry, color))
            print()  # Blank line between entries

    def get_statistics(
        self,
        category: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Generate statistics from logs.

        Args:
            category: Log category (None for all)
            since: Start time
            until: End time

        Returns:
            Statistics dictionary
        """
        # Read all relevant log files
        if category:
            log_files = [self.log_dir / f"{category}.log"]
        else:
            log_files = self.list_log_files()

        all_entries = []
        for log_file in log_files:
            if not log_file.exists():
                continue
            entries = self.read_log_file(log_file)
            filtered = self.filter_entries(entries, since=since, until=until)
            all_entries.extend(filtered)

        # Calculate statistics
        stats = {
            "total_entries": len(all_entries),
            "by_level": Counter(e.get("level") for e in all_entries),
            "by_category": Counter(e.get("category") for e in all_entries),
        }

        # Category-specific statistics
        if category == "user" or not category:
            user_entries = [e for e in all_entries if e.get("category") == "user"]
            if user_entries:
                total_duration = sum(e.get("duration_ms", 0) for e in user_entries)
                avg_duration = total_duration / len(user_entries) if user_entries else 0
                success_count = sum(1 for e in user_entries if e.get("success", True))
                stats["user"] = {
                    "total_interactions": len(user_entries),
                    "success_rate": (success_count / len(user_entries) * 100) if user_entries else 0,
                    "avg_duration_ms": avg_duration,
                }

        if category == "llm" or not category:
            llm_entries = [e for e in all_entries if e.get("category") == "llm"]
            if llm_entries:
                total_tokens = sum(e.get("total_tokens", 0) for e in llm_entries)
                total_duration = sum(e.get("duration_ms", 0) for e in llm_entries)
                providers = Counter(e.get("provider") for e in llm_entries)
                stats["llm"] = {
                    "total_calls": len(llm_entries),
                    "total_tokens": total_tokens,
                    "avg_tokens_per_call": total_tokens / len(llm_entries) if llm_entries else 0,
                    "avg_duration_ms": total_duration / len(llm_entries) if llm_entries else 0,
                    "by_provider": dict(providers),
                }

        if category == "tool" or not category:
            tool_entries = [e for e in all_entries if e.get("category") == "tool"]
            if tool_entries:
                tools_used = Counter(e.get("tool_name") for e in tool_entries)
                success_count = sum(1 for e in tool_entries if e.get("success", True))
                stats["tool"] = {
                    "total_executions": len(tool_entries),
                    "success_rate": (success_count / len(tool_entries) * 100) if tool_entries else 0,
                    "most_used_tools": dict(tools_used.most_common(10)),
                }

        return stats

    def print_statistics(self, stats: dict[str, Any]) -> None:
        """Print statistics in formatted way."""
        bold = COLORS["BOLD"]
        reset = COLORS["RESET"]
        green = COLORS["INFO"]
        yellow = COLORS["WARNING"]

        print(f"\n{bold}=== Log Statistics ==={reset}\n")

        print(f"{bold}Overall:{reset}")
        print(f"  Total Entries: {stats['total_entries']}")
        print(f"  By Level: {dict(stats['by_level'])}")
        print(f"  By Category: {dict(stats['by_category'])}")

        if "user" in stats:
            print(f"\n{bold}User Interactions:{reset}")
            user_stats = stats["user"]
            print(f"  Total: {user_stats['total_interactions']}")
            print(f"  Success Rate: {green}{user_stats['success_rate']:.1f}%{reset}")
            print(f"  Avg Duration: {user_stats['avg_duration_ms']:.2f}ms")

        if "llm" in stats:
            print(f"\n{bold}LLM Calls:{reset}")
            llm_stats = stats["llm"]
            print(f"  Total Calls: {llm_stats['total_calls']}")
            print(f"  Total Tokens: {llm_stats['total_tokens']}")
            print(f"  Avg Tokens/Call: {llm_stats['avg_tokens_per_call']:.0f}")
            print(f"  Avg Duration: {llm_stats['avg_duration_ms']:.2f}ms")
            print(f"  By Provider: {llm_stats['by_provider']}")

        if "tool" in stats:
            print(f"\n{bold}Tool Executions:{reset}")
            tool_stats = stats["tool"]
            print(f"  Total: {tool_stats['total_executions']}")
            print(f"  Success Rate: {green}{tool_stats['success_rate']:.1f}%{reset}")
            print(f"  Most Used Tools:")
            for tool, count in list(tool_stats['most_used_tools'].items())[:5]:
                print(f"    - {tool}: {count}")

        print()


def parse_time(time_str: str) -> datetime:
    """Parse time string to datetime."""
    # Try different formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%H:%M:%S",
        "%H:%M",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            # If no date provided, use today
            if fmt.startswith("%H"):
                dt = datetime.now().replace(
                    hour=dt.hour,
                    minute=dt.minute,
                    second=dt.second,
                )
            return dt
        except ValueError:
            continue

    # Try relative time
    if time_str.endswith("m"):
        minutes = int(time_str[:-1])
        return datetime.now() - timedelta(minutes=minutes)
    elif time_str.endswith("h"):
        hours = int(time_str[:-1])
        return datetime.now() - timedelta(hours=hours)
    elif time_str.endswith("d"):
        days = int(time_str[:-1])
        return datetime.now() - timedelta(days=days)

    raise ValueError(f"Cannot parse time: {time_str}")


def main():
    """Main entry point for log viewer CLI."""
    parser = argparse.ArgumentParser(
        prog="llm-os-logs",
        description="View and analyze LLM-OS logs",
    )

    parser.add_argument(
        "-d", "--log-dir",
        type=Path,
        default=DEFAULT_LOG_DIR,
        help="Log directory",
    )

    parser.add_argument(
        "-c", "--category",
        choices=["user", "system", "tool", "llm", "security", "performance"],
        help="Log category to view",
    )

    parser.add_argument(
        "-l", "--level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Filter by log level",
    )

    parser.add_argument(
        "-s", "--since",
        type=str,
        help="Show logs since time (YYYY-MM-DD HH:MM:SS, HH:MM, or 30m, 2h, 1d)",
    )

    parser.add_argument(
        "-u", "--until",
        type=str,
        help="Show logs until time",
    )

    parser.add_argument(
        "-k", "--keyword",
        type=str,
        help="Filter by keyword",
    )

    parser.add_argument(
        "-n", "--tail",
        type=int,
        help="Show only last N entries",
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics instead of logs",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available log files",
    )

    args = parser.parse_args()

    # Create viewer
    viewer = LogViewer(args.log_dir)

    # List files if requested
    if args.list:
        print(f"\nLog files in {args.log_dir}:\n")
        for log_file in viewer.list_log_files():
            size = log_file.stat().st_size / 1024  # KB
            print(f"  {log_file.name:30s} ({size:.1f} KB)")
        print()
        return

    # Parse time filters
    since = parse_time(args.since) if args.since else None
    until = parse_time(args.until) if args.until else None

    # Show statistics or logs
    if args.stats:
        stats = viewer.get_statistics(args.category, since, until)
        viewer.print_statistics(stats)
    else:
        viewer.view_logs(
            category=args.category,
            level=args.level,
            since=since,
            until=until,
            keyword=args.keyword,
            tail=args.tail,
            color=not args.no_color,
        )


if __name__ == "__main__":
    main()
