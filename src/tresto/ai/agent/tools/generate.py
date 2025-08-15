from __future__ import annotations

import re
import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import SystemMessage

from tresto.ai.agent.state import ThinkingStep

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState



async def generate_or_update_code(state: TestAgentState) -> TestAgentState:
    llm = state.create_llm()

    generate_code_message = SystemMessage(
        textwrap.dedent(
            """\
                Now you should generate a test.
                Write nothing else, except the code.
                The code should be a valid Playwright test written in Python.
            """
        )
    )

    ai_response = await llm.ainvoke(state.messages + [generate_code_message])

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

    state.current_test_code = _strip_markdown_code_fences(ai_response.content)
    state.messages.append(SystemMessage(content=f"Model wrote code to {state.test_file_path}"))

    return state
