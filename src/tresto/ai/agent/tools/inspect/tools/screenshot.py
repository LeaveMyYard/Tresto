from datetime import datetime

from langchain.tools import Tool, tool
from pydantic import BaseModel, Field

from tresto.ai.agent.tools.inspect.recording import RecordingManager


class ScreenshotArgs(BaseModel):
    timestamp: datetime | None = Field(None, description="Timestamp to get screenshot (UTC, optional)")


def create_bound_screenshot_tool(manager: RecordingManager) -> Tool:
    @tool(description="Get screenshot at timestamp from recording", args_schema=ScreenshotArgs)
    def screenshot(timestamp: datetime | None = None) -> str:
        """Return a short message confirming a screenshot was fetched. The image itself is handled by the caller."""
        try:
            img = manager.get_screenshot_at(timestamp)
        except ValueError as e:
            return f"❌ {e}"

        return f"📸 Screenshot available at size {img.width}x{img.height}"

    return screenshot
