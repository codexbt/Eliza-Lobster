"""main.py
Kairos - Unified CLI entry point.
Usage examples:
  python main.py --help
  python main.py swarm "..."
  python main.py claw "..."
  python main.py llm                 # interactive model/provider selector + auto-fetch
  python main.py llm --list
  python main.py status
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from core.llm import get_llm_manager, KNOWN_PROVIDERS

# Make sure we can import local packages
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from agents.orchestrator import run_swarm
from core.kairos_daemon import KairosDaemon
from core.react_loop import ReactLoop, get_react_loop, make_llm_call
from core.tools import get_tools
from hermes.memory import get_memory
from core.llm import get_llm_manager

console = Console()


def banner():
    console.print(
        Panel.fit(
            "[bold cyan]Kairos[/bold cyan]  •  [bold magenta]Kairos-Hermes Swarm[/bold magenta]\n"
            "Local-first • Self-hosted • Autonomous Multi-Agent Coding System",
            border_style="bright_blue",
        )
    )


def cmd_swarm(args):
    banner()
    goal = " ".join(args.goal) if isinstance(args.goal, list) else args.goal
    console.print(f"[bold]Launching swarm for:[/bold] {goal}\n")
    result = run_swarm(goal, project_root=str(ROOT))
    console.print(Panel(result.output, title="Swarm Result", border_style="green" if result.success else "red"))
    if result.artifacts:
        console.print("Artifacts:", result.artifacts)


def cmd_claw(args):
    banner()
    goal = " ".join(args.goal)
    console.print(f"[bold]Claw ReAct single-agent mode:[/bold] {goal}")
    llm = make_llm_call() if args.use_llm else None
    loop = get_react_loop(project_root=str(ROOT))
    out = loop.run(goal)
    console.print(Panel(out["final_answer"], title=f"ReAct finished in {out['iterations']} steps"))
    console.print("Artifacts:", out.get("artifacts", []))


def cmd_kairos(args):
    banner()
    daemon = KairosDaemon(project_root=str(ROOT))
    if args.once:
        console.print("[yellow]Running single KAIROS scan...[/yellow]")
        daemon.run_once()
    else:
        console.print("[bold red]Starting KAIROS autonomous daemon (Ctrl+C to stop)[/bold red]")
        daemon.run_forever()


def cmd_status(_):
    mem = get_memory(project_root=str(ROOT))
    tools = get_tools(str(ROOT))
    count = mem.get_task_count()
    console.print(Panel(f"Tasks completed: {count}\nSelf-improve trigger: {mem.should_trigger_self_improve()}", title="Hermes Memory"))
    console.print("Project health:", tools.health_check().get("metadata"))


def cmd_llm(args):
    """Interactive + CLI for switching between Ollama and remote providers with API keys + auto model fetch."""
    banner()
    manager = get_llm_manager(str(ROOT))
    current_prov = manager.get_provider_name()
    current_model = manager.get_default_model()
    console.print(Panel(f"[bold cyan]Current:[/bold cyan] {current_prov}  ->  [bold magenta]{current_model}[/bold magenta]", title="LLM Configuration"))

    if args.providers:
        table = Table(title="Supported LLM Providers (use with --set or interactive)")
        table.add_column("Name", style="cyan bold")
        table.add_column("Description", style="dim")
        table.add_column("Key via", style="green")
        for name, meta in KNOWN_PROVIDERS.items():
            table.add_row(name, meta["description"], meta.get("env") or "none (local)")
        console.print(table)
        console.print("\n[dim]Tip: python main.py llm   (interactive wizard)[/dim]")
        return

    if args.list or args.fetch:
        prov = current_prov
        key = args.key or manager.get_api_key(prov)
        if not key and prov != "ollama":
            key = Prompt.ask(f"Enter {prov} API key to fetch models", password=True, default="")
        console.print(f"[yellow]Fetching models for {prov}...[/yellow]")
        models = manager.list_models(provider=prov, api_key=key or None)
        if not models:
            console.print("[red]No models returned (is Ollama running? Key valid?)[/red]")
            return
        table = Table(title=f"Models available via {prov} (showing first 60)")
        table.add_column("#", justify="right", style="yellow")
        table.add_column("Model", style="green")
        for idx, m in enumerate(models[:60], 1):
            table.add_row(str(idx), m)
        console.print(table)

        if Confirm.ask("Select and set one as your new default model?"):
            sel = Prompt.ask("Enter number or paste full model name", default="1")
            try:
                if sel.isdigit():
                    i = int(sel) - 1
                    selected = models[i] if i < len(models) else models[0]
                else:
                    selected = sel.strip()
            except Exception:
                selected = models[0]
            save_key = None
            if key and Confirm.ask(f"Also save the API key inside config.yaml for {prov}? [red](never commit this file)[/red]", default=False):
                save_key = key
            if manager.set_active_model(prov, selected, save_key):
                console.print(Panel(f"[green]✓ Updated![/green]  Provider: [cyan]{prov}[/cyan]   Model: [magenta]{selected}[/magenta]", title="Model Selection Complete"))
            else:
                console.print("[red]Failed to persist to config.yaml[/red]")
        return

    if args.set:
        p, m = args.set
        if manager.set_active_model(p, m):
            console.print(f"[green]Default changed to[/green] {p} / {m}")
        return

    # Interactive full wizard (the "model selection" experience user asked for)
    console.print("\n[bold]Interactive Model + Provider Setup[/bold]")
    prov_list = list(KNOWN_PROVIDERS.keys())
    for i, p in enumerate(prov_list, 1):
        console.print(f"  [cyan]{i}[/cyan]. {p} — {KNOWN_PROVIDERS[p]['description']}")
    sel = Prompt.ask("Choose provider (number or name)", default="1")
    if sel.isdigit():
        idx = int(sel) - 1
        provider = prov_list[idx] if 0 <= idx < len(prov_list) else "ollama"
    else:
        provider = sel.lower().strip()
        if provider not in KNOWN_PROVIDERS:
            provider = "ollama"

    key = None
    requires_key = KNOWN_PROVIDERS[provider].get("requires_key", False)
    if requires_key:
        existing = manager.get_api_key(provider)
        if existing:
            console.print(f"[dim]Using existing key from env/config for {provider}[/dim]")
            key = existing
        else:
            key = Prompt.ask(f"Enter your {provider} API key", password=True)

    console.print(f"[yellow]Auto-fetching models for {provider}... (this may take a few seconds)[/yellow]")
    models = manager.list_models(provider=provider, api_key=key)
    selected = None
    if models:
        console.print(f"\n[bold]Found {len(models)} models. First 25 shown:[/bold]")
        for i, m in enumerate(models[:25], 1):
            console.print(f"  [green]{i}[/green]. {m}")
        sel2 = Prompt.ask("Pick number or type exact model name", default="1")
        if sel2.isdigit():
            ii = int(sel2) - 1
            selected = models[ii] if ii < len(models) else models[0]
        else:
            selected = sel2
    else:
        selected = Prompt.ask("No auto-fetch result. Enter model name manually (e.g. gpt-4o or qwen2.5-coder:14b)")

    save_key = key if key and requires_key and Confirm.ask("Save this key into config.yaml? (recommended only for local use)", default=False) else None
    if manager.set_active_model(provider, selected, save_key):
        console.print(Panel.fit(f"[bold green]Model selection complete![/bold green]\n\nProvider: [cyan]{provider}[/cyan]\nDefault model: [magenta]{selected}[/magenta]\n\nRun your commands — it will now use the new model automatically.", title="✅ Ready", border_style="green"))
    else:
        console.print("[red]Could not save selection[/red]")


def cmd_bot(_args):
    """Launch the always-running multi-platform bot (Telegram + Discord + WhatsApp)."""
    banner()
    console.print(Panel(
        "[bold green]Starting Kairos Bot Orchestrator[/bold green]\n\n"
        "Listening on all configured platforms.\n"
        "Use /goal in chat • /status • /kairos on/off • /help\n\n"
        "Logs: logs/bot.log\n"
        "Press Ctrl+C to stop.",
        title="Multi-Platform Bot",
        border_style="bright_blue"
    ))
    try:
        # Lazy import so normal CLI stays light
        from bot_orchestrator import start_bot
        start_bot()
    except Exception as e:
        console.print_exception()
        console.print("[red]Bot crashed. See logs/bot.log[/red]")


def cmd_doctor(_args):
    """Claw Code style system health check."""
    banner()
    console.print("[bold cyan]Running Kairos Doctor...[/bold cyan]\n")

    checks = []

    # 1. Tools health
    tools = get_tools(str(ROOT))
    tool_health = tools.health_check()
    checks.append(("Tools", tool_health.get("success", False), tool_health.get("metadata", {})))

    # 2. Memory
    try:
        mem = get_memory(project_root=str(ROOT))
        count = mem.get_task_count() if hasattr(mem, 'get_task_count') else "N/A"
        checks.append(("Memory", True, {"tasks": count}))
    except Exception as e:
        checks.append(("Memory", False, {"error": str(e)}))

    # 3. LLM
    try:
        llm = get_llm_manager(str(ROOT))
        prov = llm.get_provider_name()
        model = llm.get_default_model()
        checks.append(("LLM", True, {"provider": prov, "model": model}))
    except Exception as e:
        checks.append(("LLM", False, {"error": str(e)}))

    # 4. Dashboard API (simple port check)
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', 8001))
        s.close()
        checks.append(("Dashboard (8001)", result == 0, {}))
    except:
        checks.append(("Dashboard (8001)", False, {}))

    # Print results
    for name, ok, meta in checks:
        status = "[green]✓ OK[/green]" if ok else "[red]✗ FAIL[/red]"
        console.print(f"{status}  {name}")
        if meta:
            console.print(f"      {meta}")

    console.print("\n[bold]Doctor complete.[/bold]")


def main():
    parser = argparse.ArgumentParser(description="Kairos - Kairos-Hermes Swarm")
    sub = parser.add_subparsers(dest="command")

    # swarm
    p_swarm = sub.add_parser("swarm", help="Run the full multi-agent swarm on a goal")
    p_swarm.add_argument("goal", nargs="+", help="The high-level coding goal")
    p_swarm.set_defaults(func=cmd_swarm)

    # claw (direct ReAct)
    p_claw = sub.add_parser("claw", help="Single-agent powerful ReAct loop (fast for small tasks)")
    p_claw.add_argument("goal", nargs="+")
    p_claw.add_argument("--use-llm", action="store_true", help="Enable direct LLM calls (uses currently selected provider/model)")
    p_claw.set_defaults(func=cmd_claw)

    # kairos
    p_kairos = sub.add_parser("kairos", help="Autonomous background daemon")
    p_kairos.add_argument("--once", action="store_true", help="Run one scan cycle then exit")
    p_kairos.set_defaults(func=cmd_kairos)

    # status
    p_status = sub.add_parser("status", help="Show memory + system health")
    p_status.set_defaults(func=cmd_status)

    # NEW: multi-provider LLM + model selection (Ollama + remote APIs with auto-fetch)
    p_llm = sub.add_parser("llm", help="Manage LLM providers & models (Ollama + OpenAI/Groq/xAI/etc with API keys)")
    p_llm.add_argument("--list", action="store_true", help="List models for current provider (auto-fetch)")
    p_llm.add_argument("--fetch", action="store_true", help="Same as --list + prompt to select")
    p_llm.add_argument("--providers", action="store_true", help="Show all supported providers")
    p_llm.add_argument("--set", nargs=2, metavar=("PROVIDER", "MODEL"), help="Directly set e.g. --set groq llama-3.1-70b")
    p_llm.add_argument("--key", help="Provide API key for this invocation (for --list/--fetch)")
    p_llm.set_defaults(func=cmd_llm)

    # NEW: multi-platform bot (Telegram + Discord + WhatsApp) + 24/7 service
    p_bot = sub.add_parser("bot", help="Run the always-on bot orchestrator (multi-platform chat control)")
    p_bot.set_defaults(func=cmd_bot)

    # NEW: doctor command (inspired by Claw Code)
    p_doctor = sub.add_parser("doctor", help="Run system health check (like claw doctor)")
    p_doctor.set_defaults(func=cmd_doctor)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    try:
        args.func(args)
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by user[/red]")
    except Exception as e:
        console.print_exception()


if __name__ == "__main__":
    main()
