from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.panel import Panel

from tresto.core.test import run_test as run_test_code_in_file

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def run_test(state: TestAgentState) -> TestAgentState:
    console.print(f"🔍 Running {state.test_file_path}...")

    state.last_run_result = await run_test_code_in_file(state.test_file_path)

    if state.last_run_result.success:
        console.print(f"✅ Successfully ran the test in {state.last_run_result.duration_s:.2f} seconds")
    else:
        console.print(f"❌ Failed to run the test in {state.last_run_result.duration_s:.2f} seconds")

        # Display stdout in a panel if there's content
        if state.last_run_result.stdout and state.last_run_result.stdout.strip():
            stdout_panel = Panel(
                state.last_run_result.stdout,
                title="📤 Standard Output",
                title_align="left",
                border_style="blue",
                highlight=True,
            )
            console.print(stdout_panel)

        # Display stderr in a panel if there's content
        if state.last_run_result.stderr and state.last_run_result.stderr.strip():
            stderr_panel = Panel(
                state.last_run_result.stderr,
                title="❌ Error Output",
                title_align="left",
                border_style="red",
                highlight=True,
            )
            console.print(stderr_panel)

        if state.last_run_result.traceback and state.last_run_result.traceback.strip():
            traceback_panel = Panel(
                state.last_run_result.traceback,
                title="❌ Traceback",
                title_align="left",
                border_style="red",
                highlight=True,
            )
            console.print(traceback_panel)

    state.messages.append(HumanMessage(content=f"Test run result: {state.last_run_result}"))
    return state
