from __future__ import annotations

import asyncio
import builtins
import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

if TYPE_CHECKING:
    from collections.abc import Callable

    from tresto.ai.agent.state import TestAgentState


def _ask_input_impl(prompt: str) -> str:
    return builtins.input(f"{prompt}\n> ")


async def ask_user(state: TestAgentState, ask_user_fn: Callable[[str], str] | None = None) -> TestAgentState:
    llm = state.create_llm()

    ask_user_message = SystemMessage(
        textwrap.dedent(
            """\
                Model wanted to ask user a question.
                With next message, formulate what question you want to ask.
            """
        )
    )

    question = await llm.ainvoke(state.messages + [ask_user_message])

    ask = ask_user_fn or _ask_input_impl
    answer = await asyncio.to_thread(ask, question.content)
    state.messages.append(AIMessage(content=question.content))
    state.messages.append(HumanMessage(content=answer))
    return state
