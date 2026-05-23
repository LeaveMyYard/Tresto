from __future__ import annotations

import io
import time
from contextlib import redirect_stderr, redirect_stdout
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from traceback import format_exc
from typing import TYPE_CHECKING

from playwright.async_api import ViewportSize, async_playwright

from tresto.ai.agent.tools.inspect.recording import RecordingManager
from tresto.ai.agent.tools.screenshot import screenshot_page
from tresto.core.config.main import BrowserConfig

from .errors import BaseTestExtractionError
from .extract import extract_test_function
from .models import TestRunResult

if TYPE_CHECKING:
    from tresto.core.config.main import TrestoConfig


async def run_test(test_path: Path, config: TrestoConfig | None = None, artifacts_dir: Path | None = None) -> TestRunResult:
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
    img = None
    start = time.perf_counter()
    start_dt = datetime.now(UTC)
    trace_path = None
    screenshot_path = None
    browser_config = config.browser if config is not None and config.browser is not None else BrowserConfig.default()
    viewport = ViewportSize(width=browser_config.viewport.width, height=browser_config.viewport.height)

    if artifacts_dir is not None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Capture stdout and stderr during test execution
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=bool(browser_config.headless), timeout=browser_config.timeout)
                context = await browser.new_context(viewport=viewport)
                context.set_default_timeout(browser_config.timeout or 30000)
                await context.tracing.start(screenshots=True, snapshots=True, sources=False)
                page = await context.new_page()
                try:
                    await test_func(page)
                    success = True  # If we get here without exception, test passed
                except Exception:  # noqa: BLE001
                    success = False
                    tb = format_exc(limit=20)
                finally:
                    # Optional: capture a final screenshot artifact
                    await page.content()
                    img = await screenshot_page(page, "png")
                    if artifacts_dir is not None:
                        screenshot_path = artifacts_dir / "screenshot.png"
                        img.save(screenshot_path)
                    with NamedTemporaryFile(
                        prefix="tresto-trace-",
                        suffix=".zip",
                        dir=artifacts_dir,
                        delete=False,
                    ) as tmp:
                        await context.tracing.stop(path=tmp.name)
                        trace_path = Path(tmp.name)
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
    end_dt = datetime.now(UTC)
    manager = RecordingManager(
        trace_path=trace_path,
        time_range=(start_dt, end_dt) if trace_path is not None else None,
    )

    return TestRunResult(
        success=success,
        duration_s=duration,
        traceback=tb,
        stdout=stdout_content,
        stderr=stderr_content,
        artifacts_dir=artifacts_dir,
        screenshot_path=screenshot_path,
        trace_path=trace_path,
        recording=manager,
    )
