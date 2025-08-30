from __future__ import annotations

import asyncio
import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def ask_user(state: TestAgentState) -> TestAgentState:
    llm = state.create_llm()

    ask_user_message = HumanMessage(
        textwrap.dedent(
            """\
                Model wanted to ask user a question.
                With next message, formulate what question you want to ask.
            """
        )
    )

    # Stream the AI's question generation with live display
    question_content = ""

    console.print()  # Add spacing before streaming

    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.messages + [ask_user_message]):
            if chunk.content:
                question_content += str(chunk.content)

                # Create markdown content for the question
                markdown_content = Markdown(question_content, style="bold")
                char_count = len(question_content)

                # Display in a panel with character count and padding
                panel = Panel(
                    markdown_content,
                    title=f"❓ AI Question ({char_count} characters)",
                    title_align="left",
                    border_style="blue",
                    highlight=True,
                    padding=(1, 2),
                )
                live.update(panel)

    # Get user input with a styled prompt
    console.print()  # Add spacing before input
    answer = await asyncio.to_thread(
        lambda: Prompt.ask(
            "[bold cyan]Your answer[/bold cyan]",
            console=console,
        )
    )

    state.messages.append(AIMessage(content=question_content))
    state.messages.append(HumanMessage(content=answer))
    return state
