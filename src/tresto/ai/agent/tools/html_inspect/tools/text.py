from bs4 import BeautifulSoup
from langchain.tools import Tool, tool
from pydantic import BaseModel, Field

from tresto.ai.agent.tools.html_inspect.tools.core import (
    MAX_FULL_TEXT_LENGTH,
    find_element_by_css_selector,
    trim_content,
)


class TextArgs(BaseModel):
    selector: str = Field(description="CSS selector for the element (can contain spaces for descendant selectors)")


def create_bound_text_tool(soup: BeautifulSoup) -> Tool:
    @tool(description="Show text content of element", args_schema=TextArgs)
    def text(selector: str) -> str:
        """Show text content of element using CSS selector."""
        element = find_element_by_css_selector(soup, selector)

        if element is None:
            from tresto.ai.agent.tools.html_inspect.tools.core import get_navigation_suggestions
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

