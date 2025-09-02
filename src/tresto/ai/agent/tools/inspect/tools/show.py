from datetime import datetime

from langchain.tools import Tool, tool
from pydantic import BaseModel, Field, field_validator

from tresto.ai.agent.tools.inspect.recording import RecordingManager
from tresto.ai.agent.tools.inspect.tools.core import generate_collapsed_html_view
from tresto.utils.repetition import collapse_repeated_blocks, collapse_repeated_lines


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

        view = generate_collapsed_html_view(soup, max_depth=depth)
        # Collapse extremely repetitive lines/blocks to avoid drowning the model
        view = collapse_repeated_blocks(view, block_tokens={"📂 <style>", '📜 "HEAD"', "📂 <script>"}, min_repeat=10)
        return collapse_repeated_lines(view, min_repeat=20)

    return show
