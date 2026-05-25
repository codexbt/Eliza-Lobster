"""interfaces/messaging.py
Unified Messaging Interface for Kairos multi-platform bots.

Provides:
- Command parsing (/goal, /status, /kairos, etc.)
- send_message(platform, chat_id, text, parse_mode=...)
- Abstract base for platform handlers (so core stays untouched)
- Simple registry so bot_orchestrator can register real handlers (Telegram, Discord, WhatsApp)

Security: only messages from allowed_users are processed (checked in orchestrator).
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger("interfaces.messaging")


@dataclass
class Message:
    platform: str          # "telegram", "discord", "whatsapp"
    chat_id: str
    user_id: str
    text: str
    raw: Any = None        # original update object


@dataclass
class BotCommand:
    name: str
    args: str = ""
    raw_text: str = ""


class PlatformHandler(ABC):
    """Abstract handler every platform must implement."""

    name: str = "base"

    @abstractmethod
    async def send_message(self, chat_id: str, text: str, parse_mode: Optional[str] = None, **kwargs) -> bool:
        """Send text (optionally with markdown/code blocks). Return True on success."""
        raise NotImplementedError

    @abstractmethod
    async def start_listening(self, on_message: Callable[[Message], Any]) -> None:
        """Start polling / listening. Must call on_message(msg) for every incoming allowed message."""
        raise NotImplementedError

    async def stop(self) -> None:
        """Optional graceful stop."""
        pass


class MessagingInterface:
    """
    Unified entry point.
    Bot orchestrator registers real PlatformHandler instances here.
    Then uses send_message() and starts listening.
    """

    def __init__(self):
        self.handlers: dict[str, PlatformHandler] = {}
        self.command_handlers: dict[str, Callable[[Message, list[str]], Any]] = {}

    def register_handler(self, platform: str, handler: PlatformHandler):
        self.handlers[platform] = handler
        logger.info(f"Registered handler for platform: {platform}")

    def register_command(self, cmd: str, func: Callable[[Message, list[str]], Any]):
        """Register a command handler, e.g. register_command("goal", handle_goal)"""
        self.command_handlers[cmd] = func

    async def send_message(self, platform: str, chat_id: str, text: str, parse_mode: Optional[str] = "markdown", **kwargs) -> bool:
        """Single unified send function used by orchestrator and agents."""
        handler = self.handlers.get(platform)
        if not handler:
            logger.error(f"No handler registered for platform: {platform}")
            return False
        try:
            return await handler.send_message(chat_id, text, parse_mode=parse_mode, **kwargs)
        except Exception as e:
            logger.exception(f"send_message failed on {platform}: {e}")
            return False

    async def start_all_listeners(self, on_message: Callable[[Message], Any]):
        """Start listening on all registered platforms (non-blocking via tasks in orchestrator)."""
        for plat, h in self.handlers.items():
            logger.info(f"Starting listener for {plat}...")
            # Each handler runs its own polling loop
            # The on_message callback will be called from inside the handler
            # We just start them; orchestrator manages the tasks
            try:
                # In real impl the handler's start_listening runs forever
                # so orchestrator should run them as asyncio.create_task
                await h.start_listening(on_message)
            except Exception as e:
                logger.error(f"Listener for {plat} failed to start: {e}")

    # ---------- Command Parsing (used by orchestrator) ----------
    CMD_REGEX = re.compile(r"^/(goal|status|stop|kairos|help|swarm|claw)\s*(.*)$", re.IGNORECASE)

    @staticmethod
    def parse_command(text: str) -> Optional[BotCommand]:
        """Parse incoming text into command + args."""
        text = text.strip()
        m = MessagingInterface.CMD_REGEX.match(text)
        if not m:
            return None
        name = m.group(1).lower()
        args = m.group(2).strip()
        return BotCommand(name=name, args=args, raw_text=text)

    def handle_command(self, msg: Message, cmd: BotCommand) -> Optional[str]:
        """Dispatch to registered command handler if any. Returns response text or None."""
        func = self.command_handlers.get(cmd.name)
        if func:
            try:
                result = func(msg, cmd.args.split() if cmd.args else [])
                return str(result) if result is not None else None
            except Exception as e:
                logger.error(f"Command {cmd.name} failed: {e}")
                return f"Error handling /{cmd.name}: {e}"
        return None


# ---------- Helper for formatting responses (rich text) ----------
def format_response(text: str, code_lang: Optional[str] = None) -> str:
    """Return platform-friendly markdown. Telegram & Discord both understand ``` and **."""
    if code_lang and "```" not in text:
        return f"```{code_lang}\n{text}\n```"
    return text


# Simple in-memory registry for quick use
messaging = MessagingInterface()
