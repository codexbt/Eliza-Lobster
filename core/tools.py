"""Kairos core/tools.py
Production-grade local tool harness inspired by Claw-Code.
All operations are:
- confined to project_root (path escape prevention)
- logged
- typed
- return structured results
- destructive actions require explicit approval
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

try:
    from git import Repo, GitCommandError
except ImportError:
    Repo = None
    GitCommandError = Exception

try:
    from rich.console import Console
    from rich.prompt import Confirm
except ImportError:
    Console = None
    Confirm = None

logger = logging.getLogger("claw.tools")


class ToolResult(dict):
    """Standardized result container for all tools."""

    def __init__(
        self,
        success: bool,
        output: str = "",
        error: str = "",
        metadata: Optional[dict[str, Any]] = None,
        **extra: Any,
    ):
        super().__init__(
            success=success,
            output=output,
            error=error,
            metadata=metadata or {},
            **extra,
        )


class ClawTools:
    """Main harness providing safe file, shell, git and search capabilities."""

    DANGEROUS_KEYWORDS = [
        "rm -rf",
        "rm -r",
        "del /f",
        "rd /s",
        "format ",
        "shutdown",
        "reboot",
        "git push --force",
        "git reset --hard",
        ":(){ :|:& };:",
        "mkfs",
        "dd if=",
        "curl | bash",
        "wget | bash",
    ]

    def __init__(
        self,
        project_root: str = ".",
        approval_callback: Optional[Callable[[str], bool]] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        self.root = Path(project_root).resolve()
        self.approval_callback = approval_callback
        self.config = config or {}
        self.console = Console() if Console else None
        self._setup_logging()
        logger.info(f"ClawTools initialized. Root: {self.root}")

    def _setup_logging(self) -> None:
        log_file = self.root / "hermes" / "hermes.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    # ---------------- PATH SAFETY ----------------
    def _safe_path(self, relative_path: str | Path) -> Path:
        p = (self.root / relative_path).resolve()
        if not p.is_relative_to(self.root):
            raise PermissionError(f"Path escapes project root: {relative_path}")
        return p

    # ---------------- APPROVAL ----------------
    def _request_approval(self, action: str, details: str = "") -> bool:
        prompt = f"⚠️  APPROVE {action}? {details[:200]}"
        if self.approval_callback:
            return self.approval_callback(prompt)
        if self.console and Confirm:
            return Confirm.ask(f"[bold red]{prompt}[/bold red]", default=False)
        resp = input(f"{prompt} [y/N]: ").strip().lower()
        return resp in {"y", "yes"}

    def _is_destructive(self, command: str) -> bool:
        cmd_lower = command.lower()
        return any(kw in cmd_lower for kw in self.DANGEROUS_KEYWORDS)

    # ---------------- FILE TOOLS ----------------
    def read_file(
        self, path: str, offset: int = 0, limit: int = 200
    ) -> ToolResult:
        try:
            p = self._safe_path(path)
            if not p.exists():
                return ToolResult(False, error=f"File not found: {path}")
            with open(p, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            total = len(lines)
            end = min(offset + limit, total) if limit > 0 else total
            content = "".join(lines[offset:end])
            return ToolResult(
                True,
                output=content,
                metadata={
                    "path": str(p),
                    "offset": offset,
                    "limit": limit,
                    "total_lines": total,
                    "truncated": end < total,
                },
            )
        except Exception as e:
            logger.exception("read_file failed")
            return ToolResult(False, error=str(e))

    def write_file(
        self, path: str, content: str, create_backup: bool = True
    ) -> ToolResult:
        try:
            p = self._safe_path(path)
            if p.exists() and create_backup:
                backup = p.with_suffix(p.suffix + f".bak-{int(time.time())}")
                shutil.copy2(p, backup)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"write_file: {p} ({len(content)} bytes)")
            return ToolResult(True, output=f"Wrote {len(content)} bytes to {path}")
        except Exception as e:
            logger.exception("write_file failed")
            return ToolResult(False, error=str(e))

    def edit_file(
        self, path: str, search: str, replace: str, replace_all: bool = False
    ) -> ToolResult:
        try:
            p = self._safe_path(path)
            if not p.exists():
                return ToolResult(False, error="File does not exist")
            original = p.read_text(encoding="utf-8")
            if search not in original:
                return ToolResult(False, error="Search string not found")
            if replace_all:
                new_content = original.replace(search, replace)
            else:
                new_content = original.replace(search, replace, 1)
            p.write_text(new_content, encoding="utf-8")
            logger.info(f"edit_file successful on {p}")
            return ToolResult(
                True, output="Edit applied", metadata={"replacements": new_content.count(replace)}
            )
        except Exception as e:
            logger.exception("edit_file failed")
            return ToolResult(False, error=str(e))

    def delete_file(self, path: str) -> ToolResult:
        try:
            p = self._safe_path(path)
            if not p.exists():
                return ToolResult(False, error="File not found")
            if not self._request_approval("DELETE FILE", str(p)):
                return ToolResult(False, error="User denied deletion")
            p.unlink()
            logger.warning(f"delete_file: removed {p}")
            return ToolResult(True, output=f"Deleted {path}")
        except Exception as e:
            return ToolResult(False, error=str(e))

    def list_dir(self, path: str = ".", recursive: bool = False) -> ToolResult:
        try:
            p = self._safe_path(path)
            if recursive:
                entries = [str(f.relative_to(self.root)) for f in p.rglob("*")]
            else:
                entries = [str(f.relative_to(self.root)) for f in p.iterdir()]
            return ToolResult(True, output="\n".join(sorted(entries)), metadata={"count": len(entries)})
        except Exception as e:
            return ToolResult(False, error=str(e))

    def grep(
        self, pattern: str, path: str = ".", glob: str = "**/*", max_results: int = 50
    ) -> ToolResult:
        try:
            p = self._safe_path(path)
            import re
            regex = re.compile(pattern)
            matches: list[dict] = []
            for file in p.glob(glob):
                if not file.is_file():
                    continue
                try:
                    for i, line in enumerate(file.open(encoding="utf-8", errors="ignore"), 1):
                        if regex.search(line):
                            matches.append({"file": str(file.relative_to(self.root)), "line": i, "text": line.rstrip()})
                            if len(matches) >= max_results:
                                break
                except Exception:
                    pass
                if len(matches) >= max_results:
                    break
            return ToolResult(True, metadata={"matches": matches, "count": len(matches)})
        except Exception as e:
            return ToolResult(False, error=str(e))

    # ---------------- SHELL ----------------
    def run_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 120,
        env: Optional[dict[str, str]] = None,
    ) -> ToolResult:
        try:
            workdir = self._safe_path(cwd or ".")
            if self._is_destructive(command):
                if not self._request_approval("RUN DESTRUCTIVE COMMAND", command):
                    return ToolResult(False, error="Approval denied for destructive command")

            start = time.time()
            use_shell = platform.system() == "Windows"
            completed = subprocess.run(
                command,
                cwd=str(workdir),
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, **(env or {})},
            )
            duration = round(time.time() - start, 2)
            output = (completed.stdout or "") + (completed.stderr or "")
            success = completed.returncode == 0
            logger.info(f"run_command exit={completed.returncode} ({duration}s): {command[:80]}")
            return ToolResult(
                success,
                output=output[-8000:],  # truncate huge output
                metadata={
                    "returncode": completed.returncode,
                    "duration": duration,
                    "cwd": str(workdir),
                    "truncated": len(output) > 8000,
                },
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, error=f"Command timed out after {timeout}s")
        except Exception as e:
            logger.exception("run_command failed")
            return ToolResult(False, error=str(e))

    # ---------------- GIT ----------------
    def git_status(self, repo_path: str = ".") -> ToolResult:
        try:
            if Repo is None:
                return ToolResult(False, error="GitPython not installed")
            repo = Repo(self._safe_path(repo_path))
            return ToolResult(
                True,
                output=repo.git.status(),
                metadata={"branch": repo.active_branch.name if not repo.head.is_detached else "DETACHED"},
            )
        except Exception as e:
            return ToolResult(False, error=str(e))

    def git_diff(self, repo_path: str = ".", staged: bool = False) -> ToolResult:
        try:
            if Repo is None:
                return ToolResult(False, error="GitPython not installed")
            repo = Repo(self._safe_path(repo_path))
            diff = repo.git.diff("--cached" if staged else "")
            return ToolResult(True, output=diff or "No changes")
        except Exception as e:
            return ToolResult(False, error=str(e))

    def git_commit(
        self, message: str, add_all: bool = True, repo_path: str = "."
    ) -> ToolResult:
        try:
            if Repo is None:
                return ToolResult(False, error="GitPython not installed")
            repo = Repo(self._safe_path(repo_path))
            if add_all:
                repo.git.add(A=True)
            commit = repo.index.commit(message)
            return ToolResult(True, output=f"Committed {commit.hexsha[:8]}: {message}")
        except Exception as e:
            return ToolResult(False, error=str(e))

    def git_push(self, repo_path: str = ".", remote: str = "origin", branch: Optional[str] = None) -> ToolResult:
        try:
            if Repo is None:
                return ToolResult(False, error="GitPython not installed")
            repo = Repo(self._safe_path(repo_path))
            if not self._request_approval("GIT PUSH", f"{remote} {branch or repo.active_branch}"):
                return ToolResult(False, error="Push denied by user")
            push_info = repo.remote(remote).push(branch or repo.active_branch)
            return ToolResult(True, output=str(push_info))
        except Exception as e:
            return ToolResult(False, error=str(e))

    def git_log(self, repo_path: str = ".", max_count: int = 10) -> ToolResult:
        try:
            if Repo is None:
                return ToolResult(False, error="GitPython not installed")
            repo = Repo(self._safe_path(repo_path))
            log = repo.git.log(f"-{max_count}", "--oneline")
            return ToolResult(True, output=log)
        except Exception as e:
            return ToolResult(False, error=str(e))

    # ---------------- WEB SEARCH (local, no key) ----------------
    def web_search(self, query: str, max_results: int = 8) -> ToolResult:
        if DDGS is None:
            return ToolResult(False, error="duckduckgo-search not installed")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            formatted = [
                {"title": r.get("title"), "href": r.get("href"), "body": r.get("body", "")[:300]}
                for r in results
            ]
            return ToolResult(True, metadata={"results": formatted, "count": len(formatted)})
        except Exception as e:
            return ToolResult(False, error=str(e))

    # ---------------- UTILITIES ----------------
    def get_available_tools(self) -> list[dict[str, Any]]:
        """Return machine-readable tool specs for LLM ReAct / function calling."""
        return [
            {"name": "read_file", "description": "Read file contents with offset/limit", "params": ["path", "offset", "limit"]},
            {"name": "write_file", "description": "Write or overwrite file (creates backup)", "params": ["path", "content"]},
            {"name": "edit_file", "description": "Precise string replace edit", "params": ["path", "search", "replace", "replace_all"]},
            {"name": "delete_file", "description": "Delete file (requires approval)", "params": ["path"]},
            {"name": "list_dir", "description": "List directory contents", "params": ["path", "recursive"]},
            {"name": "grep", "description": "Search code for regex pattern", "params": ["pattern", "path", "glob"]},
            {"name": "run_command", "description": "Execute shell command (destructive requires approval)", "params": ["command", "cwd", "timeout"]},
            {"name": "git_status", "description": "Current git status", "params": ["repo_path"]},
            {"name": "git_diff", "description": "Show git diff", "params": ["repo_path", "staged"]},
            {"name": "git_commit", "description": "Commit changes", "params": ["message", "add_all"]},
            {"name": "git_push", "description": "Push to remote (requires approval)", "params": ["repo_path", "remote"]},
            {"name": "web_search", "description": "Privacy-friendly web search via DuckDuckGo", "params": ["query", "max_results"]},
        ]

    def health_check(self) -> ToolResult:
        return ToolResult(
            True,
            metadata={
                "root": str(self.root),
                "git_available": Repo is not None,
                "web_search_available": DDGS is not None,
                "rich_available": Console is not None,
                "platform": platform.system(),
            },
        )

    # ---------------- CLAW-CODE STYLE FILE CONTEXT ----------------
    def extract_file_context(self, text: str, max_files: int = 8, max_chars_per_file: int = 4000) -> str:
        """Extract @path references from text and return their contents (Claw Code style)."""
        import re
        paths = re.findall(r'@([^\s\'"`]+)', text)
        if not paths:
            return ""

        context_parts = []
        seen = set()
        for raw_path in paths[:max_files]:
            try:
                p = self._safe_path(raw_path)
                if p in seen or not p.exists() or not p.is_file():
                    continue
                seen.add(p)
                content = p.read_text(encoding="utf-8", errors="replace")
                if len(content) > max_chars_per_file:
                    content = content[:max_chars_per_file] + "\n... [truncated]"
                context_parts.append(f"=== FILE: {raw_path} ===\n{content}\n")
            except Exception:
                pass
        return "\n".join(context_parts)


# Convenience factory used by other modules
def get_tools(
    project_root: str = ".",
    approval_callback: Optional[Callable[[str], bool]] = None,
    config: Optional[dict] = None,
) -> ClawTools:
    return ClawTools(project_root, approval_callback, config)
