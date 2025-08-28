from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from .extract import TestExtractionFormatError, extract_test_function
from .screenshot import screenshot_page

if TYPE_CHECKING:
    from pathlib import Path

    from PIL.Image import Image


async def run_test(test_path: Path) -> tuple[BeautifulSoup, Image]:
    test_func = extract_test_function(test_path)
    if test_func is None:
        raise TestExtractionFormatError("No test function found in the provided file")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await test_func(page)
            html = await page.content()
            img = await screenshot_page(page, "png")
            img.save("screenshot.png")
        finally:
            await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    return soup, img
