from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, HumanMessage
from rich.console import Console
from rich.panel import Panel

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def screenshot_inspect_tool(state: TestAgentState) -> TestAgentState:
    """Tool for sending screenshot to AI for analysis."""

    # Check if we have screenshot content to inspect
    if state.last_run_result is None or state.last_run_result.screenshot is None:
        error_panel = Panel(
            "No screenshot available to inspect. Run a test first to capture a screenshot.",
            title="❌ No Screenshot Data",
            title_align="left",
            border_style="red",
            highlight=True,
        )
        console.print(error_panel)

        state.messages.append(
            HumanMessage(content="Error: No screenshot available to inspect. Run a test first to capture a screenshot.")
        )
        return state

    screenshot = state.last_run_result.screenshot

    try:
        # Convert PIL Image to base64 encoded string
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        buffer.seek(0)

        # Encode to base64
        screenshot_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # Create data URL for the image
        image_url = f"data:image/png;base64,{screenshot_base64}"

        # Show success message to user
        console.print()
        screenshot_panel = Panel(
            f"Screenshot captured ({screenshot.width}x{screenshot.height} pixels)\nSending to AI for analysis...",
            title="📸 Screenshot Inspection",
            title_align="left",
            border_style="green",
            highlight=True,
        )
        console.print(screenshot_panel)

        # Add screenshot to conversation context with analysis request
        state.messages.append(AIMessage(content="I need to analyze the screenshot from the test run."))

        # Create a message with the screenshot
        screenshot_message = HumanMessage(content=[{"type": "image_url", "image_url": {"url": image_url}}])

        state.messages.append(screenshot_message)

        console.print("[bold green]✅ Screenshot sent to AI for analysis[/bold green]", justify="center")

    except Exception as e:
        error_panel = Panel(
            f"Error processing screenshot: {e}",
            title="❌ Screenshot Processing Error",
            title_align="left",
            border_style="red",
            highlight=True,
        )
        console.print(error_panel)

        state.messages.append(HumanMessage(content=f"Error processing screenshot: {e}"))

    return state
