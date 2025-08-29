from __future__ import annotations

import re
import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.syntax import Syntax

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


def _strip_markdown_code_fences(text: str) -> str:
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


def _get_last_n_lines(text: str, n: int = 10) -> str:
    """Get the last n lines from text, handling both complete and partial lines."""
    if not text.strip():
        return ""

    lines = text.split("\n")
    # Take the last n lines, but ensure we don't start with empty lines
    last_lines = lines[-n:] if len(lines) >= n else lines

    # If the last line is empty and we have more than one line, remove it
    # This handles cases where the text ends with a newline
    if len(last_lines) > 1 and not last_lines[-1].strip():
        last_lines = last_lines[:-1]

    return "\n".join(last_lines)


CODE_LINES_TO_SHOW = 18


async def generate_or_update_code(state: TestAgentState) -> TestAgentState:
    llm = state.create_llm()

    generate_code_message = HumanMessage(
        textwrap.dedent(
            """\
                Now you should generate a test.
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

    # Stream the response and show real-time character count with code preview
    ai_content = ""

    console.print()  # Add spacing before streaming

    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.messages + [generate_code_message]):
            if chunk.content:
                ai_content += chunk.content

                # Strip markdown fences for preview (but keep original for final processing)
                preview_code = _strip_markdown_code_fences(ai_content)
                last_lines = _get_last_n_lines(preview_code, CODE_LINES_TO_SHOW)

                # Create syntax highlighted code
                if last_lines.strip():
                    syntax = Syntax(
                        last_lines,
                        "python",
                        theme="monokai",
                        line_numbers=False,
                        word_wrap=True,
                        background_color="default",
                    )
                else:
                    syntax = Syntax("# Generating code...", "python", theme="monokai")

                # Update the status with character count and code preview
                char_count = len(ai_content)
                total_lines = len(preview_code.split("\n")) if preview_code.strip() else 0

                panel = Panel(
                    syntax,
                    title=(
                        f"🤖 Generating Test Code ({char_count} chars, "
                        f"{total_lines} lines) [dim]last {CODE_LINES_TO_SHOW} lines:[/dim]"
                    ),
                    title_align="left",
                    border_style="blue",
                )
                live.update(panel)

    # Final status
    final_char_count = len(ai_content)
    final_code = _strip_markdown_code_fences(ai_content)
    final_lines = len(final_code.split("\n")) if final_code.strip() else 0
    console.print(
        f"✅ Test code generation completed! ({final_char_count} characters, {final_lines} lines total)",
        style="bold green",
    )

    state.current_test_code = final_code
    state.messages.append(HumanMessage(content=f"Model wrote code to {state.test_file_path}"))

    return state
