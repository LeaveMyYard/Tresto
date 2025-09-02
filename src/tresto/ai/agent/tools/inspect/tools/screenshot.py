import base64
from datetime import datetime
from io import BytesIO

from langchain.tools import Tool, tool
from pydantic import BaseModel, Field

from tresto.ai.agent.tools.inspect.recording import RecordingManager


class ScreenshotArgs(BaseModel):
    timestamp: datetime | None = Field(None, description="Timestamp to get screenshot (UTC, optional)")


def create_bound_screenshot_tool(manager: RecordingManager) -> Tool:
    @tool(description="Get screenshot at timestamp from recording", args_schema=ScreenshotArgs)
    def screenshot(timestamp: datetime | None = None) -> str | list[dict[str, str]]:
        """Return a short message confirming a screenshot was fetched. The image itself is handled by the caller."""
        try:
            image = manager.get_screenshot_at(timestamp)
        except ValueError as e:
            return f"❌ {e}"
        else:

            byte_stream = BytesIO()
            image.save(byte_stream, format="png")

            return [
                {
                    "type": "image",
                    "source_type": "base64",
                    "mime_type": "image/png",
                    "data": base64.b64encode(byte_stream.getvalue()).decode("utf-8"),
                }
            ]
        
    return screenshot
