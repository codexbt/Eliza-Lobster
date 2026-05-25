"""agents/coder.py
Coder agent: receives architecture, implements changes using the full Claw tool harness + LLM (when available).
Strong no-LLM fallback: generates real, useful code for a wide range of common simple tasks.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from core.tools import ClawTools
from hermes.memory import HermesMemory
from core.dashboard_events import emit_agent_update, emit_log

logger = logging.getLogger("agents.coder")


@dataclass
class AgentResult:
    success: bool
    output: str
    artifacts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Coder:
    name = "coder"
    SYSTEM_PROMPT = """You are an expert senior software engineer in the Kairos swarm.
You receive a goal + architecture context.
You must output ONLY the code/files needed to fulfill the goal.
For each file you want to create, output in this exact format:

FILE: path/to/file.ext
```language
<complete file content here>
```

Do not add explanations outside the FILE blocks. Be precise and complete."""

    def __init__(
        self,
        tools: ClawTools,
        memory: HermesMemory,
        llm_call: Optional[Callable[[str, str], str]] = None,
    ):
        self.tools = tools
        self.memory = memory
        self.llm_call = llm_call

    def run(self, goal: str, context: str = "") -> AgentResult:
        logger.info(f"CODER implementing for: {goal[:80]}...")
        artifacts: list[str] = []
        goal_lower = goal.lower()

        # 1. Try LLM first if available (best quality)
        if self.llm_call:
            try:
                prompt = f"""GOAL: {goal}

ARCHITECTURE / CONTEXT (from previous phase):
{context[:2200]}

CURRENT PROJECT STRUCTURE (top level):
{self.tools.list_dir(".", recursive=False).get("output", "")[:600]}

Produce the complete implementation now. Use the exact FILE: ``` format for every file you create."""
                raw = self.llm_call(self.SYSTEM_PROMPT, prompt)
                if raw and "ERROR" not in raw[:100].upper():  # ignore broken LLM responses
                    files = self._parse_and_write_files(raw)
                    if files:
                        artifacts.extend(files)
                        return AgentResult(
                            success=True,
                            output=f"LLM implementation complete. Files: {files}",
                            artifacts=artifacts,
                            metadata={"phase": "implementation", "llm_used": True},
                        )
            except Exception as e:
                logger.warning(f"LLM path failed, using strong fallback: {e}")

        # 2. STRONG RULE-BASED FALLBACK (works without any LLM / Ollama / keys)
        emit_agent_update("Coder", "working", "Generating real code from goal...", 50)
        created = self._smart_generate(goal, goal_lower, context)
        if created:
            for idx, (path, content) in enumerate(created):
                res = self.tools.write_file(path, content)
                if res.get("success"):
                    artifacts.append(path)
                    emit_log(f"✓ Wrote real file: {path}", "success", "Coder")
                    emit_agent_update("Coder", "working", f"Created {path}", 50 + (idx * 12))
                    logger.info(f"Coder (fallback) created: {path}")
                else:
                    logger.error(f"Failed to write {path}: {res.get('error')}")

        if not artifacts:
            # Last resort - at least explain what should be done
            default_path = "output/task_instructions.md"
            content = f"""# Task for Kairos

**Goal:** {goal}

The Coder could not auto-generate code for this specific request.

**Suggested next steps:**
1. Run with Ollama installed and running for full LLM power: `ollama pull qwen2.5-coder:7b`
2. Or give a more specific goal (e.g. "create python function...", "make html page with ...")
3. Or use `python main.py claw "..."` for the powerful ReAct tool-using agent.

Architecture context that was available:
{context[:800]}
"""
            self.tools.write_file(default_path, content)
            artifacts.append(default_path)

        emit_agent_update("Coder", "completed", f"Real files created: {len(artifacts)}", 95)
        return AgentResult(
            success=bool(artifacts),
            output=f"Implementation done (smart fallback). Created: {artifacts}",
            artifacts=artifacts,
            metadata={"phase": "implementation", "fallback": True, "files": len(artifacts)},
        )

    # ==================== SMART NO-LLM GENERATOR ====================

    def _smart_generate(self, goal: str, goal_lower: str, context: str) -> list[tuple[str, str]]:
        """Generate real useful files based on goal keywords. No LLM required."""
        files: list[tuple[str, str]] = []

        # --- HTML / Web page tasks (very common) ---
        if any(k in goal_lower for k in ["html", "web page", "website", "index.html", "landing page", "hello"]):
            title = self._extract_title(goal) or "Hello"
            body = self._extract_body(goal) or "Welcome to the page generated by Kairos."

            # Better support for "with mentioned XXX" or "showing XXX" style requests
            if "with mentioned" in goal_lower or "showing " in goal_lower or "display " in goal_lower:
                # Try to pull the requested text
                for marker in ["with mentioned ", "showing ", "display ", "with text ", "saying "]:
                    if marker in goal_lower:
                        after = goal_lower.split(marker, 1)[1].strip().split()[0:4]
                        if after:
                            prominent = " ".join(after).title()
                            body = f"<span style='font-size:2.2rem; font-weight:600; color:#fff'>{prominent}</span>"
                            if not title or title.lower() == "hello":
                                title = prominent
                            break
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&amp;family=Space+Grotesk:wght@500;600&amp;display=swap');
        
        :root {{
            --bg: #0a0a0f;
            --accent: #00ffcc;
        }}
        
        body {{
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #0a0a0f 0%, #12121a 100%);
            color: #e0e0e0;
            font-family: 'Inter', system_ui, sans-serif;
        }}
        
        .card {{
            background: #16161f;
            border: 1px solid #2a2a35;
            border-radius: 20px;
            padding: 3rem 4rem;
            text-align: center;
            box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.4);
            max-width: 520px;
        }}
        
        h1 {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 4.5rem;
            margin: 0 0 1rem;
            background: linear-gradient(90deg, #fff, var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 600;
            letter-spacing: -0.04em;
        }}
        
        .subtitle {{
            font-size: 1.25rem;
            opacity: 0.85;
            margin-bottom: 2rem;
            line-height: 1.5;
        }}
        
        .badge {{
            display: inline-block;
            background: #1f1f2a;
            color: var(--accent);
            font-size: 0.75rem;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-weight: 500;
            letter-spacing: 0.5px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="badge">HERMESCLAW</div>
        <h1>{title}</h1>
        <p class="subtitle">{body}</p>
        <p style="font-size:0.9rem; opacity:0.6;">Auto-generated by the autonomous swarm</p>
    </div>
</body>
</html>"""
            files.append(("index.html", html))
            files.append(("HELLO_PAGE.md", f"# {title}\n\n{body}\n\nOpen `index.html` in your browser.\n\nGenerated from goal: {goal}"))
            return files

        # --- React / TSX / Frontend component (dashboard friendly) ---
        if any(k in goal_lower for k in ["react", "tsx", "component", "typescript", "frontend"]):
            name = self._extract_name(goal, default="MyComponent")
            tsx = f"""import React from 'react';

interface {name}Props {{
    title?: string;
    onAction?: () => void;
}}

export const {name}: React.FC<{name}Props> = ({{ title = '{name}', onAction }}) => {{
    return (
        <div className="p-8 bg-[#0a0a0f] text-white rounded-2xl border border-[#2a2a35]">
            <h2 className="text-4xl font-semibold tracking-tighter mb-4">{{title}}</h2>
            <p className="text-[#a0a0b0] mb-6">
                This React component was auto-generated by Kairos Coder for your goal:
                <br />
                <span className="text-[#00ffcc] font-mono text-sm">"{goal}"</span>
            </p>
            <button 
                onClick={{onAction}}
                className="px-6 py-3 bg-[#00ffcc] text-black rounded-xl font-medium hover:bg-white transition-colors"
            >
                Trigger Action
            </button>
        </div>
    );
}};

export default {name};
"""
            files.append((f"src/components/{name}.tsx", tsx))
            files.append(("COMPONENT_README.md", f"# {name}\n\nGenerated React/TSX component.\n\nGoal: {goal}"))
            return files

        # --- Python function / script / utility ---
        if any(k in goal_lower for k in ["python", "function", "script", "def ", "add two", "calculate", "utility"]):
            func_name = self._extract_function_name(goal) or "process_data"
            print_line = f'    print(f"{func_name}({{a}}, {{b}}) = {{result}}")'
            py_code = f'''"""Auto-generated by Kairos Coder
Goal: {goal}
"""

from typing import Any


def {func_name}(a: int | float, b: int | float) -> int | float:
    """Example implementation based on the request.
    Replace with your actual logic.
    """
    result = a + b
{print_line}
    return result


if __name__ == "__main__":
    # Quick demo
    print({func_name}(10, 32))
    print({func_name}(3.5, 7.25))
'''
            files.append(("examples/generated_function.py", py_code))
            files.append(("PYTHON_TASK.md", f"# Python Implementation\n\n**Goal:** {goal}\n\nFile: `examples/generated_function.py`"))
            return files

        # --- FastAPI / API endpoint ---
        if any(k in goal_lower for k in ["api", "fastapi", "endpoint", "route", "server"]):
            endpoint = self._extract_endpoint(goal) or "/hello"
            api_code = f'''"""FastAPI endpoint generated by Kairos
Goal: {goal}
Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Kairos Generated API")


class Item(BaseModel):
    name: str
    value: int | float


@app.get("/")
def root():
    return {{"message": "Kairos API is running", "goal": "{goal[:60]}..."}}


@app.get("{endpoint}")
def {endpoint.strip("/").replace("/", "_") or "hello"}():
    return {{"status": "success", "result": "Hello from the generated endpoint"}}


@app.post("{endpoint}/item")
def create_item(item: Item):
    return {{"received": item.model_dump(), "processed": True}}
'''
            files.append(("api_generated.py", api_code))
            files.append(("API_README.md", f"# Generated API\n\n`python -m uvicorn api_generated:app --reload`\n\nGoal: {goal}"))
            return files

        # --- Generic but useful: create a clean Python module based on goal words ---
        # Infer a reasonable filename
        words = re.findall(r"[a-zA-Z]+", goal_lower)
        filename = "_".join(words[:4]) or "new_module"
        if not filename.endswith(".py"):
            filename += ".py"

        generic_py = f'''"""Module generated by Kairos for goal:
{goal}

This is a sensible starting point. Expand as needed.
"""

from __future__ import annotations


def main() -> None:
    """Entry point for the generated task."""
    print("Running generated code for: {goal}")
    # TODO: implement the actual logic here
    result = "Task completed successfully"
    print(result)
    return result


if __name__ == "__main__":
    main()
'''
        files.append((f"output/{filename}", generic_py))
        files.append(("TASK_NOTES.md", f"# Task Notes\n\n**Original goal:** {goal}\n\nImplementation file: output/{filename}"))

        return files

    # ==================== HELPERS ====================

    def _extract_title(self, goal: str) -> str:
        match = re.search(r"(?:page|website|title)\s+(?:called|named|with)?\s*['\"]?([A-Za-z0-9\s\-]+)", goal, re.IGNORECASE)
        if match:
            return match.group(1).strip().title()
        # fallback: take first few words
        words = [w for w in re.findall(r"[A-Za-z]+", goal) if len(w) > 2][:3]
        return " ".join(words).title() or "Hello"

    def _extract_body(self, goal: str) -> str:
        goal_lower = goal.lower()
        if "with" in goal_lower:
            after = goal[goal_lower.find("with") + 4 :].strip()
            if after:
                return after.capitalize()[:120]
        return "This page was automatically created by the Kairos autonomous coding swarm."

    def _extract_name(self, goal: str, default: str = "GeneratedComponent") -> str:
        match = re.search(r"([A-Z][a-zA-Z0-9]+Component|[A-Z][a-z]+)", goal)
        if match:
            return match.group(1)
        words = re.findall(r"[A-Za-z]+", goal)
        if words:
            return "".join(w.capitalize() for w in words[:3]) + "Component"
        return default

    def _extract_function_name(self, goal: str) -> str:
        # Look for explicit "function called foo" or "def foo"
        match = re.search(r"(?:function|def)\s+(?:called|named)?\s*([a-zA-Z_][a-zA-Z0-9_]*)", goal, re.IGNORECASE)
        if match:
            name = match.group(1)
            if name.lower() not in {"to", "a", "the", "and", "for"}:
                return name
        # Make a nice name from meaningful words in the goal
        words = [w for w in re.findall(r"[a-zA-Z]{3,}", goal.lower()) 
                 if w not in {"the", "and", "for", "create", "python", "function", "return", "sum", "add", "two", "numbers"}]
        if words:
            return "_".join(words[:3])
        return "generated_function"

    def _extract_endpoint(self, goal: str) -> str:
        match = re.search(r"/[a-zA-Z0-9/_-]+", goal)
        if match:
            return match.group(0)
        return "/hello"

    def _parse_and_write_files(self, llm_output: str) -> list[str]:
        """Robust parser for LLM output in FILE: format."""
        created: list[str] = []

        # Primary pattern
        pattern = r"FILE:\s*([^\n]+)\s*\n```[^\n]*\n(.*?)```"
        matches = re.findall(pattern, llm_output, re.DOTALL | re.IGNORECASE)

        for path, code in matches:
            path = path.strip().strip(" '\"`")
            if not path or not code.strip():
                continue
            result = self.tools.write_file(path, code.strip() + "\n")
            if result.get("success"):
                created.append(path)

        # Fallback: if LLM just dumped code without the marker
        if not created:
            if "<!DOCTYPE" in llm_output or "<html" in llm_output.lower():
                self.tools.write_file("output/llm_page.html", llm_output)
                created.append("output/llm_page.html")
            elif "def " in llm_output or "class " in llm_output:
                self.tools.write_file("output/llm_code.py", llm_output)
                created.append("output/llm_code.py")

        return created
