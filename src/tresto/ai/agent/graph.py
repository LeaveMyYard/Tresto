from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, cast

from langgraph.graph import END, StateGraph
from rich.console import Console
from pathlib import Path

from .state import Decision, TestAgentState
from .tools.ask_user import ask_user as tool_ask_user
from .tools.deside_next_action import tool_decide_next_action
from .tools.generate import generate_or_update_code
from .tools.playwright_codegen import tool_record_user_input
from .tools.run_test import run_test as tool_run_test

if TYPE_CHECKING:
    from collections.abc import Callable

    from tresto.core.config.main import TrestoConfig


def _ask_input_impl(prompt: str) -> str:
    return builtins.input(f"{prompt}\n> ")


class LangGraphTestAgent:
    """LangGraph-driven agent that can generate, run, inspect, and refine tests."""

    def __init__(
        self,
        config: TrestoConfig,
        test_name: str,
        test_file_path: Path,
        test_instructions: str,
        ask_user: Callable[[str], str] | None = None,
        console: Console | None = None,
    ) -> None:
        self.config = config
        self._ask_user = ask_user or _ask_input_impl
        self._console = console or Console()

        self.test_name = test_name
        self.test_file_path = test_file_path
        self.test_instructions = test_instructions

        self.state = TestAgentState(
            test_name=test_name,
            test_file_path=test_file_path,
            test_instructions=test_instructions,
            config=config,
            recording_file_path=Path(f"./tresto/.recordings/{test_name}.py"),
        )

        self.state.messages.append(self.state.current_state_message)

        # Build graph with logging wrappers
        graph = StateGraph(TestAgentState)

        graph.add_node(Decision.RECORD_USER_INPUT, tool_record_user_input)
        graph.add_node(Decision.DESIDE_NEXT_ACTION, tool_decide_next_action)
        graph.add_node(Decision.MODIFY_CODE, generate_or_update_code)
        graph.add_node(Decision.RUN_TEST, tool_run_test)
        # graph.add_node(Decision.INSPECT_SITE, tool_inspect)
        graph.add_node(Decision.ASK_USER, self.ask_user)

        graph.set_entry_point(
            Decision.DESIDE_NEXT_ACTION if self.state.current_recording_code is not None else Decision.RECORD_USER_INPUT
        )

        for node in set(Decision) - {Decision.FINISH, Decision.DESIDE_NEXT_ACTION}:
            graph.add_edge(node, Decision.DESIDE_NEXT_ACTION)

        # Router
        def router(state: TestAgentState) -> str:
            return state.last_decision or Decision.DESIDE_NEXT_ACTION

        graph.add_conditional_edges(
            Decision.DESIDE_NEXT_ACTION,
            router,
            # We map all decisions to themselves, so that we can use the decision as a key in the dictionary
            {Decision(v.value): Decision(v.value) for v in Decision._member_map_.values()} | {Decision.FINISH: END},
        )

        self._app = graph.compile()

    async def ask_user(self, state: TestAgentState) -> TestAgentState:
        return await tool_ask_user(state, self._ask_user)

    async def run(self) -> None:
        try:
            await self._app.ainvoke(self.state)
        except Exception:  # noqa: BLE001
            self._console.print_exception()
        else:
            self._console.print("[bold green]Agent Finished[/bold green]")
