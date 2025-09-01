from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from langgraph.graph import END, StateGraph
from rich.console import Console

from .state import Decision, TestAgentState
from .tools.ask_user import ask_user as tool_ask_user
from .tools.deside_next_action import tool_decide_next_action
from .tools.generate import generate_or_update_code
from .tools.inspect import inspect_html_tool
from .tools.playwright_codegen import tool_record_user_input
from .tools.run_test import run_test as tool_run_test

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

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
        recording_file_path: Path,
        ask_user: Callable[[str], str] | None = None,
        console: Console | None = None,
    ) -> None:
        self.config = config
        self._ask_user = ask_user or _ask_input_impl
        self._console = console or Console()

        self.test_name = test_name
        self.test_file_path = test_file_path
        self.test_instructions = test_instructions
        self.recording_file_path = recording_file_path

        self.state = TestAgentState(
            test_name=test_name,
            test_file_path=test_file_path,
            test_instructions=test_instructions,
            config=config,
            recording_file_path=recording_file_path,
        )

        self.state.messages.append(self.state.current_state_message)
        self.state.messages.extend(self.state.test_database.to_prompt())

    async def init(self) -> None:
        if self.state.current_recording_code is None:
            await tool_record_user_input(self.state)

        await tool_run_test(self.state)

        # if self.state.project_inspection_report is None:
        #     await project_inspect_cycle(self.state)

        # Build graph with logging wrappers
        graph = StateGraph(TestAgentState)

        graph.add_node(Decision.RECORD_USER_INPUT, tool_record_user_input)
        graph.add_node(Decision.DESIDE_NEXT_ACTION, tool_decide_next_action)
        graph.add_node(Decision.MODIFY_CODE, generate_or_update_code)
        graph.add_node(Decision.RUN_TEST, tool_run_test)
        graph.add_node(Decision.INSPECT, inspect_html_tool)
        graph.add_node(Decision.ASK_USER, tool_ask_user)

        graph.set_entry_point(Decision.DESIDE_NEXT_ACTION)

        # Always run the test after modifying the code
        graph.add_edge(Decision.MODIFY_CODE, Decision.RUN_TEST)

        # After any tool (except for code modification), ask on what to do next
        for node in set(Decision) - {Decision.FINISH, Decision.DESIDE_NEXT_ACTION, Decision.MODIFY_CODE}:
            graph.add_edge(node, Decision.DESIDE_NEXT_ACTION)

        # Router
        def router(state: TestAgentState) -> str:
            return state.last_decision or Decision.DESIDE_NEXT_ACTION

        # Decide next action conditionally goes to the next tool, based on the model response
        graph.add_conditional_edges(
            Decision.DESIDE_NEXT_ACTION,
            router,
            # We map all decisions to themselves, so that we can use the decision as a key in the dictionary
            {Decision(v.value): Decision(v.value) for v in Decision._member_map_.values()} | {Decision.FINISH: END},
        )

        self._app = graph.compile()

    async def run(self) -> None:
        try:
            await self._app.ainvoke(self.state, {"recursion_limit": 100})
        except Exception:  # noqa: BLE001
            self._console.print_exception()
        else:
            self._console.print("[bold green]✅ Finished[/bold green]")
