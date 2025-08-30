from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from tresto.ai.agent.tools.html_inspect.tools import create_bound_tools

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def inspect_html_tool(state: TestAgentState) -> TestAgentState:
    """Tool for interactively exploring HTML content using BeautifulSoup."""

    # Check if we have HTML content to inspect
    if state.last_run_result is None or state.last_run_result.soup is None:
        error_panel = Panel(
            "No HTML content available to inspect. Run a test first to capture HTML.",
            title="❌ No HTML Data",
            title_align="left",
            border_style="red",
            highlight=True,
        )
        console.print(error_panel)

        state.messages.append(
            HumanMessage(content="Error: No HTML content available to inspect. Run a test first to capture HTML.")
        )
        return state

    soup = state.last_run_result.soup
    agent = state.create_agent(
        system_message="""You are exploring HTML content from a web page using BeautifulSoup. Use tools to explore the HTML content.""",
        tools=create_bound_tools(soup),
    )

    while True:
        result = await agent.invoke(
            message=HumanMessage(content="Use tools or respond with 'done' to finish."),
            panel_title="🤖 AI exploring HTML content...",
            border_style="yellow",
        )
        if result == "done":
            break

    return state
