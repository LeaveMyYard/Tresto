from __future__ import annotations

from contextlib import contextmanager
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel, ConfigDict

from tresto import __version__
from tresto.ai.agent.agent import Agent
from tresto.core.config.main import TrestoConfig
from tresto.core.database import TestDatabase
from tresto.core.file_header import FileHeader, TrestoFileHeaderCorrupted
from tresto.core.test import TestRunResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from langchain.chat_models.base import BaseChatModel
    from langchain_core.tools import Tool


class Decision(StrEnum):
    MODIFY_CODE = "modify_code"
    RUN_TEST = "run_test"
    INSPECT = "inspect"
    # SCREENSHOT_INSPECT = "screenshot_inspect"
    ASK_USER = "ask_user"
    RECORD_USER_INPUT = "record_user_input"
    DESIDE_NEXT_ACTION = "decide_next_action"
    # READ_FILE_CONTENT = "read_file_content"
    # LIST_DIRECTORY = "list_directory"
    # PROJECT_INSPECT = "project_inspect"
    # INSPECT_SITE = "inspect_site"
    FINISH = "finish"

    @property
    def description(self) -> str:
        return {
            self.MODIFY_CODE: "Modify the test code",
            self.RUN_TEST: "Run the test",
            self.INSPECT: (
                "Inspect the state of the website during the test run by inspecting snapshots by time. "
                "(By HTML or screenshots)"
            ),
            self.ASK_USER: "Ask the user for input",
            self.RECORD_USER_INPUT: "Record the user input using playwright codegen",
            self.DESIDE_NEXT_ACTION: "Decide the next action to take",
            self.FINISH: "Finish working (task is finished or task can not be finished)",
        }[self]


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
    messages: list[BaseMessage | dict] = []
    local_messages: list[BaseMessage | dict] = []  # Temporary messages for tools

    # Working artifacts
    last_run_result: TestRunResult | None = None
    last_decision: Decision | None = None
    iterations: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def create_agent(self, task_message: str, tools: list[Tool] | None = None) -> Agent:
        return Agent(
            state=self,
            llm=self.create_llm(tools=tools),
            task_message=task_message,
            tools={tool.name: tool for tool in tools or []},
        )

    def add_message(self, message: BaseMessage | dict) -> None:
        with open(self.config.project.test_directory / "debug.txt", "a") as f:
            f.write(f"{message}\n")

        if not isinstance(message, dict) and not message.content:
            return

        self.messages.append(message)

        with open(self.config.project.test_directory / "state.yaml", "w") as f:
            yaml.dump(self.model_dump(mode="json", exclude=["last_run_result"]), f, indent=2)

    @property
    def test_database(self) -> TestDatabase:
        """Get the test database for persistent storage."""
        return TestDatabase(test_directory=self.config.project.test_directory, test_name=self.test_name)

    def create_llm(self: TestAgentState, tools: list[Tool] | None = None) -> BaseChatModel:
        # Make it possible to pass custom options to the LLM
        options = self.config.ai.options or {}

        return init_chat_model(
            f"{self.config.ai.connector}:{self.config.ai.model}",
            max_tokens=self.config.ai.max_tokens,
            temperature=self.config.ai.temperature,
            max_retries=3,
            **options,
        ).bind_tools(tools or [])

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
    def current_state_message(self) -> HumanMessage:
        return HumanMessage(
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
