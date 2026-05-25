"""core/kairos_daemon.py
KAIROS - Autonomous background swarm daemon.
Every N minutes it wakes up, scans the repo for issues, and proposes/fixes small problems
using the full Kairos stack (ReAct + multi-agent swarm when needed).
All actions respect the safety approval system by default.

Run with:
  python -m core.kairos_daemon
  python -m core.kairos_daemon --once
  python run_kairos.bat

Can be left running 24/7 on a local machine.
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

from core.react_loop import ReactLoop, get_react_loop
from core.tools import get_tools
from hermes.memory import get_memory

logger = logging.getLogger("core.kairos")


class KairosDaemon:
    def __init__(self, config_path: str = "config.yaml", project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.config_path = self.project_root / config_path
        self.config = self._load_config()
        self.tools = get_tools(str(self.project_root))
        self.memory = get_memory(config=self.config, project_root=str(self.project_root))
        self.react = get_react_loop(
            tools=self.tools,
            memory=self.memory,
            project_root=str(self.project_root),
            max_iterations=8,
        )
        self.running = True
        self._setup_signal_handlers()
        logger.info("KAIROS daemon initialized")

    def _load_config(self) -> dict:
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _setup_signal_handlers(self):
        def handler(signum, frame):
            logger.info("KAIROS received shutdown signal")
            self.running = False
        signal.signal(signal.SIGINT, handler)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, handler)

    def scan_for_issues(self) -> list[str]:
        """Lightweight issue detection. Returns list of actionable mini-goals."""
        issues: list[str] = []

        # 1. Git dirty state older than 1 day?
        status = self.tools.git_status()
        if status.get("success") and "modified" in status.get("output", "").lower():
            issues.append("Review and commit or clean the current uncommitted changes")

        # 2. Any TODO/FIXME/HACK in core or agents?
        grep = self.tools.grep(r"(TODO|FIXME|HACK|BUG):", path=".", glob="*.py", max_results=5)
        if grep.get("success") and grep.get("metadata", {}).get("count", 0) > 0:
            issues.append("Address high-priority TODO/FIXME comments found in the codebase")

        # 3. Recent test failures?
        test_run = self.tools.run_command("python -m pytest --tb=no -q 2>&1 | tail -5", timeout=60)
        if "failed" in (test_run.get("output") or "").lower():
            issues.append("Investigate and fix the failing tests reported by pytest")

        # 4. Syntax or import errors in recently changed files (basic)
        syntax = self.tools.run_command(
            'python -c "import ast, pathlib; [ast.parse(p.read_text(encoding=\'utf-8\')) for p in pathlib.Path(\'. \').rglob(\'*.py\')]; print(\'syntax ok\')"',
            timeout=25,
        )
        if "syntax" not in (syntax.get("output") or "").lower():
            issues.append("Fix Python syntax or import errors preventing the project from loading cleanly")

        # Dedup + limit
        return list(dict.fromkeys(issues))[: self.config.get("kairos", {}).get("max_proactive_fixes", 3)]

    def process_issue(self, issue: str) -> dict:
        """Use the ReAct engine for small autonomous fixes (fast path)."""
        logger.info(f"KAIROS processing issue: {issue}")
        result = self.react.run(goal=f"[KAIROS AUTONOMOUS] {issue}")
        # Also store a task record
        self.memory.store_task(
            type("T", (), {
                "goal": issue,
                "success": result.get("success", False),
                "result_summary": result.get("final_answer", "")[:400],
                "duration": 0,
                "agent": "kairos",
                "metadata": {"iterations": result.get("iterations")},
            })()
        )
        return result

    def run_once(self) -> None:
        """Single scan + fix cycle. Safe to call from cron or manually."""
        logger.info("KAIROS waking up for scan...")
        issues = self.scan_for_issues()
        if not issues:
            logger.info("KAIROS: No actionable issues found. Sleeping.")
            return

        logger.info(f"KAIROS found {len(issues)} issues")
        for issue in issues:
            if not self.running:
                break
            res = self.process_issue(issue)
            logger.info(f"KAIROS result for '{issue}': success={res.get('success')}")

        # Update soul with autonomous activity
        soul = self.project_root / "hermes" / "soul.md"
        with open(soul, "a", encoding="utf-8") as f:
            f.write(f"\n\n## {datetime.now().isoformat()} (KAIROS)\nAutonomous scan completed. Issues addressed: {len(issues)}\n")

    def run_forever(self) -> None:
        interval = self.config.get("kairos", {}).get("scan_interval_minutes", 15) * 60
        logger.info(f"KAIROS entering autonomous loop (every {interval//60} minutes)")
        while self.running:
            try:
                self.run_once()
            except Exception as e:
                logger.exception(f"KAIROS cycle error: {e}")
            if self.running:
                time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Kairos Autonomous Daemon")
    parser.add_argument("--once", action="store_true", help="Run one scan cycle and exit")
    parser.add_argument("--root", default=".", help="Project root")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [KAIROS] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("hermes/hermes.log", encoding="utf-8"),
        ],
    )

    daemon = KairosDaemon(project_root=args.root)
    if args.once:
        daemon.run_once()
    else:
        daemon.run_forever()


if __name__ == "__main__":
    main()
