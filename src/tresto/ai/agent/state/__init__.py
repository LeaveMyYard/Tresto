from __future__ import annotations

from contextlib import contextmanager
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict

from tresto import __version__
from tresto.ai import prompts
from tresto.core.config.main import TrestoConfig
from tresto.core.database import TestDatabase
from tresto.core.file_header import FileHeader, TrestoFileHeaderCorrupted
from tresto.core.test import TestRunResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from langchain.chat_models.base import BaseChatModel


class Decision(StrEnum):
    RECORD_USER_INPUT = "record_user_input"
    DESIDE_NEXT_ACTION = "decide_next_action"
    ASK_USER = "ask_user"
    RUN_TEST = "run_test"
    MODIFY_CODE = "modify_code"
    READ_FILE_CONTENT = "read_file_content"
    LIST_DIRECTORY = "list_directory"
    HTML_INSPECT = "html_inspect"
    # PROJECT_INSPECT = "project_inspect"
    # INSPECT_SITE = "inspect_site"
    FINISH = "finish"


class RunningTestState(BaseModel):
    total: int
    completed: int
    success: int
    failed: int


class TestAgentState(BaseModel):
    # Inputs
    test_name: str
    test_instructions: str
    test_file_path: Path
    recording_file_path: Path
    config: TrestoConfig

    # Conversational context
    messages: list[BaseMessage] = [SystemMessage(content=prompts.MAIN_PROMPT)]
    local_messages: list[BaseMessage] = []  # Temporary messages for tools

    # Working artifacts
    last_run_result: TestRunResult | None = None
    last_decision: Decision | None = None
    iterations: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def test_database(self) -> TestDatabase:
        """Get the test database for persistent storage."""
        return TestDatabase(
            test_directory=self.config.project.test_directory,
            test_name=self.test_name
        )

    def create_llm(self: TestAgentState) -> BaseChatModel:
        if self.config.ai.connector.lower() in {"openai", "gpt"}:
            return ChatOpenAI(model=self.config.ai.model, temperature=self.config.ai.temperature)

        return ChatAnthropic(model_name=self.config.ai.model, temperature=self.config.ai.temperature)

    @property
    def all_messages(self) -> list[BaseMessage]:
        """Get all messages including local messages for LLM context."""
        return self.messages + self.local_messages

    @contextmanager
    def temporary_messages(self) -> Iterator[None]:
        """Context manager to automatically clear local_messages when exiting."""
        try:
            yield
        finally:
            self.local_messages.clear()

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

    @property
    def project_inspection_report(self) -> str | None:
        """Get the project inspection report from database."""
        return self.test_database.get_project_inspection_report()

    @project_inspection_report.setter
    def project_inspection_report(self, value: str) -> None:
        """Store the project inspection report in database."""
        self.test_database.store_project_inspection_report(value)
