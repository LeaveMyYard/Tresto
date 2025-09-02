from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Literal

from PIL import Image

if TYPE_CHECKING:
    from playwright.async_api import Page

type ScreenshotFormatType = Literal["png", "jpeg"]


async def screenshot_page(page: Page, format: ScreenshotFormatType = "png") -> Image.Image:
    screenshot_bytes = await page.screenshot(type=format)
    return Image.open(BytesIO(screenshot_bytes), formats=[format])
