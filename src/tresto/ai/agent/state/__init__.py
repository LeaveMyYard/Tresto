from __future__ import annotations

import textwrap
from enum import StrEnum
from pathlib import Path

from langchain.chat_models.base import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict

from tresto import __version__
from tresto.core.config.main import TrestoConfig
from tresto.core.test import TestRunResult

from tresto.core.file_header import FileHeader, TrestoFileHeaderCorrupted


class Decision(StrEnum):
    RECORD_USER_INPUT = "record_user_input"
    DESIDE_NEXT_ACTION = "decide_next_action"
    ASK_USER = "ask_user"
    RUN_TEST = "run_test"
    MODIFY_CODE = "modify_code"
    # READ_FILE_CONTENT = "read_file_content"
    # LIST_DIRECTORY = "list_directory"
    # INSPECT_SITE = "inspect_site"
    FINISH = "finish"


class RunningTestState(BaseModel):
    total: int
    completed: int
    success: int
    failed: int


SYSTEM_PROMPT = textwrap.dedent(
    """\
        You are a CLI tool called Tresto. You write automatic E2E tests for web applications.
        You are given a codegen file of user manually executing a test on his website.
        Your task is to produce a complete, meaningful test for this website using pytest + Playwright async API.
        Use robust selectors and proper waits, and meaningful expect() assertions.
        You will be running in the loop and will be able to select actions to take: 
        write code, ask the user for input, ask the user to manually record the test using playwright codegen, etc.
    """
)


class TestAgentState(BaseModel):
    # Inputs
    test_name: str
    test_instructions: str
    test_file_path: Path
    recording_file_path: Path
    config: TrestoConfig

    # Conversational context
    messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]

    # Working artifacts
    last_run_result: TestRunResult | None = None
    last_decision: Decision | None = None
    iterations: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def create_llm(self: TestAgentState) -> BaseChatModel:
        if self.config.ai.connector.lower() in {"openai", "gpt"}:
            return ChatOpenAI(model=self.config.ai.model, temperature=self.config.ai.temperature)

        return ChatAnthropic(model_name=self.config.ai.model, temperature=self.config.ai.temperature)

    @property
    def current_state_message(self) -> SystemMessage:
        return SystemMessage(
            f"Test name: {self.test_name}\n"
            f"Test instructions: {self.test_instructions}\n\n"
            + self._current_test_code_message
            + "\n\n"
            + self._current_recording_code_message
        )

    @property
    def _current_test_code_message(self) -> str:
        return (
            "Current test code:\n```python\n" + self.current_test_code + "\n```"
            if self.current_test_code
            else "There is no test code yet."
        )

    @property
    def _current_recording_code_message(self) -> str:
        return (
            "Current recording code:\n```python\n" + self.current_recording_code + "\n```"
            if self.current_recording_code
            else "There is no recording code yet."
        )

    @property
    def current_test_code(self) -> str | None:
        try:
            return FileHeader.read_from_file(self.test_file_path).content
        except TrestoFileHeaderCorrupted:
            return None

    @current_test_code.setter
    def current_test_code(self, value: str) -> None:
        file = FileHeader.read_from_file(self.test_file_path)
        file.content = value
        file.write_to_file(self.test_file_path)

    @property
    def current_recording_code(self) -> str | None:
        try:
            with open(self.recording_file_path) as f:
                return f.read()
        except FileNotFoundError:
            return None

    @current_recording_code.setter
    def current_recording_code(self, value: str) -> None:
        with open(self.recording_file_path, "w") as f:
            f.write(value)
