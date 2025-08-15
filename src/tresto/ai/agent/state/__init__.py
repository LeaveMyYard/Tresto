from __future__ import annotations

import asyncio
import textwrap
from abc import ABC, abstractmethod
from asyncio import Queue
from collections.abc import AsyncIterable
from enum import StrEnum
from pathlib import Path
from typing import Any, Self

from langchain.chat_models.base import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, BaseMessageChunk, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict, Field

from tresto import __version__
from tresto.core.config.main import TrestoConfig
from tresto.core.test import TestRunResult


class Decision(StrEnum):
    RECORD_USER_INPUT = "record_user_input"
    DESIDE_NEXT_ACTION = "decide_next_action"
    ASK_USER = "ask_user"
    RUN_TEST = "run_test"
    MODIFY_CODE = "modify_code"
    # INSPECT_SITE = "inspect_site"
    FINISH = "finish"


class ConsoleStepOutput[T](ABC):
    @abstractmethod
    def consume(self) -> AsyncIterable[T]: ...


class ThinkingStep(BaseModel, ConsoleStepOutput[str]):
    batch_queue: Queue[BaseMessageChunk] = Field(default_factory=Queue)
    result: str = ""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def add_message_chunk(self, chunk: BaseMessageChunk) -> None:
        await self.batch_queue.put(chunk)

    async def consume(self) -> AsyncIterable[str]:
        yield "Thinking..."

        chunk = await self.batch_queue.get()

        while chunk.type != "end":
            self.result += chunk.content if isinstance(chunk.content, str) else "\n".join(str(c) for c in chunk.content)
            yield self.result

            chunk = await self.batch_queue.get()


class PrintingStep(BaseModel, ConsoleStepOutput[str]):
    text: str

    async def consume(self) -> AsyncIterable[str]:
        yield self.text


class WaitingStep(BaseModel, ConsoleStepOutput[str]):
    done: asyncio.Event = Field(default_factory=asyncio.Event)
    start_message: str = "Waiting..."
    end_message: str = "Done."

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def __aenter__(self) -> Self:
        self.done.clear()
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.done.set()

    async def consume(self) -> AsyncIterable[str]:
        yield self.start_message

        await self.done.wait()

        yield self.end_message


class WritingCodeStep(BaseModel, ConsoleStepOutput[str]):
    path: str

    async def consume(self) -> AsyncIterable[str]:
        yield f"Writing code to {self.path}..."


class PlaywrightRecordingStep(WaitingStep):
    start_message: str = "Recording user manually conducting the test using playwright codegen..."
    end_message: str = "Recording completed."


class DecideNextActionStep(WaitingStep):
    start_message: str = "Deciding next action..."
    reasoning: str = ""
    end_message: str = "Next action decided."

    async def consume(self) -> AsyncIterable[str]:
        yield self.start_message

        await self.done.wait()

        yield self.reasoning

        yield self.end_message


class RunningTestState(BaseModel):
    total: int
    completed: int
    success: int
    failed: int


class RunningTests(ConsoleStepOutput[RunningTestState]):
    async def consume(self) -> AsyncIterable[RunningTestState]:
        yield RunningTestState(total=10, completed=0, success=0, failed=0)
        await asyncio.sleep(1)
        yield RunningTestState(total=10, completed=1, success=1, failed=0)
        await asyncio.sleep(1)
        yield RunningTestState(total=10, completed=2, success=1, failed=1)
        await asyncio.sleep(1)
        yield RunningTestState(total=10, completed=10, success=10, failed=0)


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


AgentConsoleStepOutput = ThinkingStep | WaitingStep | WritingCodeStep | PrintingStep


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

    output_queue: Queue[AgentConsoleStepOutput] = Field(default_factory=Queue)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def create_llm(self: TestAgentState) -> BaseChatModel:
        if self.config.ai.connector.lower() in {"openai", "gpt"}:
            return ChatOpenAI(model=self.config.ai.model, temperature=self.config.ai.temperature)

        return ChatAnthropic(model_name=self.config.ai.model, temperature=self.config.ai.temperature)

    async def add_output(self, output: AgentConsoleStepOutput) -> None:
        await self.output_queue.put(output)

    async def consume_output(self) -> AgentConsoleStepOutput:
        return await self.output_queue.get()

    async def output_to_console(self, text: str) -> None:
        await self.output_queue.put(PrintingStep(text=text))

    def output_to_console_nowait(self, text: str) -> None:
        self.output_queue.put_nowait(PrintingStep(text=text))

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
            with open(self.test_file_path) as f:
                result = f.read()
                if result.startswith("# Generated by Tresto"):
                    return result.split("\n\n", 1)[-1].strip()
                return result
        except FileNotFoundError:
            return None

    @current_test_code.setter
    def current_test_code(self, value: str) -> None:
        with open(self.test_file_path, "w") as f:
            f.write(
                f"# Generated by Tresto v{__version__}\n"
                f"# Test name: {self.test_name}\n"
                f"# Test instructions: {self.test_instructions}\n"
                f"\n\n{value}"
            )

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
