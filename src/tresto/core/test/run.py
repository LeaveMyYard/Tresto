from __future__ import annotations

import io
import time
from contextlib import redirect_stderr, redirect_stdout
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

    success = False
    tb = None
    html = None
    img = None
    start = time.perf_counter()

    # Capture stdout and stderr during test execution
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(channel="chrome", headless=False)
                context = await browser.new_context()
                page = await context.new_page()
                try:
                    await test_func(page)
                    success = True  # If we get here without exception, test passed
                except Exception:  # noqa: BLE001
                    success = False
                    tb = format_exc(limit=20)
                finally:
                    html = await page.content()
                    img = await screenshot_page(page, "png")
                    img.save("screenshot.png")
                    await browser.close()
    except Exception:  # noqa: BLE001
        # Catch any outer exceptions (e.g., playwright setup failures)
        success = False
        if tb is None:  # Only set if not already set by inner exception
            tb = format_exc(limit=20)
    finally:
        # Get captured output
        stdout_content = stdout_buffer.getvalue()
        stderr_content = stderr_buffer.getvalue()

    duration = time.perf_counter() - start
    soup = BeautifulSoup(html, "html.parser") if html else None

    return TestRunResult(
        success=success,
        duration_s=duration,
        traceback=tb,
        stdout=stdout_content,
        stderr=stderr_content,
        soup=soup,
        screenshot=img,
    )
