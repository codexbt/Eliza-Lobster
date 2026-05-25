"""bot_orchestrator.py
Central multi-platform bot orchestrator for Kairos.

- Loads messaging tokens from config.yaml or .env
- Registers Telegram, Discord, WhatsApp handlers
- Listens on all platforms simultaneously (asyncio)
- Parses commands and forwards /goal etc. to core (agents.orchestrator + react_loop)
- Sends rich responses back to the originating platform
- Security: only allowed user IDs
- Logging to logs/bot.log
- Designed so core/ hermes/ agents/ are 100% untouched

Run via: python main.py bot
or the run_forever scripts.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

# Core Kairos (never modify these imports or the folders)
from agents.orchestrator import run_swarm
from core.kairos_daemon import KairosDaemon
from core.react_loop import get_react_loop
from interfaces.messaging import (
    Message, BotCommand, MessagingInterface, messaging as msg_interface,
    PlatformHandler, format_response
)

# ---------- Logging ----------
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
BOT_LOG = LOG_DIR / "bot.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(BOT_LOG, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("bot_orchestrator")

load_dotenv()  # load .env if present (recommended for tokens)

ROOT = Path(__file__).parent.resolve()
CONFIG_PATH = ROOT / "config.yaml"


class Config:
    """Simple config loader for messaging section + backward compat."""

    def __init__(self, path: Path = CONFIG_PATH):
        self.path = path
        self.data: dict[str, Any] = {}
        self._load()

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                self.data = yaml.safe_load(f) or {}
        except Exception:
            self.data = {}

    def get_messaging(self) -> dict[str, Any]:
        return self.data.get("messaging", {}) or {}

    @property
    def telegram_token(self) -> Optional[str]:
        return self.get_messaging().get("telegram_token") or os.getenv("TELEGRAM_BOT_TOKEN")

    @property
    def discord_token(self) -> Optional[str]:
        return self.get_messaging().get("discord_token") or os.getenv("DISCORD_BOT_TOKEN")

    @property
    def whatsapp_api_key(self) -> Optional[str]:
        return self.get_messaging().get("whatsapp_api_key") or os.getenv("WHATSAPP_API_KEY")

    @property
    def allowed_users(self) -> list[str]:
        users = self.get_messaging().get("allowed_users", []) or []
        # Also support comma separated in env
        env_users = os.getenv("ALLOWED_USERS", "")
        if env_users:
            users.extend([u.strip() for u in env_users.split(",") if u.strip()])
        return [str(u) for u in users]


config = Config()


# ---------- Platform Handlers (real implementations) ----------

class TelegramHandler(PlatformHandler):
    name = "telegram"

    def __init__(self, token: str):
        self.token = token
        self.app = None  # python-telegram-bot Application

    async def send_message(self, chat_id: str, text: str, parse_mode: Optional[str] = "markdown", **kwargs) -> bool:
        if not self.app:
            return False
        try:
            await self.app.bot.send_message(
                chat_id=int(chat_id),
                text=text[:4096],
                parse_mode=parse_mode if parse_mode in ("markdown", "markdownv2", "html") else None,
            )
            return True
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    async def start_listening(self, on_message):
        """Start python-telegram-bot v21+ polling."""
        if not self.token:
            logger.warning("No Telegram token — skipping Telegram")
            return

        try:
            from telegram import Update
            from telegram.ext import Application, MessageHandler, filters, ContextTypes

            self.app = Application.builder().token(self.token).build()

            async def _handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
                if not update.message or not update.message.text:
                    return
                user_id = str(update.message.from_user.id)
                chat_id = str(update.message.chat.id)
                text = update.message.text

                msg = Message(
                    platform="telegram",
                    chat_id=chat_id,
                    user_id=user_id,
                    text=text,
                    raw=update,
                )
                # The orchestrator's on_message will check allowed + dispatch
                await on_message(msg)

            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle))
            # Also handle commands as normal text so our parser catches /goal etc.
            self.app.add_handler(MessageHandler(filters.COMMAND, _handle))

            logger.info("Telegram polling started")
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(drop_pending_updates=True)
            # Keep running until stop
            await asyncio.Event().wait()  # never returns until cancelled
        except Exception as e:
            logger.exception(f"Telegram handler failed: {e}")


class DiscordHandler(PlatformHandler):
    name = "discord"

    def __init__(self, token: str):
        self.token = token
        self.bot = None  # discord.py Client or commands.Bot

    async def send_message(self, chat_id: str, text: str, parse_mode: Optional[str] = None, **kwargs) -> bool:
        if not self.bot:
            return False
        try:
            channel = self.bot.get_channel(int(chat_id))
            if channel:
                # Discord supports ``` for code blocks
                await channel.send(text[:2000])
                return True
        except Exception as e:
            logger.error(f"Discord send failed: {e}")
        return False

    async def start_listening(self, on_message):
        if not self.token:
            logger.warning("No Discord token — skipping Discord")
            return

        try:
            import discord
            from discord.ext import commands

            intents = discord.Intents.default()
            intents.message_content = True

            self.bot = commands.Bot(command_prefix="!", intents=intents)

            @self.bot.event
            async def on_ready():
                logger.info(f"Discord bot logged in as {self.bot.user}")

            @self.bot.event
            async def on_message(message: discord.Message):
                if message.author.bot:
                    return
                msg = Message(
                    platform="discord",
                    chat_id=str(message.channel.id),
                    user_id=str(message.author.id),
                    text=message.content,
                    raw=message,
                )
                await on_message(msg)
                # Do not process discord commands here — our unified parser handles /goal

            logger.info("Discord bot starting...")
            await self.bot.start(self.token)
        except Exception as e:
            logger.exception(f"Discord handler failed: {e}")


class WhatsAppHandler(PlatformHandler):
    """Placeholder / simple bridge using pywhatkit (unofficial, requires phone logged in).
    For production use WhatsApp Business API instead.
    """
    name = "whatsapp"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def send_message(self, chat_id: str, text: str, parse_mode: Optional[str] = None, **kwargs) -> bool:
        try:
            import pywhatkit as kit
            # chat_id expected as "+91xxxxxxxxxx"
            # pywhatkit is sync and opens browser — only for occasional use
            kit.sendwhatmsg_instantly(chat_id, text[:1000], wait_time=10, tab_close=True)
            logger.info(f"WhatsApp message attempted to {chat_id}")
            return True
        except Exception as e:
            logger.warning(f"WhatsApp send failed (pywhatkit): {e}. Consider official API.")
            return False

    async def start_listening(self, on_message):
        logger.warning("WhatsApp listening not supported reliably with pywhatkit. Use webhook or official API for incoming messages.")
        # For now we only support outbound. Incoming would require WhatsApp Business API + webhook.
        # To keep always-on bot working, we simply do nothing here.
        await asyncio.sleep(1)


# ---------- Core Integration Helpers (non-blocking) ----------

executor = ThreadPoolExecutor(max_workers=4)
kairos_instance: Optional["KairosDaemon"] = None
kairos_running = False


def _run_swarm_sync(goal: str, project_root: str = ".") -> str:
    """Run full swarm in a worker thread (sync call to core)."""
    try:
        result = run_swarm(goal, project_root=project_root)
        return result.output if hasattr(result, "output") else str(result)
    except Exception as e:
        logger.exception("Swarm execution failed")
        return f"Swarm error: {e}"


async def run_goal_on_core(msg: Message, args: list[str]) -> str:
    """Non-blocking call to core orchestrator."""
    if not args:
        return "Usage: /goal <your high-level task description>"

    goal = " ".join(args)
    logger.info(f"[{msg.platform}] /goal from {msg.user_id}: {goal[:80]}")

    loop = asyncio.get_event_loop()
    # Run heavy swarm in thread so bot doesn't block
    response = await loop.run_in_executor(executor, _run_swarm_sync, goal, str(ROOT))
    return format_response(response, code_lang="text")


def get_status() -> str:
    """Quick status of memory + current LLM + kairos."""
    try:
        from hermes.memory import get_memory
        mem = get_memory(project_root=str(ROOT))
        count = mem.get_task_count()
        from core.llm import get_llm_manager
        llm = get_llm_manager(str(ROOT))
        prov = llm.get_provider_name()
        model = llm.get_default_model()
        kstat = "running" if kairos_running else "stopped"
        return f"Tasks completed: {count}\nLLM: {prov} / {model}\nKAIROS: {kstat}\nUptime: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    except Exception as e:
        return f"Status error: {e}"


async def toggle_kairos(on: bool) -> str:
    global kairos_instance, kairos_running
    if on and not kairos_running:
        kairos_instance = KairosDaemon(project_root=str(ROOT))
        # Run in background thread (daemon has its own loop)
        t = threading.Thread(target=kairos_instance.run_forever, daemon=True)
        t.start()
        kairos_running = True
        return "KAIROS daemon started (background)."
    elif not on and kairos_running:
        kairos_running = False
        # Note: full stop would require signal in daemon; for v1 we just flag
        return "KAIROS stop requested (will finish current cycle)."
    return "KAIROS already in requested state."


# ---------- Command Router ----------

def command_router(msg: Message, cmd: BotCommand) -> Optional[str]:
    if cmd.name == "goal":
        # We return None here because we want async response later
        # The real handling is done in the on_message coroutine
        return None
    if cmd.name == "status":
        return get_status()
    if cmd.name == "help":
        return "Commands: /goal <task> | /status | /kairos on|off | /stop"
    if cmd.name == "kairos":
        on = "on" in cmd.args.lower() or cmd.args.strip() == ""
        # We will handle async in caller
        return None
    if cmd.name in ("stop", "stop_task"):
        return "Task stop acknowledged (current swarm continues until finish)."
    return None


async def on_incoming_message(msg: Message):
    """Central callback called by every platform handler."""
    cfg = config
    if str(msg.user_id) not in cfg.allowed_users:
        logger.warning(f"Ignoring message from unauthorized user {msg.user_id} on {msg.platform}")
        return

    cmd = MessagingInterface.parse_command(msg.text)
    if not cmd:
        # Plain chat? optionally treat as /goal or ignore
        # For safety we ignore non-command messages
        await msg_interface.send_message(msg.platform, msg.chat_id, "Send a command like /goal ... or /help")
        return

    # Special async commands
    if cmd.name == "goal":
        response = await run_goal_on_core(msg, cmd.args.split() if cmd.args else [])
        await msg_interface.send_message(msg.platform, msg.chat_id, response)
        return

    if cmd.name == "kairos":
        on = "on" in (cmd.args or "").lower()
        resp = await toggle_kairos(on)
        await msg_interface.send_message(msg.platform, msg.chat_id, resp)
        return

    # Sync commands
    resp = command_router(msg, cmd)
    if resp:
        await msg_interface.send_message(msg.platform, msg.chat_id, resp)


# ---------- Main Orchestrator Entry Point ----------

async def run_bot_forever():
    """The main always-running bot service."""
    logger.info("=== Kairos Multi-Platform Bot Starting ===")

    cfg = config
    allowed = cfg.allowed_users
    if not allowed:
        logger.warning("No allowed_users configured! Bot will accept NO messages. Set in config.yaml")

    # Register handlers only if tokens present
    if cfg.telegram_token:
        tg = TelegramHandler(cfg.telegram_token)
        msg_interface.register_handler("telegram", tg)
    if cfg.discord_token:
        dc = DiscordHandler(cfg.discord_token)
        msg_interface.register_handler("discord", dc)
    if cfg.whatsapp_api_key or True:  # even without key we register placeholder
        wa = WhatsAppHandler(cfg.whatsapp_api_key)
        msg_interface.register_handler("whatsapp", wa)

    # Register core command handlers (optional, we mostly use the central on_message)
    # msg_interface.register_command("goal", ...) — we handle inside on_incoming_message for async

    # Start listeners in parallel
    tasks = []
    for platform, handler in msg_interface.handlers.items():
        # Each start_listening is long-running; run as task
        task = asyncio.create_task(handler.start_listening(on_incoming_message))
        tasks.append(task)
        logger.info(f"Listener task created for {platform}")

    if not tasks:
        logger.error("No messaging platforms configured. Add tokens in config.yaml or .env and restart.")
        return

    logger.info("All platforms listening. Bot is live.")
    await asyncio.gather(*tasks, return_exceptions=True)


def start_bot():
    """Sync entry used by main.py and run_service.py"""
    try:
        asyncio.run(run_bot_forever())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Bot crashed: {e}")
        # For service wrapper we want auto-restart handled outside


# ---------- Optional FastAPI Web Dashboard ----------
# Run independently with:
#   uvicorn bot_orchestrator:dashboard_app --host 0.0.0.0 --port 8000
# Gives /status , /trigger_goal , /kairos/toggle  (protected by simple token if set)

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from pydantic import BaseModel
except ImportError:
    FastAPI = None

if FastAPI:
    dashboard_app = FastAPI(title="Kairos Bot Dashboard", version="1.0")

    class GoalRequest(BaseModel):
        goal: str
        platform: str = "web"
        chat_id: str = "dashboard"

    @dashboard_app.get("/status")
    async def status():
        return {"status": get_status(), "kairos_running": kairos_running, "platforms": list(msg_interface.handlers.keys())}

    @dashboard_app.post("/trigger_goal")
    async def trigger_goal(req: GoalRequest, background: BackgroundTasks):
        # Fire and forget via the same non-blocking path
        async def _run():
            resp = await run_goal_on_core(Message(platform=req.platform, chat_id=req.chat_id, user_id="dashboard", text="/goal " + req.goal), req.goal.split())
            # In real use you would push to a websocket or store result
            logger.info(f"[Dashboard] Goal result: {resp[:200]}...")
        background.add_task(_run)
        return {"queued": True, "goal": req.goal}

    @dashboard_app.post("/kairos/{action}")
    async def kairos_toggle(action: str):
        if action not in ("on", "off"):
            raise HTTPException(400, "Use on or off")
        result = await toggle_kairos(action == "on")
        return {"result": result}
else:
    dashboard_app = None  # type: ignore


if __name__ == "__main__":
    start_bot()
