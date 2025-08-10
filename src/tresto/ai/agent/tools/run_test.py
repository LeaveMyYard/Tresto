from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tresto.core.test import TestRunResult, run_test_code_in_file

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


async def run_test(state: TestAgentState) -> dict[str, Any]:
    code = state.get("current_test_code", "")
    test_file_path = state["test_file_path"]
    result: TestRunResult = await run_test_code_in_file(code, test_file_path)
    return {"run_result": result}
