from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, SystemMessage
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from tresto.ai.agent.state import Decision

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def tool_decide_next_action(state: TestAgentState) -> TestAgentState:
    llm = state.create_llm()

    # We create a copy of the messages to avoid modifying the original list
    # So that we don't pass useless messages to the model
    messages = state.messages.copy()
    available_actions = set(Decision) - {Decision.DESIDE_NEXT_ACTION}

    # If the user already recorded the test, let's not ask him to do it again
    if state.current_recording_code is not None:
        available_actions.add(Decision.RECORD_USER_INPUT)

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

    # Stream the response and display markdown in real-time
    reasoning_content = ""

    console.print()  # Add spacing before streaming
    
    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(messages):
            if chunk.content:
                reasoning_content += chunk.content
                
                # Create markdown content with character count
                markdown_content = Markdown(reasoning_content, style="dim")
                char_count = len(reasoning_content)
                
                # Display in a panel with title showing character count
                panel = Panel(
                    markdown_content,
                    title=f"🤔 AI Reasoning ({char_count} characters)",
                    title_align="left",
                    border_style="dim"
                )
                live.update(panel)
    
    console.print()  # Add spacing after streaming completes
    
    messages.append(AIMessage(content=reasoning_content))
    decision = reasoning_content.split("\n")[-1].strip()

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
            
            # Stream the retry response with markdown too
            retry_content = ""
            
            with Live(console=console, refresh_per_second=10) as live:
                async for chunk in llm.astream(messages):
                    if chunk.content:
                        retry_content += chunk.content
                        
                        # Create markdown content with character count
                        markdown_content = Markdown(retry_content)
                        char_count = len(retry_content)
                        
                        # Display in a panel with title showing character count
                        panel = Panel(
                            markdown_content,
                            title=f"🔄 AI Retry ({char_count} characters)",
                            title_align="left",
                            border_style="yellow"
                        )
                        live.update(panel)
            
            console.print()  # Add spacing after retry streaming completes
            decision = retry_content.split("\n")[-1].strip()
        else:
            break

    state.messages.append(SystemMessage(content=f"Model decided to take action: {state.last_decision.value}"))
    console.print(f"[bold green]✅ Model decided to take action: {state.last_decision.value}[/bold green]", justify="center")
    return state
