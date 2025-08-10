from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from tresto.ai.agent.state import TestAgentState


def _ask_input_impl(prompt: str) -> str:
    return builtins.input(f"{prompt}\n> ")


async def ask_user(state: TestAgentState, ask_user_fn: Callable[[str], str] | None = None) -> dict[str, Any]:
    question = (
        state.get("pending_question") or "Provide additional details or constraints for the test (or leave empty)."
    )
    ask = ask_user_fn or _ask_input_impl
    answer = await __import__("asyncio").to_thread(ask, question)
    msgs = state.get("messages", []) + [f"USER:\n{answer}"]
    return {"messages": msgs, "pending_question": ""}
