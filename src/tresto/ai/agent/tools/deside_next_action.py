from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from rich.console import Console, RenderableType
from rich.panel import Panel

from tresto.ai.agent.state import Decision

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


class DecisionResponse(BaseModel):
    decision: Decision
    reason: str

    def format(self) -> RenderableType:
        return Panel(
            self.decision.description,
            title=f"Decision: {self.decision.value}",
            title_align="left",
            border_style="green",
        )


async def tool_decide_next_action(state: TestAgentState) -> TestAgentState:
    available_actions = set(Decision) - {Decision.DESIDE_NEXT_ACTION}

    # If the user already recorded the test, let's not ask him to do it again
    if state.current_recording_code is not None:
        available_actions.remove(Decision.RECORD_USER_INPUT)

    actions = "\n".join(f"- {action.value} ({action.description})" for action in available_actions)
    prompt = """\
        You are required to decide the next action to take in a test.
        Available actions are: {actions}
        Respond with the decision and the reason.
    """

    agent = state.create_agent(prompt.format(actions=actions))

    result = await agent.structured_response(DecisionResponse)

    state.last_decision = result.decision
    state.messages.append(HumanMessage(content=f"Model decided to take action: {state.last_decision.value}"))
    console.print(
        f"[bold green]✅ Model decided to take action: {state.last_decision.value}[/bold green]", justify="center"
    )
    return state
