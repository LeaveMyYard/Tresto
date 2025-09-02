from datetime import datetime

from langchain.tools import Tool, tool
from pydantic import BaseModel, Field

from tresto.ai.agent.tools.inspect.recording import RecordingManager
from tresto.ai.agent.tools.inspect.tools.core import (
    MAX_ATTR_VALUE_LENGTH,
    MAX_VIEW_LENGTH,
    find_element_by_css_selector,
    trim_content,
)


class AttrsArgs(BaseModel):
    selector: str = Field(description="CSS selector for the element (can contain spaces for descendant selectors)")
    timestamp: datetime | None = Field(None, description="Timestamp to inspect at (UTC, optional)")


def create_bound_attrs_tool(manager: RecordingManager) -> Tool:
    @tool(description="Show attributes of element", args_schema=AttrsArgs)
    def attrs(selector: str, timestamp: datetime | None = None) -> str:
        """Show attributes of element using CSS selector."""
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

        if hasattr(element, "attrs") and element.attrs:
            # Trim individual attribute values for display
            attrs_list = []
            for k, v in element.attrs.items():
                value_str = str(v)
                trimmed_value = trim_content(value_str, MAX_ATTR_VALUE_LENGTH)
                attrs_list.append(f"  {k}: {trimmed_value}")

            attrs_str = "\n".join(attrs_list)
            # Trim overall attributes display
            trimmed_attrs = trim_content(attrs_str, MAX_VIEW_LENGTH)
            return f"🏷️ Attributes of '{selector}':\n{trimmed_attrs}"
        return f"🏷️ Element '{selector}' has no attributes"

    return attrs
