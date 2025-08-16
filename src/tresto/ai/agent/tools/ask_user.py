from __future__ import annotations

import asyncio
import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from rich.console import Console

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def ask_user(state: TestAgentState) -> TestAgentState:
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

    answer = await asyncio.to_thread(lambda: console.input(question.content))
    state.messages.append(AIMessage(content=question.content))
    state.messages.append(HumanMessage(content=answer))
    return state
