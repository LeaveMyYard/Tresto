from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import SystemMessage

from tresto.core.test import run_test_code_in_file

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


async def run_test(state: TestAgentState) -> TestAgentState:
    state.last_run_result = await run_test_code_in_file(state.current_test_code, state.test_file_path)
    state.messages.append(SystemMessage(content=f"Test run result: {state.last_run_result}"))
    await state.output_to_console(f"Test run result: {state.last_run_result}")
    return state