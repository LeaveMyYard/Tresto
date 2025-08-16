from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, SystemMessage
from rich.console import Console
from rich.progress import Progress

from tresto.ai.agent.state import Decision

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def tool_decide_next_action(state: TestAgentState) -> TestAgentState:
    with Progress() as progress:
        task = progress.add_task("Deciding next action", total=100)
        llm = state.create_llm()

        # We create a copy of the messages to avoid modifying the original list
        # So that we don't pass useless messages to the model
        messages = state.messages.copy()
        available_actions = set(Decision) - {Decision.DESIDE_NEXT_ACTION}

        message = SystemMessage(
            textwrap.dedent(
                f"""\
                    You are required to decide the next action to take in a test.
                    Available actions are: {" ".join(f"- {action.value}" for action in available_actions)}
                    With the next message, verbosely think about what to choose.
                    The last line should contain the action you want to take and nothing else.
                """
            )
        )

        messages.append(message)

        reasoning = await llm.ainvoke(messages)
        console.print(reasoning.content)
        messages.append(AIMessage(content=reasoning.content))
        decision = reasoning.content.split("\n")[-1].strip()

        progress.update(task, completed=90)

        while True:
            try:
                if decision in available_actions:
                    state.last_decision = Decision(decision)
                else:
                    raise ValueError(
                        f"Invalid action: {decision}. "
                        f"Available actions are: {'\n'.join(f'- {action.value}' for action in available_actions)}"
                    )
            except ValueError:
                messages.append(
                    SystemMessage(
                        f"Invalid action: {decision}. "
                        f"Available actions are: {'\n'.join(f'- {action.value}' for action in available_actions)}"
                        f"\nTry again with the correct action and nothing else."
                    )
                )
                decision = (await llm.ainvoke(messages)).content.split("\n")[-1].strip()
            else:
                break

        progress.update(task, completed=100)

        state.messages.append(SystemMessage(content=f"Model decided to take action: {state.last_decision.value}"))
        return state
