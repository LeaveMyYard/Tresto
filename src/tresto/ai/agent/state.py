from __future__ import annotations

from typing import Literal, TypedDict
from tresto.core.config.main import TrestoConfig
from tresto.core.test import TestRunResult

Decision = Literal["ask_user", "run_test", "modify_code", "inspect_site", "finish"]

class TestAgentState(TypedDict, total=False):
    # Inputs
    test_name: str
    test_instructions: str
    test_file_path: str
    recording_path: str
    config: TrestoConfig

    # Conversational context
    messages: list[str]

    # Working artifacts
    current_test_code: str
    run_result: TestRunResult
    inspection_notes: str
    iterations: int
    max_iterations: int
    pending_question: str
    decision: Decision
