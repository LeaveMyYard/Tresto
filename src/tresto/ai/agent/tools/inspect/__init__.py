from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from tresto.ai.agent.tools.inspect.recording import RecordingManager, RecordingSources
from tresto.ai.agent.tools.inspect.tools import create_bound_tools

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def inspect_html_tool(state: TestAgentState) -> TestAgentState:
    """Tool for interactively exploring HTML content using a time-aware recording manager."""

    # Check if we have a recording to inspect
    if state.last_run_result is None or state.last_run_result.recording is None:
        error_panel = Panel(
            "No recording available to inspect. Run a test first to capture a recording.",
            title="❌ No HTML Data",
            title_align="left",
            border_style="red",
            highlight=True,
        )
        console.print(error_panel)

        state.messages.append(
            HumanMessage(content="Error: No recording available to inspect. Run a test first to capture a recording.")
        )
        return state

    manager = state.last_run_result.recording
    agent = state.create_agent(
        """You are exploring HTML content from a web page recording. Use tools to explore the HTML and screenshots at specific timestamps.""",
        tools=create_bound_tools(manager),
    )

    current_status_message = f"Last Run Result:\n{manager.to_text()}"
    console.print(
        Panel(
            current_status_message,
            title="Last Run Result",
            title_align="left",
            border_style="yellow",
            highlight=True,
        )
    )
    state.messages.append(HumanMessage(content=current_status_message))

    while True:
        result = await agent.invoke(
            message=HumanMessage(content="Use tools or respond with 'done' to finish."),
            panel_title="🤖 AI exploring HTML content...",
            border_style="yellow",
        )
        if result.endswith("done"):
            break

    return state
