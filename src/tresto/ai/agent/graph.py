from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any

from langgraph.graph import END, StateGraph
from rich.console import Console

from .state import TestAgentState
from .tools.ask_user import ask_user as tool_ask_user
from .tools.generate import generate_or_update_code
from .tools.inspect import inspect as tool_inspect
from .tools.run_test import run_test as tool_run_test

if TYPE_CHECKING:
    from tresto.core.config.main import TrestoConfig
    from collections.abc import Callable



def _ask_input_impl(prompt: str) -> str:
    return builtins.input(f"{prompt}\n> ")


def _ensure_state_defaults(state: TestAgentState) -> TestAgentState:
    state.setdefault("messages", [])
    return state


def _decide_next(state: TestAgentState) -> dict[str, Any]:
    it = state.get("iterations", 0)
    max_it = state.get("max_iterations", 5)
    if it >= max_it:
        return {"decision": "finish"}

    if "current_test_code" not in state:
        return {"decision": "modify_code"}

    if "run_result" not in state:
        return {"decision": "run_test"}

    run = state["run_result"]
    if not run.success:
        if not state.get("inspection_notes"):
            return {"decision": "inspect_site"}
        if it % 2 == 1:
            return {"decision": "ask_user"}
        return {"decision": "modify_code"}

    return {"decision": "finish"}


class LangGraphTestAgent:
    """LangGraph-driven agent that can generate, run, inspect, and refine tests."""

    def __init__(self, config: TrestoConfig, ask_user: Callable[[str], str] | None = None, console: Console | None = None) -> None:
        self.config = config
        self.ask_user = ask_user or _ask_input_impl
        self._console = console or Console()

        # Router
        def router(state: TestAgentState) -> str:
            return str(_decide_next(state).get("decision", "finish"))

        # Build graph with logging wrappers
        graph = StateGraph(TestAgentState)

        def wrap(name: str, fn):
            async def inner(s: TestAgentState):
                it = s.get("iterations", 0) + 1
                self._console.print(f"[bold cyan]{name} • iteration {it}[/bold cyan]")
                res = await fn(s)
                # For code editing, only print a single edit line
                if name == "Generate/Improve Code":
                    filename = s.get("test_file_path", "<unknown>")
                    self._console.print(f"Edited {filename}")
                    return res
                # Pretty-print debug payloads if present
                dbg_gen = res.get("debug_generate") if isinstance(res, dict) else None
                if isinstance(dbg_gen, dict):
                    prompt = dbg_gen.get("prompt") or ""
                    preview = dbg_gen.get("response_preview") or ""
                    if prompt:
                        self._console.print("[bold cyan]Prompt:[/bold cyan]")
                        self._console.print(prompt)
                    if preview:
                        self._console.print("[bold magenta]Model Output (preview):[/bold magenta]")
                        self._console.print(preview)

                think = res.get("debug_think") if isinstance(res, dict) else None
                if isinstance(think, str) and think.strip():
                    self._console.print("[bold blue]Thinking:[/bold blue]")
                    self._console.print(think)

                dbg_run = res.get("debug_run") if isinstance(res, dict) else None
                if isinstance(dbg_run, dict):
                    ok = dbg_run.get("success")
                    dur = dbg_run.get("duration_s")
                    color = "green" if ok else "red"
                    self._console.print(f"[bold {color}]Test Run: success={ok} duration={dur:.2f}s[/bold {color}]")
                    tb = dbg_run.get("traceback")
                    if tb:
                        self._console.print("[bold red]Traceback:[/bold red]")
                        self._console.print(tb)

                dbg_inspect = res.get("debug_inspect") if isinstance(res, dict) else None
                if isinstance(dbg_inspect, str) and dbg_inspect.strip():
                    self._console.print("[bold yellow]Inspection Notes:[/bold yellow]")
                    self._console.print(dbg_inspect)
                return res

            return inner

        graph.add_node("modify_code", wrap("Generate/Improve Code", generate_or_update_code))
        graph.add_node("run_test", wrap("Run Test", tool_run_test))
        graph.add_node("inspect_site", wrap("Inspect Site", tool_inspect))
        graph.add_node("ask_user", wrap("Ask User", lambda s: tool_ask_user(s, self.ask_user)))

        graph.set_conditional_entry_point(
            router,
            {
                "modify_code": "modify_code",
                "run_test": "run_test",
                "inspect_site": "inspect_site",
                "ask_user": "ask_user",
                "finish": END,
            },
        )

        # Edges: after each action, route again
        for node in ("modify_code", "run_test", "inspect_site", "ask_user"):
            graph.add_conditional_edges(
                node,
                router,
                {
                    "modify_code": "modify_code",
                    "run_test": "run_test",
                    "inspect_site": "inspect_site",
                    "ask_user": "ask_user",
                    "finish": END,
                },
            )

        self._app = graph.compile(debug=True)

    async def run(
        self,
        *,
        test_name: str,
        test_instructions: str,
        test_file_path: str,
        recording_path: str | None,
        max_iterations: int = 5,
    ) -> TestAgentState:
        initial: TestAgentState = {
            "test_name": test_name,
            "test_instructions": test_instructions,
            "test_file_path": test_file_path,
            "recording_path": recording_path or "",
            "config": self.config,
            "messages": [],
            "iterations": 0,
            "max_iterations": max_iterations,
        }

        state = _ensure_state_defaults(initial)
        while True:
            # Execute one step
            state = await self._app.ainvoke(state)
            state["iterations"] = state.get("iterations", 0) + 1

            if _decide_next(state).get("decision") == "finish":
                break

        self._console.print("[bold green]Agent Finished[/bold green]")
        return state
