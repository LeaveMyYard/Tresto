from datetime import datetime

from langchain.tools import Tool, tool
from pydantic import BaseModel, Field

from tresto.ai.agent.tools.inspect.recording import RecordingManager
from tresto.ai.agent.tools.inspect.tools.core import (
    MAX_FULL_TEXT_LENGTH,
    find_element_by_css_selector,
    trim_content,
)


class TextArgs(BaseModel):
    selector: str = Field(description="CSS selector for the element (can contain spaces for descendant selectors)")
    timestamp: datetime | None = Field(None, description="Timestamp to inspect at (UTC, optional)")


def create_bound_text_tool(manager: RecordingManager) -> Tool:
    @tool(description="Show text content of element", args_schema=TextArgs)
    def text(selector: str, timestamp: datetime | None = None) -> str:
        """Show text content of element using CSS selector."""
        try:
            soup = manager[timestamp].soup
        except ValueError as e:
            return f"❌ {e}"

        element = find_element_by_css_selector(soup, selector)

        if element is None:
            from tresto.ai.agent.tools.inspect.tools.core import get_navigation_suggestions

            suggestions = get_navigation_suggestions(soup, selector)
            return (
                f"❌ Could not find element with selector: {selector}\n\n"
                + f"💡 Try these selectors instead:\n{suggestions}"
            )

        text_content = element.get_text(strip=True)
        trimmed_text = trim_content(text_content, MAX_FULL_TEXT_LENGTH)

        if trimmed_text == "":
            return f"❌ Element '{selector}' has no text content"

        return f"📝 Text content of '{selector}':\n{trimmed_text}"

    return text
