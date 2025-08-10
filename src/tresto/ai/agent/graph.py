from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any

from langgraph.graph import END, StateGraph

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

    def __init__(self, config: TrestoConfig, ask_user: Callable[[str], str] | None = None) -> None:
        self.config = config
        self.ask_user = ask_user or _ask_input_impl

        # Router
        def router(state: TestAgentState) -> str:
            return str(_decide_next(state).get("decision", "finish"))

        # Build graph
        graph = StateGraph(TestAgentState)
        graph.add_node("modify_code", generate_or_update_code)
        graph.add_node("run_test", tool_run_test)
        graph.add_node("inspect_site", tool_inspect)
        graph.add_node("ask_user", lambda s: tool_ask_user(s, self.ask_user))

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

        self._app = graph.compile()

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

        return state
