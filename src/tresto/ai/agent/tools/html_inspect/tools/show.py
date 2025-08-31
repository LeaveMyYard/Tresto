from datetime import datetime

from langchain.tools import Tool, tool
from pydantic import BaseModel, Field, field_validator

from tresto.ai.agent.tools.html_inspect.tools.core import generate_collapsed_html_view
from tresto.ai.agent.tools.html_inspect.recording import RecordingManager


class ShowArgs(BaseModel):
    depth: int = Field(2, description="The depth of the HTML structure to show")
    timestamp: datetime | None = Field(None, description="Timestamp to inspect at (UTC, optional)")

    @field_validator("depth")
    def validate_depth(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Depth must be between 1 and 5")
        return v


def create_bound_show_tool(manager: RecordingManager) -> Tool:
    @tool(description="Show the HTML structure of the page", args_schema=ShowArgs)
    def show(depth: int = 2, timestamp: datetime | None = None) -> str:
        """Show the collapsed HTML structure of the page with the given depth."""
        try:
            soup = manager[timestamp].soup
        except ValueError as e:
            return f"❌ {e}"

        return generate_collapsed_html_view(soup, max_depth=depth)

    return show
