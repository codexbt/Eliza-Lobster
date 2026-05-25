"""core/dashboard_events.py
Global event broadcaster for real-time 3D dashboard updates.

Allows any part of Kairos (orchestrator, agents, kairos) to emit events
that get WebSocket-broadcasted to all connected 3D dashboards in real-time.

Usage:
    from core.dashboard_events import emit_agent_update, emit_log_update, get_broadcaster
    
    emit_agent_update("Coder", "working", "Writing feature X", progress=45)
    emit_log_update("✓ Test passed", level="success")
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable, List, Any, Dict

logger = logging.getLogger("dashboard_events")


class DashboardEventBroadcaster:
    """Central event hub for real-time dashboard updates."""

    def __init__(self):
        self.listeners: List[Callable[[Dict[str, Any]], Any]] = []
        self.enabled = False
        self.log_buffer: List[str] = []

    def register_listener(self, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """Register a callback to receive all dashboard events (e.g., WebSocket broadcast)."""
        self.listeners.append(callback)
        logger.debug(f"Registered dashboard listener: {callback.__name__}")

    def enable(self) -> None:
        """Enable event broadcasting (called when dashboard_api starts)."""
        self.enabled = True
        logger.info("Dashboard event broadcasting ENABLED")

    def disable(self) -> None:
        """Disable broadcasting (e.g., API shutdown)."""
        self.enabled = False
        logger.info("Dashboard event broadcasting DISABLED")

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Internal: emit event to all registered listeners."""
        if not self.enabled:
            return

        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            **payload
        }

        for listener in self.listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    # For async listeners
                    asyncio.create_task(listener(event))
                else:
                    listener(event)
            except Exception as e:
                logger.error(f"Error in dashboard listener: {e}", exc_info=True)

    def agent_status_update(
        self,
        agent_name: str,
        status: str,  # idle, thinking, working, completed, error
        current_task: str = "",
        progress: float = 0.0,
        color: Optional[str] = None,
    ) -> None:
        """Emit agent status update (used by orchestrator during swarm execution)."""
        default_colors = {
            "Orchestrator": "#00f0ff",
            "Architect": "#a855f7",
            "Coder": "#22c55e",
            "Tester": "#eab308",
            "Scribe": "#f472b6",
        }
        color = color or default_colors.get(agent_name, "#ffffff")

        self._emit("agent_update", {
            "agent": {
                "name": agent_name,
                "status": status,
                "current_task": current_task,
                "progress": progress,
                "color": color,
            }
        })

    def log_update(self, message: str, level: str = "info", agent: Optional[str] = None) -> None:
        """Emit log/activity update for the live terminal feed in 3D."""
        self._emit("log_update", {
            "message": message,
            "level": level,  # info, success, warning, error
            "agent": agent
        })

    def metrics_update(
        self,
        tasks_completed: Optional[int] = None,
        skills_created: Optional[int] = None,
        token_usage: Optional[int] = None,
        kairos_status: Optional[str] = None,
    ) -> None:
        """Emit metrics update (stats rings in 3D)."""
        payload = {}
        if tasks_completed is not None:
            payload["tasks_completed"] = tasks_completed
        if skills_created is not None:
            payload["skills_created"] = skills_created
        if token_usage is not None:
            payload["token_usage"] = token_usage
        if kairos_status is not None:
            payload["kairos_status"] = kairos_status

        if payload:
            self._emit("metrics_update", payload)

    def particle_effect(self, agent_name: str, effect_type: str = "activity") -> None:
        """Trigger particle effect on 3D agent (e.g., "code_particles", "check_mark")."""
        self._emit("particle_effect", {
            "agent": agent_name,
            "effect": effect_type  # code, check, error, sparkle, etc.
        })


# Global singleton
_broadcaster = DashboardEventBroadcaster()


def get_broadcaster() -> DashboardEventBroadcaster:
    """Get the global event broadcaster."""
    return _broadcaster


# Convenience functions for use throughout codebase
def emit_agent_update(
    agent_name: str,
    status: str,
    current_task: str = "",
    progress: float = 0.0,
    color: Optional[str] = None,
) -> None:
    """Update agent status on 3D dashboard."""
    _broadcaster.agent_status_update(agent_name, status, current_task, progress, color)


def emit_log(message: str, level: str = "info", agent: Optional[str] = None) -> None:
    """Emit log message to live terminal in 3D."""
    _broadcaster.log_update(message, level, agent)


def emit_metrics(
    tasks_completed: Optional[int] = None,
    skills_created: Optional[int] = None,
    token_usage: Optional[int] = None,
    kairos_status: Optional[str] = None,
) -> None:
    """Update metrics/stats on 3D dashboard."""
    _broadcaster.metrics_update(tasks_completed, skills_created, token_usage, kairos_status)


def emit_particles(agent_name: str, effect_type: str = "activity") -> None:
    """Trigger particle effect on 3D dashboard."""
    _broadcaster.particle_effect(agent_name, effect_type)
