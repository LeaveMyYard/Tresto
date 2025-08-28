from __future__ import annotations

import time
from dataclasses import dataclass
from traceback import format_exc
from typing import TYPE_CHECKING

from tresto.core.test.run import run_test

from .utils import resolve_tests_root

if TYPE_CHECKING:
    from pathlib import Path

    from bs4 import BeautifulSoup
    from PIL.Image import Image


@dataclass
class TestRunResult:
    success: bool
    duration_s: float
    traceback: str | None = None
    stdout: str | None = None
    stderr: str | None = None

    soup: BeautifulSoup | None = None
    screenshot: Image | None = None



async def run_test_code_in_file(test_file_path: Path) -> TestRunResult:
    if not test_file_path.exists():
        return TestRunResult(success=False, duration_s=0.0, traceback="Test file not found")

    test_path = test_file_path.resolve()

    start = time.perf_counter()
    soup: BeautifulSoup | None = None
    screenshot: Image | None = None

    try:
        soup, screenshot = await run_test(test_path)
        success = True
        tb = None
    except Exception:  # noqa: BLE001
        success = False
        tb = format_exc()

    duration = time.perf_counter() - start

    return TestRunResult(
        success=success,
        duration_s=duration,
        traceback=tb,
        stdout=None,
        stderr=None,
        soup=soup,
        screenshot=screenshot,
    )



