from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from pydantic import BaseModel

from tresto.ai.agent.state import Decision

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


class DecisionResponse(BaseModel):
    decision: Decision
    reason: str


async def tool_decide_next_action(state: TestAgentState) -> TestAgentState:
    available_actions = set(Decision) - {Decision.DESIDE_NEXT_ACTION}

    # If the user already recorded the test, let's not ask him to do it again
    if state.current_recording_code is not None:
        available_actions.remove(Decision.RECORD_USER_INPUT)

    agent = state.create_agent(
        f"""\
            You are required to decide the next action to take in a test.
            Available actions are: {" ".join(f"- {action.value}" for action in available_actions)}
            Respond with the decision and the reason.
        """
    )

    result = await agent.structured_process(DecisionResponse)

    state.last_decision = result.decision
    state.messages.append(HumanMessage(content=f"Model decided to take action: {state.last_decision.value}"))
    console.print(
        f"[bold green]✅ Model decided to take action: {state.last_decision.value}[/bold green]", justify="center"
    )
    return state
