"""
Git MCP Server

Provides Git version control operations for LLM-OS.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from llm_os.mcp.servers.base import BaseMCPServer
from llm_os.mcp.types.tools import ToolResult


logger = logging.getLogger(__name__)


@dataclass
class GitStatus:
    """Git repository status."""
    branch: str
    is_clean: bool
    staged: list[str]
    modified: list[str]
    untracked: list[str]
    ahead: int = 0
    behind: int = 0


class GitServer(BaseMCPServer):
    """
    MCP server for Git operations.

    Provides tools for:
    - Repository status and information
    - Staging and committing changes
    - Branch management
    - Remote operations
    - Log and diff viewing
    """

    server_id = "git"
    server_name = "Git Server"
    server_version = "1.0.0"
    server_description = "Git version control operations"

    def __init__(self, default_repo: str | None = None):
        """
        Initialize Git server.

        Args:
            default_repo: Default repository path
        """
        super().__init__()
        self.default_repo = default_repo or os.getcwd()
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all Git tools."""

        # Git status
        self.register_tool(
            name="git_status",
            description="Get the status of a Git repository.",
            handler=self._git_status,
            parameters=[
                self.string_param(
                    "path",
                    "Path to the repository (default: current directory)",
                    required=False,
                ),
            ],
            permission_level="read",
        )

        # Git log
        self.register_tool(
            name="git_log",
            description="Show commit history.",
            handler=self._git_log,
            parameters=[
                self.integer_param(
                    "count",
                    "Number of commits to show",
                    required=False,
                    default=10,
                ),
                self.string_param(
                    "branch",
                    "Branch name (default: current branch)",
                    required=False,
                ),
                self.boolean_param(
                    "oneline",
                    "Show one line per commit",
                    required=False,
                    default=True,
                ),
                self.string_param(
                    "path",
                    "Repository path",
                    required=False,
                ),
            ],
            permission_level="read",
        )

        # Git diff
        self.register_tool(
            name="git_diff",
            description="Show changes in the working directory or between commits.",
            handler=self._git_diff,
            parameters=[
                self.boolean_param(
                    "staged",
                    "Show staged changes",
                    required=False,
                    default=False,
                ),
                self.string_param(
                    "file",
                    "Show diff for specific file",
                    required=False,
                ),
                self.string_param(
                    "commit",
                    "Compare with specific commit",
                    required=False,
                ),
                self.string_param(
                    "path",
                    "Repository path",
                    required=False,
                ),
            ],
            permission_level="read",
        )

        # Git add
        self.register_tool(
            name="git_add",
            description="Stage files for commit.",
            handler=self._git_add,
            parameters=[
                self.array_param(
                    "files",
                    "Files to stage (use '.' for all)",
                ),
                self.string_param(
                    "path",
                    "Repository path",
                    required=False,
                ),
            ],
            permission_level="write",
        )

        # Git commit
        self.register_tool(
            name="git_commit",
            description="Commit staged changes.",
            handler=self._git_commit,
            parameters=[
                self.string_param(
                    "message",
                    "Commit message",
                ),
                self.boolean_param(
                    "all",
                    "Automatically stage modified files (-a)",
                    required=False,
                    default=False,
                ),
                self.string_param(
                    "path",
                    "Repository path",
                    required=False,
                ),
            ],
            requires_confirmation=True,
            permission_level="write",
        )

        # Git branch
        self.register_tool(
            name="git_branch",
            description="List, create, or delete branches.",
            handler=self._git_branch,
            parameters=[
                self.string_param(
                    "action",
                    "Action: list, create, delete, rename",
                    required=False,
                    default="list",
                    enum=["list", "create", "delete", "rename"],
                ),
                self.string_param(
                    "name",
                    "Branch name (for create/delete/rename)",
                    required=False,
                ),
                self.string_param(
                    "new_name",
                    "New branch name (for rename)",
                    required=False,
                ),
                self.string_param(
                    "path",
                    "Repository path",
                    required=False,
                ),
            ],
            permission_level="write",
        )

        # Git checkout
        self.register_tool(
            name="git_checkout",
            description="Switch branches or restore files.",
            handler=self._git_checkout,
            parameters=[
                self.string_param(
                    "target",
                    "Branch name, commit hash, or file path",
                ),
                self.boolean_param(
                    "create",
                    "Create new branch (-b)",
                    required=False,
                    default=False,
                ),
                self.string_param(
                    "path",
                    "Repository path",
                    required=False,
                ),
            ],
            requires_confirmation=True,
            permission_level="write",
        )

        # Git pull
        self.register_tool(
            name="git_pull",
            description="Fetch and merge from remote.",
            handler=self._git_pull,
            parameters=[
                self.string_param(
                    "remote",
                    "Remote name",
                    required=False,
                    default="origin",
                ),
                self.string_param(
                    "branch",
                    "Branch to pull",
                    required=False,
                ),
                self.string_param(
                    "path",
                    "Repository path",
                    required=False,
                ),
            ],
            requires_confirmation=True,
            permission_level="write",
        )

        # Git push
        self.register_tool(
            name="git_push",
            description="Push commits to remote.",
            handler=self._git_push,
            parameters=[
                self.string_param(
                    "remote",
                    "Remote name",
                    required=False,
                    default="origin",
                ),
                self.string_param(
                    "branch",
                    "Branch to push",
                    required=False,
                ),
                self.boolean_param(
                    "set_upstream",
                    "Set upstream (-u)",
                    required=False,
                    default=False,
                ),
                self.string_param(
                    "path",
                    "Repository path",
                    required=False,
                ),
            ],
            requires_confirmation=True,
            permission_level="write",
        )

        # Git stash
        self.register_tool(
            name="git_stash",
            description="Stash or restore changes.",
            handler=self._git_stash,
            parameters=[
                self.string_param(
                    "action",
                    "Action: push, pop, list, apply, drop",
                    required=False,
                    default="push",
                    enum=["push", "pop", "list", "apply", "drop"],
                ),
                self.string_param(
                    "message",
                    "Stash message (for push)",
                    required=False,
                ),
                self.integer_param(
                    "index",
                    "Stash index (for apply/drop)",
                    required=False,
                    default=0,
                ),
                self.string_param(
                    "path",
                    "Repository path",
                    required=False,
                ),
            ],
            permission_level="write",
        )

        # Git reset
        self.register_tool(
            name="git_reset",
            description="Reset current HEAD to a state.",
            handler=self._git_reset,
            parameters=[
                self.string_param(
                    "target",
                    "Commit to reset to (default: HEAD)",
                    required=False,
                    default="HEAD",
                ),
                self.string_param(
                    "mode",
                    "Reset mode: soft, mixed, hard",
                    required=False,
                    default="mixed",
                    enum=["soft", "mixed", "hard"],
                ),
                self.string_param(
                    "path",
                    "Repository path",
                    required=False,
                ),
            ],
            requires_confirmation=True,
            permission_level="write",
        )

        # Git clone
        self.register_tool(
            name="git_clone",
            description="Clone a repository.",
            handler=self._git_clone,
            parameters=[
                self.string_param(
                    "url",
                    "Repository URL to clone",
                ),
                self.string_param(
                    "directory",
                    "Target directory",
                    required=False,
                ),
                self.string_param(
                    "branch",
                    "Branch to clone",
                    required=False,
                ),
                self.boolean_param(
                    "shallow",
                    "Shallow clone (--depth 1)",
                    required=False,
                    default=False,
                ),
            ],
            requires_confirmation=True,
            permission_level="write",
        )

        # Git remote
        self.register_tool(
            name="git_remote",
            description="Manage remote repositories.",
            handler=self._git_remote,
            parameters=[
                self.string_param(
                    "action",
                    "Action: list, add, remove, show",
                    required=False,
                    default="list",
                    enum=["list", "add", "remove", "show"],
                ),
                self.string_param(
                    "name",
                    "Remote name",
                    required=False,
                ),
                self.string_param(
                    "url",
                    "Remote URL (for add)",
                    required=False,
                ),
                self.string_param(
                    "path",
                    "Repository path",
                    required=False,
                ),
            ],
            permission_level="write",
        )

        # Git init
        self.register_tool(
            name="git_init",
            description="Initialize a new Git repository.",
            handler=self._git_init,
            parameters=[
                self.string_param(
                    "path",
                    "Directory to initialize",
                    required=False,
                ),
                self.string_param(
                    "initial_branch",
                    "Initial branch name",
                    required=False,
                    default="main",
                ),
            ],
            permission_level="write",
        )

    async def _run_git(
        self,
        args: list[str],
        repo_path: str | None = None,
    ) -> tuple[int, str, str]:
        """Run a git command and return (returncode, stdout, stderr)."""
        cmd = ["git"] + args

        cwd = repo_path or self.default_repo

        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
        )

        return result.returncode, result.stdout, result.stderr

    def _get_repo_path(self, path: str | None) -> str:
        """Get repository path, expanding ~ and resolving."""
        if path:
            return str(Path(path).expanduser().resolve())
        return self.default_repo

    async def _git_status(self, path: str | None = None) -> ToolResult:
        """Get repository status."""
        try:
            repo_path = self._get_repo_path(path)

            # Check if it's a git repo
            code, _, _ = await self._run_git(["rev-parse", "--git-dir"], repo_path)
            if code != 0:
                return ToolResult.error_result(f"Not a git repository: {repo_path}")

            # Get branch name
            code, branch, _ = await self._run_git(
                ["rev-parse", "--abbrev-ref", "HEAD"],
                repo_path
            )
            branch = branch.strip() if code == 0 else "unknown"

            # Get status
            code, status_output, _ = await self._run_git(
                ["status", "--porcelain"],
                repo_path
            )

            staged = []
            modified = []
            untracked = []

            for line in status_output.strip().split("\n"):
                if not line:
                    continue
                status = line[:2]
                filename = line[3:]

                if status[0] in "MADRCU":
                    staged.append(filename)
                if status[1] in "MADU":
                    modified.append(filename)
                if status == "??":
                    untracked.append(filename)

            # Get ahead/behind
            code, tracking, _ = await self._run_git(
                ["rev-list", "--left-right", "--count", f"{branch}...origin/{branch}"],
                repo_path
            )
            ahead, behind = 0, 0
            if code == 0 and tracking.strip():
                parts = tracking.strip().split()
                if len(parts) == 2:
                    ahead, behind = int(parts[0]), int(parts[1])

            is_clean = not staged and not modified and not untracked

            # Format output
            lines = [
                f"Git Status: {repo_path}",
                "",
                f"Branch: {branch}",
            ]

            if ahead or behind:
                lines.append(f"Ahead: {ahead}, Behind: {behind}")

            if is_clean:
                lines.append("\nWorking tree clean")
            else:
                if staged:
                    lines.append(f"\nStaged ({len(staged)}):")
                    for f in staged[:10]:
                        lines.append(f"  + {f}")
                    if len(staged) > 10:
                        lines.append(f"  ... and {len(staged) - 10} more")

                if modified:
                    lines.append(f"\nModified ({len(modified)}):")
                    for f in modified[:10]:
                        lines.append(f"  M {f}")
                    if len(modified) > 10:
                        lines.append(f"  ... and {len(modified) - 10} more")

                if untracked:
                    lines.append(f"\nUntracked ({len(untracked)}):")
                    for f in untracked[:10]:
                        lines.append(f"  ? {f}")
                    if len(untracked) > 10:
                        lines.append(f"  ... and {len(untracked) - 10} more")

            return ToolResult.success_result(
                "\n".join(lines),
                branch=branch,
                is_clean=is_clean,
                staged=staged,
                modified=modified,
                untracked=untracked,
                ahead=ahead,
                behind=behind,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting status: {e}")

    async def _git_log(
        self,
        count: int = 10,
        branch: str | None = None,
        oneline: bool = True,
        path: str | None = None,
    ) -> ToolResult:
        """Show commit log."""
        try:
            repo_path = self._get_repo_path(path)

            args = ["log", f"-{count}"]

            if oneline:
                args.append("--oneline")
            else:
                args.append("--format=medium")

            if branch:
                args.append(branch)

            code, output, stderr = await self._run_git(args, repo_path)

            if code != 0:
                return ToolResult.error_result(f"Git log failed: {stderr}")

            return ToolResult.success_result(
                f"Commit History:\n\n{output}",
                commits=output.strip().split("\n") if output.strip() else [],
            )

        except Exception as e:
            return ToolResult.error_result(f"Error getting log: {e}")

    async def _git_diff(
        self,
        staged: bool = False,
        file: str | None = None,
        commit: str | None = None,
        path: str | None = None,
    ) -> ToolResult:
        """Show diff."""
        try:
            repo_path = self._get_repo_path(path)

            args = ["diff"]

            if staged:
                args.append("--staged")

            if commit:
                args.append(commit)

            if file:
                args.extend(["--", file])

            code, output, stderr = await self._run_git(args, repo_path)

            if code != 0:
                return ToolResult.error_result(f"Git diff failed: {stderr}")

            if not output.strip():
                return ToolResult.success_result("No changes to show")

            # Truncate if too long
            if len(output) > 10000:
                output = output[:10000] + "\n... (truncated)"

            return ToolResult.success_result(output)

        except Exception as e:
            return ToolResult.error_result(f"Error getting diff: {e}")

    async def _git_add(
        self,
        files: list[str],
        path: str | None = None,
    ) -> ToolResult:
        """Stage files."""
        try:
            repo_path = self._get_repo_path(path)

            args = ["add"] + files

            code, output, stderr = await self._run_git(args, repo_path)

            if code != 0:
                return ToolResult.error_result(f"Git add failed: {stderr}")

            return ToolResult.success_result(
                f"Staged {len(files)} file(s): {', '.join(files[:5])}" +
                (f" and {len(files) - 5} more" if len(files) > 5 else ""),
                files=files,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error staging files: {e}")

    async def _git_commit(
        self,
        message: str,
        all: bool = False,
        path: str | None = None,
    ) -> ToolResult:
        """Commit changes."""
        try:
            repo_path = self._get_repo_path(path)

            args = ["commit", "-m", message]
            if all:
                args.insert(1, "-a")

            code, output, stderr = await self._run_git(args, repo_path)

            if code != 0:
                if "nothing to commit" in stderr.lower() or "nothing to commit" in output.lower():
                    return ToolResult.success_result("Nothing to commit, working tree clean")
                return ToolResult.error_result(f"Git commit failed: {stderr}")

            # Get commit hash
            code2, hash_output, _ = await self._run_git(
                ["rev-parse", "--short", "HEAD"],
                repo_path
            )
            commit_hash = hash_output.strip() if code2 == 0 else "unknown"

            return ToolResult.success_result(
                f"Committed: {commit_hash} - {message}",
                commit_hash=commit_hash,
                message=message,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error committing: {e}")

    async def _git_branch(
        self,
        action: str = "list",
        name: str | None = None,
        new_name: str | None = None,
        path: str | None = None,
    ) -> ToolResult:
        """Branch operations."""
        try:
            repo_path = self._get_repo_path(path)

            if action == "list":
                code, output, stderr = await self._run_git(["branch", "-a"], repo_path)
                if code != 0:
                    return ToolResult.error_result(f"Failed to list branches: {stderr}")
                return ToolResult.success_result(f"Branches:\n\n{output}")

            elif action == "create":
                if not name:
                    return ToolResult.error_result("Branch name required")
                code, output, stderr = await self._run_git(["branch", name], repo_path)
                if code != 0:
                    return ToolResult.error_result(f"Failed to create branch: {stderr}")
                return ToolResult.success_result(f"Created branch: {name}")

            elif action == "delete":
                if not name:
                    return ToolResult.error_result("Branch name required")
                code, output, stderr = await self._run_git(["branch", "-d", name], repo_path)
                if code != 0:
                    return ToolResult.error_result(f"Failed to delete branch: {stderr}")
                return ToolResult.success_result(f"Deleted branch: {name}")

            elif action == "rename":
                if not name or not new_name:
                    return ToolResult.error_result("Both current and new branch names required")
                code, output, stderr = await self._run_git(
                    ["branch", "-m", name, new_name],
                    repo_path
                )
                if code != 0:
                    return ToolResult.error_result(f"Failed to rename branch: {stderr}")
                return ToolResult.success_result(f"Renamed branch: {name} -> {new_name}")

            else:
                return ToolResult.error_result(f"Unknown action: {action}")

        except Exception as e:
            return ToolResult.error_result(f"Error with branch operation: {e}")

    async def _git_checkout(
        self,
        target: str,
        create: bool = False,
        path: str | None = None,
    ) -> ToolResult:
        """Checkout branch or file."""
        try:
            repo_path = self._get_repo_path(path)

            args = ["checkout"]
            if create:
                args.append("-b")
            args.append(target)

            code, output, stderr = await self._run_git(args, repo_path)

            if code != 0:
                return ToolResult.error_result(f"Checkout failed: {stderr}")

            action = "Created and switched to" if create else "Switched to"
            return ToolResult.success_result(f"{action}: {target}")

        except Exception as e:
            return ToolResult.error_result(f"Error with checkout: {e}")

    async def _git_pull(
        self,
        remote: str = "origin",
        branch: str | None = None,
        path: str | None = None,
    ) -> ToolResult:
        """Pull from remote."""
        try:
            repo_path = self._get_repo_path(path)

            args = ["pull", remote]
            if branch:
                args.append(branch)

            code, output, stderr = await self._run_git(args, repo_path)

            if code != 0:
                return ToolResult.error_result(f"Pull failed: {stderr}")

            return ToolResult.success_result(f"Pull completed:\n\n{output}")

        except Exception as e:
            return ToolResult.error_result(f"Error pulling: {e}")

    async def _git_push(
        self,
        remote: str = "origin",
        branch: str | None = None,
        set_upstream: bool = False,
        path: str | None = None,
    ) -> ToolResult:
        """Push to remote."""
        try:
            repo_path = self._get_repo_path(path)

            args = ["push"]
            if set_upstream:
                args.append("-u")
            args.append(remote)
            if branch:
                args.append(branch)

            code, output, stderr = await self._run_git(args, repo_path)

            if code != 0:
                return ToolResult.error_result(f"Push failed: {stderr}")

            return ToolResult.success_result(
                f"Push completed" + (f":\n\n{output}" if output.strip() else "")
            )

        except Exception as e:
            return ToolResult.error_result(f"Error pushing: {e}")

    async def _git_stash(
        self,
        action: str = "push",
        message: str | None = None,
        index: int = 0,
        path: str | None = None,
    ) -> ToolResult:
        """Stash operations."""
        try:
            repo_path = self._get_repo_path(path)

            if action == "push":
                args = ["stash", "push"]
                if message:
                    args.extend(["-m", message])
            elif action == "pop":
                args = ["stash", "pop"]
            elif action == "list":
                args = ["stash", "list"]
            elif action == "apply":
                args = ["stash", "apply", f"stash@{{{index}}}"]
            elif action == "drop":
                args = ["stash", "drop", f"stash@{{{index}}}"]
            else:
                return ToolResult.error_result(f"Unknown action: {action}")

            code, output, stderr = await self._run_git(args, repo_path)

            if code != 0:
                return ToolResult.error_result(f"Stash {action} failed: {stderr}")

            if action == "list":
                if not output.strip():
                    return ToolResult.success_result("No stashes")
                return ToolResult.success_result(f"Stash list:\n\n{output}")

            return ToolResult.success_result(f"Stash {action} completed")

        except Exception as e:
            return ToolResult.error_result(f"Error with stash: {e}")

    async def _git_reset(
        self,
        target: str = "HEAD",
        mode: str = "mixed",
        path: str | None = None,
    ) -> ToolResult:
        """Reset HEAD."""
        try:
            repo_path = self._get_repo_path(path)

            args = ["reset", f"--{mode}", target]

            code, output, stderr = await self._run_git(args, repo_path)

            if code != 0:
                return ToolResult.error_result(f"Reset failed: {stderr}")

            return ToolResult.success_result(f"Reset to {target} ({mode})")

        except Exception as e:
            return ToolResult.error_result(f"Error with reset: {e}")

    async def _git_clone(
        self,
        url: str,
        directory: str | None = None,
        branch: str | None = None,
        shallow: bool = False,
    ) -> ToolResult:
        """Clone repository."""
        try:
            args = ["clone"]

            if shallow:
                args.extend(["--depth", "1"])

            if branch:
                args.extend(["-b", branch])

            args.append(url)

            if directory:
                args.append(directory)

            code, output, stderr = await self._run_git(args, os.getcwd())

            if code != 0:
                return ToolResult.error_result(f"Clone failed: {stderr}")

            return ToolResult.success_result(
                f"Cloned {url}" + (f" to {directory}" if directory else ""),
                url=url,
                directory=directory,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error cloning: {e}")

    async def _git_remote(
        self,
        action: str = "list",
        name: str | None = None,
        url: str | None = None,
        path: str | None = None,
    ) -> ToolResult:
        """Remote operations."""
        try:
            repo_path = self._get_repo_path(path)

            if action == "list":
                code, output, stderr = await self._run_git(["remote", "-v"], repo_path)
                if code != 0:
                    return ToolResult.error_result(f"Failed to list remotes: {stderr}")
                if not output.strip():
                    return ToolResult.success_result("No remotes configured")
                return ToolResult.success_result(f"Remotes:\n\n{output}")

            elif action == "add":
                if not name or not url:
                    return ToolResult.error_result("Remote name and URL required")
                code, output, stderr = await self._run_git(
                    ["remote", "add", name, url],
                    repo_path
                )
                if code != 0:
                    return ToolResult.error_result(f"Failed to add remote: {stderr}")
                return ToolResult.success_result(f"Added remote: {name} -> {url}")

            elif action == "remove":
                if not name:
                    return ToolResult.error_result("Remote name required")
                code, output, stderr = await self._run_git(
                    ["remote", "remove", name],
                    repo_path
                )
                if code != 0:
                    return ToolResult.error_result(f"Failed to remove remote: {stderr}")
                return ToolResult.success_result(f"Removed remote: {name}")

            elif action == "show":
                if not name:
                    return ToolResult.error_result("Remote name required")
                code, output, stderr = await self._run_git(
                    ["remote", "show", name],
                    repo_path
                )
                if code != 0:
                    return ToolResult.error_result(f"Failed to show remote: {stderr}")
                return ToolResult.success_result(output)

            else:
                return ToolResult.error_result(f"Unknown action: {action}")

        except Exception as e:
            return ToolResult.error_result(f"Error with remote: {e}")

    async def _git_init(
        self,
        path: str | None = None,
        initial_branch: str = "main",
    ) -> ToolResult:
        """Initialize repository."""
        try:
            repo_path = self._get_repo_path(path)

            # Create directory if needed
            Path(repo_path).mkdir(parents=True, exist_ok=True)

            args = ["init", "-b", initial_branch]

            code, output, stderr = await self._run_git(args, repo_path)

            if code != 0:
                return ToolResult.error_result(f"Init failed: {stderr}")

            return ToolResult.success_result(
                f"Initialized Git repository in {repo_path}",
                path=repo_path,
                branch=initial_branch,
            )

        except Exception as e:
            return ToolResult.error_result(f"Error initializing: {e}")
