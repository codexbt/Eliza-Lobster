"""core/react_loop.py
Custom ReAct reasoning + tool-calling engine.
Supports Ollama + any remote OpenAI-compatible provider (via API key).
Auto model fetching and selection handled by core/llm.py
Used by KAIROS and main CLI.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Callable, Optional

from core.llm import get_llm_manager
from core.tools import ClawTools, get_tools
from hermes.memory import HermesMemory, get_memory

logger = logging.getLogger("core.react")


class ReactLoop:
    """Production ReAct engine with tool use, memory, safety, and iteration limits."""

    DEFAULT_SYSTEM = """You are Kairos, an autonomous local coding agent inside the Kairos swarm.
You have access to powerful local tools.
Always follow this exact format for every response:

Thought: <your reasoning>
Action: <tool_name or FINISH>
Action Input: <JSON object with exact parameters for the tool, or empty object for FINISH>
Observation: <will be filled by system - do not write this yourself>

When the task is complete, output:
Thought: <final summary>
Action: FINISH
Action Input: {"answer": "<clear concise final answer or 'Task completed successfully'>"}

Available tools (use exact names):
{tools}

Rules:
- Never guess file contents. Always use read_file or grep first.
- Every destructive action will require explicit user approval via the tool layer.
- Stay inside the project root at all times.
- Think step by step. Be concise.
"""

    def __init__(
        self,
        tools: Optional[ClawTools] = None,
        memory: Optional[HermesMemory] = None,
        model: Optional[str] = None,
        project_root: str = ".",
        max_iterations: int = 12,
    ):
        self.tools = tools or get_tools(project_root)
        self.memory = memory or get_memory(project_root=project_root)
        self.model = model
        self.max_iterations = max_iterations
        self.project_root = project_root
        self.history: list[dict] = []
        self.llm_manager = get_llm_manager(project_root=project_root)

    def _get_model(self) -> str:
        if self.model:
            return self.model
        return self.llm_manager.get_default_model()

    def _format_tools(self) -> str:
        tool_list = self.tools.get_available_tools()
        lines = []
        for t in tool_list:
            params = ", ".join(t.get("params", []))
            lines.append(f"- {t['name']}({params}): {t['description']}")
        return "\n".join(lines)

    def _call_llm(self, messages: list[dict]) -> str:
        model = self._get_model()
        try:
            return self.llm_manager.chat(
                messages=messages,
                model=model,
                temperature=0.5,
                max_tokens=8192,
            )
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"ERROR: {e}"

    def _parse_action(self, text: str) -> tuple[str, dict]:
        """Robust parser for Thought / Action / Action Input blocks."""
        action_match = re.search(r"Action:\s*([A-Za-z0-9_]+)", text, re.IGNORECASE)
        if not action_match:
            return "FINISH", {"answer": "No action found - terminating"}

        action = action_match.group(1).strip()

        input_match = re.search(r"Action Input:\s*(\{.*?\})", text, re.DOTALL | re.IGNORECASE)
        if input_match:
            try:
                args = json.loads(input_match.group(1))
            except json.JSONDecodeError:
                args = {"raw": input_match.group(1)[:500]}
        else:
            args = {}

        return action, args

    def run(self, goal: str, extra_context: str = "") -> dict:
        """Execute the full ReAct loop until FINISH or max iterations."""
        logger.info(f"ReAct starting for goal: {goal[:100]}")
        system = self.DEFAULT_SYSTEM.format(tools=self._format_tools())
        memory_context = self.memory.get_relevant_context(goal, max_items=4)

        # Claw Code style: auto-inject @path file context
        file_context = self.tools.extract_file_context(goal) if hasattr(self.tools, 'extract_file_context') else ""
        combined_context = (extra_context + "\n" + file_context).strip()

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"GOAL: {goal}\n\nRELEVANT MEMORY:\n{memory_context}\n\nEXTRA CONTEXT:\n{combined_context}\n\nBegin."},
        ]

        final_answer = "Task did not complete within iteration limit."
        artifacts: list[str] = []

        for i in range(1, self.max_iterations + 1):
            logger.info(f"ReAct iteration {i}/{self.max_iterations}")
            raw = self._call_llm(messages)
            self.history.append({"role": "assistant", "content": raw})

            action, args = self._parse_action(raw)
            logger.info(f"  -> {action} {args}")

            if action.upper() == "FINISH":
                final_answer = args.get("answer", raw[-300:])
                break

            # Execute tool
            tool_method = getattr(self.tools, action, None)
            if not callable(tool_method):
                obs = f"ERROR: Unknown tool '{action}'. Available: {[t['name'] for t in self.tools.get_available_tools()]}"
            else:
                try:
                    result = tool_method(**{k: v for k, v in args.items() if v is not None})
                    obs = str(result)
                    if isinstance(result, dict) and result.get("success") and "path" in str(result):
                        artifacts.append(result.get("path", ""))
                except Exception as e:
                    obs = f"TOOL ERROR: {e}"

            self.history.append({"role": "user", "content": f"Observation: {obs}"})

            # Feed back
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": f"Observation: {obs[:2000]}"})

            # Safety: stop if we are looping too much on same action
            if i > 3 and action in [h.get("content", "") for h in self.history[-4:]]:
                break

        # Store the entire trace
        self.memory.store_conversation(
            turns=self.history,
            summary=f"ReAct trace for: {goal[:80]}",
            tokens=len(str(self.history)),
        )

        return {
            "success": "FINISH" in str(final_answer).upper() or "completed" in final_answer.lower(),
            "final_answer": final_answer,
            "iterations": i,
            "artifacts": list(set(artifacts)),
            "history": self.history[-6:],  # last few for debugging
        }


def get_react_loop(**kwargs) -> ReactLoop:
    return ReactLoop(**kwargs)


# Simple LLM callable for agents that want direct (non-ReAct) LLM access
# Now supports any configured provider (Ollama or remote with API key)
def make_llm_call(model: Optional[str] = None) -> Callable[[str, str], str]:
    manager = get_llm_manager()
    def _call(system: str, user: str) -> str:
        msgs = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        try:
            return manager.chat(msgs, model=model, temperature=0.6)
        except Exception as e:
            return f"[LLM ERROR] {e}"
    return _call
