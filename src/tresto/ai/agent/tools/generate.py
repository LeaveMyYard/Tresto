from __future__ import annotations

import re
import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


def _strip_markdown_code_fences(text: str) -> str:
    """Extract code from markdown fenced code blocks."""
    # Try to extract the first fenced code block; prefer ```python
    pattern = re.compile(r"```\s*(?:python|py)?\s*\n([\s\S]*?)\n```", re.IGNORECASE)
    m = pattern.search(text)
    if m:
        return m.group(1).strip()
    # Fallback: remove any wrapping triple backticks without language
    pattern2 = re.compile(r"^```\s*\n?([\s\S]*?)\n?```\s*$", re.IGNORECASE)
    m2 = pattern2.match(text.strip())
    if m2:
        return m2.group(1).strip()
    return text.strip()


CODE_LINES_TO_SHOW = 18


async def generate_or_update_code(state: TestAgentState) -> TestAgentState:
    """Generate or update test code using the agent's process method."""
    
    # Create agent for code generation
    agent = state.create_agent(
        system_message=textwrap.dedent(
            """\
            You are a test code generator. Generate valid Playwright test code in Python.
            
            Write nothing else, except the code.
            
            The code should be a valid Playwright test written in Python with this exact format:
            - Import the Page type from playwright.async_api
            - Define an async function called test_<descriptive_name> that takes one parameter: page: Page
            - The function should contain the test logic using the page parameter
            
            Example format:
            ```python
            from playwright.async_api import Page
            
            async def test_login_flow(page: Page):
                await page.goto("https://example.com")
                # ... test logic here
            ```
            """
        )
    )

    # Use agent.process in code generation mode
    state.current_test_code = await agent.process(
        message=HumanMessage(content="Now you should generate a test."),
        panel_title=(
            "🤖 Generating Test Code ({char_count} chars, "
            "{total_lines} lines) [dim]last {code_lines_to_show} lines:[/dim]"
        ),
        border_style="blue",
        code_generation_mode=True,
        code_lines_to_show=CODE_LINES_TO_SHOW,
        post_process_callback=_strip_markdown_code_fences,
    )

    return state
