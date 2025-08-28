from __future__ import annotations

import time
from traceback import format_exc
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from .errors import BaseTestExtractionError
from .extract import extract_test_function
from .models import TestRunResult
from .screenshot import screenshot_page

if TYPE_CHECKING:
    from pathlib import Path



async def run_test(test_path: Path) -> TestRunResult:
    test_path = test_path.resolve()

    if not test_path.exists():
        return TestRunResult(
            success=False,
            duration_s=0.0,
            traceback=f"Test file not found: {test_path}",
            stdout=None,
            stderr=None,
        )

    try:
        test_func = extract_test_function(test_path)
    except BaseTestExtractionError as e:
        return TestRunResult(
            success=False,
            duration_s=0.0,
            traceback=str(e),
            stdout=None,
            stderr=None,
        )
    else:
        if test_func is None:
            return TestRunResult(
                success=False,
                duration_s=0.0,
                traceback=f"Test file found but no test function found: {test_path}",
                stdout=None,
                stderr=None,
            )
    
    success = False
    tb = None
    start = time.perf_counter()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await test_func(page)
        except Exception:  # noqa: BLE001
            success = False
            tb = format_exc(limit=20)
        finally:
            html = await page.content()
            img = await screenshot_page(page, "png")
            img.save("screenshot.png")
            await browser.close()

    duration = time.perf_counter() - start

    soup = BeautifulSoup(html, "html.parser") if html else None
    return TestRunResult(
        success=success,
        duration_s=duration,
        traceback=tb,
        stdout=None,
        stderr=None,
        soup=soup,
        screenshot=img,
    )
