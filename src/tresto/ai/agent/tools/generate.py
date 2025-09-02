from __future__ import annotations

import re
import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from rich.console import Console, RenderableType
from rich.panel import Panel

from tresto.ai import prompts

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


def _strip_markdown_code_fences(text: str) -> str | None:
    """Extract code from markdown fenced code blocks."""
    if not text.strip():
        return ""

    # Try to extract the first fenced code block with optional language specifier
    # This pattern handles: ```python, ```py, or just ```
    pattern = re.compile(r"```\s*(?:python|py)?\s*\r?\n([\s\S]*?)\r?\n```", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    if match:
        return match.group(1).strip()

    # Fallback: handle code blocks that wrap the entire text
    stripped_text = text.strip()
    if stripped_text.startswith("```"):
        # Find the first newline after opening ```
        first_newline = stripped_text.find("\n")
        if first_newline != -1:
            # Check if it ends with ```
            if stripped_text.endswith("```"):
                # Complete code block - remove first and last lines
                lines = stripped_text.split("\n")
                if len(lines) >= 2:
                    code_lines = lines[1:-1]
                    return "\n".join(code_lines).strip()
            else:
                # Incomplete code block - check if this is a real incomplete block
                # (has substantial content after the opening ```)
                potential_code = stripped_text[first_newline + 1 :].strip()
                if potential_code and len(potential_code.split("\n")) > 1:
                    return None
                # This is likely just malformed (empty or single line), return original
                return text.strip()

    # If no code blocks found, return original text
    return text.strip()


def _validate_test_code(code: str) -> tuple[bool, str]:
    """Validate that the extracted code is a proper Playwright test."""
    if not code.strip():
        return False, "No code content found"

    # Check for test function definition
    if not re.search(r"async def test_\w+\(page:\s*Page\):", code):
        return False, "Missing required test function definition: async def test_<name>(page: Page):"

    return True, ""


class GenerateCodeDecision(BaseModel):
    """Model for deciding whether to continue editing the generated code."""

    wants_to_edit: bool = Field(description="Whether the model wants to make further edits to the code")
    reason: str = Field(description="Brief explanation of why the model wants to edit or is satisfied")

    def format(self) -> RenderableType:
        return Panel(
            self.reason,
            title="Iterating on the code" if self.wants_to_edit else "Finished iterating on the code",
            title_align="left",
            border_style="green",
        )


async def generate_or_update_code(state: TestAgentState) -> TestAgentState:
    """Generate or update test code using the agent's process method."""

    # Create agent for code generation
    agent = state.create_agent(prompts.create_test(state.config.secrets))

    retry_count = 0
    last_error = ""

    while True:
        # Generate the code
        if retry_count == 0:
            prompt = "Now you should generate a test."
        else:
            prompt = textwrap.dedent(
                f"""\
                    The previous attempt failed with error: {last_error}
                    Please try again and make sure to:
                    1. Wrap your code in ```python code blocks
                    2. Include the required import: from playwright.async_api import Page
                    3. Define a test function: async def test_<name>(page: Page):
                    4. Do not include any text outside the code block
                """
            )

        response = await agent.invoke(
            message=HumanMessage(content=prompt),
            panel_title=f"🤖 Generating Test Code (attempt {retry_count + 1}) - {{char_count}} chars",
            border_style="blue" if retry_count == 0 else "yellow",
        )

        # Try to extract code from the response
        extracted_code = _strip_markdown_code_fences(response)
        if extracted_code is None:
            last_error = "The code block format is not finished. Valid code block format requires ```"
            console.print(
                Panel(last_error, title="❌ Invalid Code Block", title_align="left", border_style="red", highlight=True)
            )
            continue

        # Validate the extracted code
        is_valid, error_message = _validate_test_code(extracted_code)

        if is_valid:
            state.current_test_code = extracted_code
            if retry_count > 0:
                console.print(f"✅ Successfully generated test code on attempt {retry_count + 1}")
        else:
            # If validation failed, prepare for retry
            last_error = error_message
            retry_count += 1

        result = await agent.structured_response(
            GenerateCodeDecision, message=HumanMessage(content="Do you want to edit the code further?")
        )

        if not result.wants_to_edit:
            break
