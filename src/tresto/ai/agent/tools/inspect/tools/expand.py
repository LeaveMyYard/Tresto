from datetime import datetime

from langchain.tools import Tool, tool
from pydantic import BaseModel, Field, field_validator

from tresto.ai.agent.tools.inspect.recording import RecordingManager
from tresto.ai.agent.tools.inspect.tools.core import (
    MAX_VIEW_LENGTH,
    find_element_by_css_selector,
    format_element_collapsed,
    trim_content,
)
from tresto.utils.repetition import collapse_repeated_blocks, collapse_repeated_lines


class ExpandArgs(BaseModel):
    selector: str = Field(
        description="CSS selector for the element to expand (can contain spaces for descendant selectors)"
    )
    depth: int = Field(3, description="Maximum depth to show (default: 3)")
    timestamp: datetime | None = Field(None, description="Timestamp to inspect at (UTC, optional)")

    @field_validator("depth")
    def validate_depth(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Depth must be between 1 and 5")
        return v


def create_bound_expand_tool(manager: RecordingManager) -> Tool:
    @tool(description="Expand specific element using CSS selector", args_schema=ExpandArgs)
    def expand(selector: str, depth: int = 3, timestamp: datetime | None = None) -> str:
        """Expand specific element using CSS selector with specified depth."""
        # Validate depth
        if depth < 1 or depth > 5:
            return "❌ Depth must be between 1 and 5"

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

        view = format_element_collapsed(element, 0, max_depth=depth)
        # Collapse extremely repetitive lines/blocks to avoid drowning the model
        view = collapse_repeated_blocks(view, block_tokens={"📂 <style>", '📜 "HEAD"', "📂 <script>"}, min_repeat=10)
        view = collapse_repeated_lines(view, min_repeat=20)
        trimmed_view = trim_content(view, MAX_VIEW_LENGTH)
        return (
            f"📂 Expanded view of '{selector}' ({depth} levels):\n\n{trimmed_view}\n"
            + "💡 Use more specific selectors or try exploring children shown above"
        )

    return expand
