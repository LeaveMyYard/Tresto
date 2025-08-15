from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import SystemMessage, AIMessage

from tresto.ai.agent.state import DecideNextActionStep, Decision

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


async def tool_decide_next_action(state: TestAgentState) -> TestAgentState:
    decide_next_action_step = DecideNextActionStep()
    await state.add_output(decide_next_action_step)

    async with decide_next_action_step:
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
        decide_next_action_step.reasoning = reasoning.content
        messages.append(AIMessage(content=reasoning.content))
        decision = reasoning.content.split("\n")[-1].strip()

        while True:
            
            try:
                if decision in available_actions:
                    state.last_decision = Decision(decision)
                else:
                    raise ValueError(f"Invalid action: {decision}. Available actions are: {'\n'.join(f'- {action.value}' for action in available_actions)}")
            except ValueError as e:
                print(e)
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

        decide_next_action_step.end_message = f"Model decided to take action: {state.last_decision.value}"

        state.messages.append(SystemMessage(content=decide_next_action_step.end_message))
        return state
