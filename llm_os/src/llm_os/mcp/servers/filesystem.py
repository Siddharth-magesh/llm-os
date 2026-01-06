"""
Filesystem MCP Server

Provides file and directory operations for the LLM-OS.
"""

from __future__ import annotations

import asyncio
import hashlib
import mimetypes
import os
import shutil
import stat
from datetime import datetime
from pathlib import Path
from typing import Any

from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types.tools import ToolResult, ParameterType


class FilesystemServer(BaseMCPServer):
    """
    MCP server for filesystem operations.

    Provides tools for:
    - Reading and writing files
    - Directory listing and navigation
    - File information and metadata
    - File search and pattern matching
    - File manipulation (copy, move, delete)
    """

    server_id = "filesystem"
    server_name = "Filesystem Server"
    server_version = "1.0.0"
    server_description = "File and directory operations"

    def __init__(
        self,
        base_path: str | None = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        allowed_extensions: list[str] | None = None,
    ):
        """
        Initialize filesystem server.

        Args:
            base_path: Base path for operations (defaults to home)
            max_file_size: Maximum file size to read/write
            allowed_extensions: Allowed file extensions (None = all)
        """
        super().__init__()
        self.base_path = Path(base_path) if base_path else Path.home()
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all filesystem tools."""

        # Read file
        self.register_tool(
            name="read_file",
            description="Read the contents of a file. Returns the file content as text.",
            handler=self._read_file,
            parameters=[
                self.string_param(
                    "path",
                    "Path to the file to read (absolute or relative to home)",
                ),
                self.integer_param(
                    "max_lines",
                    "Maximum number of lines to read (0 = all)",
                    required=False,
                    default=0,
                ),
                self.integer_param(
                    "offset",
                    "Line offset to start reading from",
                    required=False,
                    default=0,
                ),
            ],
            permission_level="read",
        )

        # Write file
        self.register_tool(
            name="write_file",
            description="Write content to a file. Creates the file if it doesn't exist.",
            handler=self._write_file,
            parameters=[
                self.string_param("path", "Path to the file to write"),
                self.string_param("content", "Content to write to the file"),
                self.boolean_param(
                    "append",
                    "Append to file instead of overwriting",
                    required=False,
                    default=False,
                ),
                self.boolean_param(
                    "create_dirs",
                    "Create parent directories if they don't exist",
                    required=False,
                    default=True,
                ),
            ],
            requires_confirmation=True,
            permission_level="write",
        )

        # List directory
        self.register_tool(
            name="list_directory",
            description="List files and directories in a path. Returns file names with type indicators.",
            handler=self._list_directory,
            parameters=[
                self.string_param(
                    "path",
                    "Path to the directory to list",
                    required=False,
                    default="~",
                ),
                self.boolean_param(
                    "show_hidden",
                    "Include hidden files (starting with .)",
                    required=False,
                    default=False,
                ),
                self.boolean_param(
                    "detailed",
                    "Show detailed information (size, permissions, dates)",
                    required=False,
                    default=False,
                ),
            ],
            permission_level="read",
        )

        # Get file info
        self.register_tool(
            name="file_info",
            description="Get detailed information about a file or directory.",
            handler=self._file_info,
            parameters=[
                self.string_param("path", "Path to the file or directory"),
            ],
            permission_level="read",
        )

        # Search files
        self.register_tool(
            name="search_files",
            description="Search for files by name pattern in a directory tree.",
            handler=self._search_files,
            parameters=[
                self.string_param("pattern", "Glob pattern to match (e.g., '*.py', '**/*.txt')"),
                self.string_param(
                    "path",
                    "Directory to search in",
                    required=False,
                    default="~",
                ),
                self.integer_param(
                    "max_results",
                    "Maximum number of results to return",
                    required=False,
                    default=50,
                ),
            ],
            permission_level="read",
        )

        # Search file contents
        self.register_tool(
            name="search_content",
            description="Search for text content within files.",
            handler=self._search_content,
            parameters=[
                self.string_param("query", "Text or regex pattern to search for"),
                self.string_param(
                    "path",
                    "Directory to search in",
                    required=False,
                    default="~",
                ),
                self.string_param(
                    "file_pattern",
                    "File pattern to filter (e.g., '*.py')",
                    required=False,
                    default="*",
                ),
                self.integer_param(
                    "max_results",
                    "Maximum number of results",
                    required=False,
                    default=20,
                ),
            ],
            permission_level="read",
        )

        # Create directory
        self.register_tool(
            name="create_directory",
            description="Create a new directory.",
            handler=self._create_directory,
            parameters=[
                self.string_param("path", "Path for the new directory"),
                self.boolean_param(
                    "parents",
                    "Create parent directories if needed",
                    required=False,
                    default=True,
                ),
            ],
            permission_level="write",
        )

        # Delete file/directory
        self.register_tool(
            name="delete",
            description="Delete a file or directory.",
            handler=self._delete,
            parameters=[
                self.string_param("path", "Path to delete"),
                self.boolean_param(
                    "recursive",
                    "Recursively delete directory contents",
                    required=False,
                    default=False,
                ),
            ],
            requires_confirmation=True,
            permission_level="write",
        )

        # Copy file/directory
        self.register_tool(
            name="copy",
            description="Copy a file or directory to a new location.",
            handler=self._copy,
            parameters=[
                self.string_param("source", "Source path"),
                self.string_param("destination", "Destination path"),
                self.boolean_param(
                    "recursive",
                    "Recursively copy directory contents",
                    required=False,
                    default=True,
                ),
            ],
            permission_level="write",
        )

        # Move/rename file
        self.register_tool(
            name="move",
            description="Move or rename a file or directory.",
            handler=self._move,
            parameters=[
                self.string_param("source", "Source path"),
                self.string_param("destination", "Destination path"),
            ],
            permission_level="write",
        )

        # Get current directory
        self.register_tool(
            name="get_cwd",
            description="Get the current working directory.",
            handler=self._get_cwd,
            parameters=[],
            permission_level="read",
        )

        # Change directory
        self.register_tool(
            name="change_directory",
            description="Change the current working directory.",
            handler=self._change_directory,
            parameters=[
                self.string_param("path", "Path to change to"),
            ],
            permission_level="read",
        )

        # Check if path exists
        self.register_tool(
            name="exists",
            description="Check if a file or directory exists.",
            handler=self._exists,
            parameters=[
                self.string_param("path", "Path to check"),
            ],
            permission_level="read",
        )

    def _resolve_path(self, path: str) -> Path:
        """Resolve a path, expanding ~ and making absolute."""
        p = Path(path).expanduser()
        if not p.is_absolute():
            p = self.base_path / p
        return p.resolve()

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable form."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def _format_permissions(self, mode: int) -> str:
        """Format file permissions as rwx string."""
        perms = ""
        for who in [stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
                    stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
                    stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH]:
            if mode & who:
                if who in [stat.S_IRUSR, stat.S_IRGRP, stat.S_IROTH]:
                    perms += "r"
                elif who in [stat.S_IWUSR, stat.S_IWGRP, stat.S_IWOTH]:
                    perms += "w"
                else:
                    perms += "x"
            else:
                perms += "-"
        return perms

    async def _read_file(
        self,
        path: str,
        max_lines: int = 0,
        offset: int = 0,
    ) -> ToolResult:
        """Read file contents."""
        try:
            resolved = self._resolve_path(path)

            if not resolved.exists():
                return ToolResult.error_result(f"File not found: {path}")

            if not resolved.is_file():
                return ToolResult.error_result(f"Not a file: {path}")

            # Check file size
            size = resolved.stat().st_size
            if size > self.max_file_size:
                return ToolResult.error_result(
                    f"File too large: {self._format_size(size)} "
                    f"(max: {self._format_size(self.max_file_size)})"
                )

            # Detect encoding and read
            content = await asyncio.to_thread(
                self._read_file_sync, resolved, max_lines, offset
            )

            return ToolResult.success_result(
                content,
                path=str(resolved),
                size=size,
                lines=content.count("\n") + 1 if content else 0,
            )

        except UnicodeDecodeError:
            return ToolResult.error_result(
                f"Cannot read file: appears to be binary"
            )
        except PermissionError:
            return ToolResult.error_result(f"Permission denied: {path}")
        except Exception as e:
            return ToolResult.error_result(f"Error reading file: {e}")

    def _read_file_sync(
        self,
        path: Path,
        max_lines: int,
        offset: int,
    ) -> str:
        """Synchronous file reading."""
        # Try UTF-8 first, then fallback encodings
        encodings = ["utf-8", "utf-16", "latin-1"]

        for encoding in encodings:
            try:
                with open(path, "r", encoding=encoding) as f:
                    if max_lines > 0 or offset > 0:
                        lines = f.readlines()
                        if offset > 0:
                            lines = lines[offset:]
                        if max_lines > 0:
                            lines = lines[:max_lines]
                        return "".join(lines)
                    return f.read()
            except UnicodeDecodeError:
                continue

        raise UnicodeDecodeError("utf-8", b"", 0, 1, "Could not decode file")

    async def _write_file(
        self,
        path: str,
        content: str,
        append: bool = False,
        create_dirs: bool = True,
    ) -> ToolResult:
        """Write content to file."""
        try:
            resolved = self._resolve_path(path)

            # Create parent directories if needed
            if create_dirs and not resolved.parent.exists():
                resolved.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            mode = "a" if append else "w"
            await asyncio.to_thread(
                lambda: resolved.write_text(content) if not append
                else self._append_file_sync(resolved, content)
            )

            return ToolResult.success_result(
                f"{'Appended to' if append else 'Wrote'} {len(content)} characters to {path}",
                path=str(resolved),
                bytes_written=len(content.encode("utf-8")),
            )

        except PermissionError:
            return ToolResult.error_result(f"Permission denied: {path}")
        except Exception as e:
            return ToolResult.error_result(f"Error writing file: {e}")

    def _append_file_sync(self, path: Path, content: str) -> None:
        """Synchronous file append."""
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)

    async def _list_directory(
        self,
        path: str = "~",
        show_hidden: bool = False,
        detailed: bool = False,
    ) -> ToolResult:
        """List directory contents."""
        try:
            resolved = self._resolve_path(path)

            if not resolved.exists():
                return ToolResult.error_result(f"Directory not found: {path}")

            if not resolved.is_dir():
                return ToolResult.error_result(f"Not a directory: {path}")

            entries = await asyncio.to_thread(
                self._list_directory_sync, resolved, show_hidden, detailed
            )

            if detailed:
                # Format as table
                lines = [f"Contents of {resolved}:", ""]
                lines.append(f"{'Type':<5} {'Permissions':<11} {'Size':>10} {'Modified':<20} Name")
                lines.append("-" * 70)
                lines.extend(entries)
            else:
                lines = [f"Contents of {resolved}:", ""] + entries

            return ToolResult.success_result(
                "\n".join(lines),
                path=str(resolved),
                count=len(entries),
            )

        except PermissionError:
            return ToolResult.error_result(f"Permission denied: {path}")
        except Exception as e:
            return ToolResult.error_result(f"Error listing directory: {e}")

    def _list_directory_sync(
        self,
        path: Path,
        show_hidden: bool,
        detailed: bool,
    ) -> list[str]:
        """Synchronous directory listing."""
        entries = []

        for item in sorted(path.iterdir()):
            name = item.name

            # Skip hidden files if not requested
            if not show_hidden and name.startswith("."):
                continue

            if detailed:
                try:
                    st = item.stat()
                    item_type = "d" if item.is_dir() else "f"
                    perms = self._format_permissions(st.st_mode)
                    size = self._format_size(st.st_size) if item.is_file() else "-"
                    modified = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")

                    if item.is_dir():
                        name += "/"

                    entries.append(f"{item_type:<5} {perms:<11} {size:>10} {modified:<20} {name}")
                except (PermissionError, OSError):
                    entries.append(f"?     ?????????? {'?':>10} {'?':<20} {name}")
            else:
                if item.is_dir():
                    entries.append(f"{name}/")
                elif item.is_symlink():
                    entries.append(f"{name}@")
                elif os.access(item, os.X_OK):
                    entries.append(f"{name}*")
                else:
                    entries.append(name)

        return entries

    async def _file_info(self, path: str) -> ToolResult:
        """Get detailed file information."""
        try:
            resolved = self._resolve_path(path)

            if not resolved.exists():
                return ToolResult.error_result(f"Path not found: {path}")

            st = resolved.stat()

            info = {
                "path": str(resolved),
                "name": resolved.name,
                "type": "directory" if resolved.is_dir() else "file",
                "size": st.st_size,
                "size_human": self._format_size(st.st_size),
                "permissions": self._format_permissions(st.st_mode),
                "permissions_octal": oct(st.st_mode)[-3:],
                "owner_uid": st.st_uid,
                "group_gid": st.st_gid,
                "created": datetime.fromtimestamp(st.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(st.st_atime).isoformat(),
            }

            if resolved.is_file():
                info["mime_type"] = mimetypes.guess_type(str(resolved))[0] or "unknown"

                # Calculate hash for small files
                if st.st_size < 1024 * 1024:  # 1MB
                    hash_md5 = hashlib.md5(resolved.read_bytes()).hexdigest()
                    info["md5"] = hash_md5

            if resolved.is_symlink():
                info["symlink_target"] = str(resolved.readlink())

            # Format output
            lines = [f"File Information: {resolved.name}", ""]
            for key, value in info.items():
                lines.append(f"  {key}: {value}")

            return ToolResult.success_result(
                "\n".join(lines),
                **info,
            )

        except PermissionError:
            return ToolResult.error_result(f"Permission denied: {path}")
        except Exception as e:
            return ToolResult.error_result(f"Error getting file info: {e}")

    async def _search_files(
        self,
        pattern: str,
        path: str = "~",
        max_results: int = 50,
    ) -> ToolResult:
        """Search for files by pattern."""
        try:
            resolved = self._resolve_path(path)

            if not resolved.exists():
                return ToolResult.error_result(f"Path not found: {path}")

            matches = await asyncio.to_thread(
                self._search_files_sync, resolved, pattern, max_results
            )

            if not matches:
                return ToolResult.success_result(
                    f"No files found matching '{pattern}' in {path}"
                )

            lines = [f"Found {len(matches)} file(s) matching '{pattern}':", ""]
            lines.extend(matches)

            if len(matches) == max_results:
                lines.append(f"\n(Results limited to {max_results})")

            return ToolResult.success_result(
                "\n".join(lines),
                matches=matches,
                count=len(matches),
            )

        except Exception as e:
            return ToolResult.error_result(f"Error searching files: {e}")

    def _search_files_sync(
        self,
        path: Path,
        pattern: str,
        max_results: int,
    ) -> list[str]:
        """Synchronous file search."""
        matches = []

        try:
            for match in path.glob(pattern):
                if len(matches) >= max_results:
                    break
                matches.append(str(match))
        except Exception:
            pass

        return matches

    async def _search_content(
        self,
        query: str,
        path: str = "~",
        file_pattern: str = "*",
        max_results: int = 20,
    ) -> ToolResult:
        """Search for content within files."""
        try:
            import re

            resolved = self._resolve_path(path)

            if not resolved.exists():
                return ToolResult.error_result(f"Path not found: {path}")

            # Compile regex
            try:
                regex = re.compile(query, re.IGNORECASE)
            except re.error:
                # Treat as literal string
                regex = re.compile(re.escape(query), re.IGNORECASE)

            matches = await asyncio.to_thread(
                self._search_content_sync, resolved, regex, file_pattern, max_results
            )

            if not matches:
                return ToolResult.success_result(
                    f"No matches found for '{query}' in {path}"
                )

            lines = [f"Found matches for '{query}':", ""]
            for file_path, line_num, line_content in matches:
                lines.append(f"{file_path}:{line_num}: {line_content.strip()}")

            return ToolResult.success_result(
                "\n".join(lines),
                match_count=len(matches),
            )

        except Exception as e:
            return ToolResult.error_result(f"Error searching content: {e}")

    def _search_content_sync(
        self,
        path: Path,
        regex: Any,
        file_pattern: str,
        max_results: int,
    ) -> list[tuple[str, int, str]]:
        """Synchronous content search."""
        matches = []

        for file_path in path.glob(f"**/{file_pattern}"):
            if len(matches) >= max_results:
                break

            if not file_path.is_file():
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            matches.append((str(file_path), line_num, line[:200]))
                            if len(matches) >= max_results:
                                break
            except (PermissionError, OSError):
                continue

        return matches

    async def _create_directory(
        self,
        path: str,
        parents: bool = True,
    ) -> ToolResult:
        """Create a directory."""
        try:
            resolved = self._resolve_path(path)

            if resolved.exists():
                return ToolResult.error_result(f"Path already exists: {path}")

            resolved.mkdir(parents=parents, exist_ok=False)

            return ToolResult.success_result(
                f"Created directory: {resolved}",
                path=str(resolved),
            )

        except PermissionError:
            return ToolResult.error_result(f"Permission denied: {path}")
        except Exception as e:
            return ToolResult.error_result(f"Error creating directory: {e}")

    async def _delete(
        self,
        path: str,
        recursive: bool = False,
    ) -> ToolResult:
        """Delete a file or directory."""
        try:
            resolved = self._resolve_path(path)

            if not resolved.exists():
                return ToolResult.error_result(f"Path not found: {path}")

            if resolved.is_dir():
                if recursive:
                    await asyncio.to_thread(shutil.rmtree, resolved)
                else:
                    resolved.rmdir()
            else:
                resolved.unlink()

            return ToolResult.success_result(
                f"Deleted: {resolved}",
                path=str(resolved),
            )

        except OSError as e:
            if "not empty" in str(e).lower():
                return ToolResult.error_result(
                    f"Directory not empty. Use recursive=True to delete contents."
                )
            return ToolResult.error_result(f"Error deleting: {e}")
        except Exception as e:
            return ToolResult.error_result(f"Error deleting: {e}")

    async def _copy(
        self,
        source: str,
        destination: str,
        recursive: bool = True,
    ) -> ToolResult:
        """Copy a file or directory."""
        try:
            src = self._resolve_path(source)
            dst = self._resolve_path(destination)

            if not src.exists():
                return ToolResult.error_result(f"Source not found: {source}")

            if src.is_dir():
                if not recursive:
                    return ToolResult.error_result(
                        "Source is a directory. Use recursive=True to copy."
                    )
                await asyncio.to_thread(shutil.copytree, src, dst)
            else:
                # Ensure parent exists
                dst.parent.mkdir(parents=True, exist_ok=True)
                await asyncio.to_thread(shutil.copy2, src, dst)

            return ToolResult.success_result(
                f"Copied {src} to {dst}",
                source=str(src),
                destination=str(dst),
            )

        except Exception as e:
            return ToolResult.error_result(f"Error copying: {e}")

    async def _move(
        self,
        source: str,
        destination: str,
    ) -> ToolResult:
        """Move or rename a file/directory."""
        try:
            src = self._resolve_path(source)
            dst = self._resolve_path(destination)

            if not src.exists():
                return ToolResult.error_result(f"Source not found: {source}")

            # Ensure parent exists
            dst.parent.mkdir(parents=True, exist_ok=True)

            await asyncio.to_thread(shutil.move, src, dst)

            return ToolResult.success_result(
                f"Moved {src} to {dst}",
                source=str(src),
                destination=str(dst),
            )

        except Exception as e:
            return ToolResult.error_result(f"Error moving: {e}")

    async def _get_cwd(self) -> ToolResult:
        """Get current working directory."""
        cwd = Path.cwd()
        return ToolResult.success_result(
            str(cwd),
            path=str(cwd),
        )

    async def _change_directory(self, path: str) -> ToolResult:
        """Change current working directory."""
        try:
            resolved = self._resolve_path(path)

            if not resolved.exists():
                return ToolResult.error_result(f"Path not found: {path}")

            if not resolved.is_dir():
                return ToolResult.error_result(f"Not a directory: {path}")

            os.chdir(resolved)
            self.base_path = resolved

            return ToolResult.success_result(
                f"Changed directory to: {resolved}",
                path=str(resolved),
            )

        except PermissionError:
            return ToolResult.error_result(f"Permission denied: {path}")
        except Exception as e:
            return ToolResult.error_result(f"Error changing directory: {e}")

    async def _exists(self, path: str) -> ToolResult:
        """Check if a path exists."""
        resolved = self._resolve_path(path)
        exists = resolved.exists()

        if exists:
            file_type = "directory" if resolved.is_dir() else "file"
            return ToolResult.success_result(
                f"Yes, '{path}' exists ({file_type})",
                exists=True,
                type=file_type,
                path=str(resolved),
            )
        else:
            return ToolResult.success_result(
                f"No, '{path}' does not exist",
                exists=False,
                path=str(resolved),
            )
