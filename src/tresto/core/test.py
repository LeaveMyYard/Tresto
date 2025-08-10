from __future__ import annotations

import asyncio
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from playwright.async_api import async_playwright

if TYPE_CHECKING:
    from tresto.core.config.main import TrestoConfig


@dataclass
class TestRunResult:
    success: bool
    duration_s: float
    traceback: str | None = None
    stdout: str | None = None
    stderr: str | None = None


def ensure_test_file(path_str: str) -> Path:
    path = Path(path_str).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    for parent in list(path.parent.parents):
        init_file = parent / "__init__.py"
        if str(init_file).startswith(str(Path.cwd())) and not init_file.exists():
            try:
                init_file.touch(exist_ok=True)
            except OSError:
                pass
    return path


async def run_test_code_in_file(test_code: str, test_file_path: str) -> TestRunResult:
    test_path = ensure_test_file(test_file_path)
    if not test_code.strip():
        return TestRunResult(success=False, duration_s=0.0, traceback="No test code to run")

    try:
        test_path.write_text(test_code, encoding="utf-8")
    except OSError as exc:
        return TestRunResult(success=False, duration_s=0.0, traceback=str(exc))

    cmd = [sys.executable, "-m", "pytest", str(test_path), "-q", "--maxfail=1", "--disable-warnings"]
    start = time.perf_counter()
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out_b, err_b = await proc.communicate()
    dur = time.perf_counter() - start
    success = proc.returncode == 0
    tb = None if success else (err_b.decode() or out_b.decode())
    return TestRunResult(
        success=success,
        duration_s=dur,
        traceback=tb,
        stdout=out_b.decode(),
        stderr=err_b.decode(),
    )


async def inspect_site(config: TrestoConfig, recording_path: str | None) -> str:
    notes: list[str] = []

    async def run_recording_if_available(page: Any) -> None:
        if not recording_path:
            return
        rec_path = Path(recording_path)
        if not rec_path.exists():
            return
        src = rec_path.read_text(encoding="utf-8")
        ns: dict[str, Any] = {}
        exec(src, ns, ns)  # noqa: S102
        cand = ns.get("run") or ns.get("main")
        if callable(cand):
            try:
                await cand(page)
            except Exception as exc:  # noqa: BLE001
                notes.append(f"Recorded steps error: {exc}")

    base_url = config.project.base_url
    try:
        async with async_playwright() as pw:  # noqa: SIM117
            browser = await pw.chromium.launch(headless=config.browser.headless if config.browser else True)
            page = await (await browser.new_context()).new_page()
            if base_url:
                await page.goto(base_url)
                notes.append(f"Opened {base_url}")
            await run_recording_if_available(page)
            notes.append(f"Title: {await page.title()}")
            notes.append(f"URL: {page.url}")
            await browser.close()
    except Exception as exc:  # noqa: BLE001
        notes.append(f"Playwright inspection failed: {exc}")

    return "\n".join(notes[-50:])


# Test suite runners (used by CLI)
def resolve_tests_root(config: TrestoConfig | None = None) -> Path:
    if config is not None:
        return Path(config.project.test_directory).resolve()
    cwd = Path.cwd()
    for d in (cwd / "tresto" / "tests", cwd / "tests"):
        if d.exists():
            return d.resolve()
    return cwd


def run_tests_path_via_pytest_module(target: Path) -> int | None:
    try:
        import pytest  # noqa: PLC0415
    except ImportError:
        return None
    try:
        return int(pytest.main([str(target)]))
    except SystemExit as e:  # pytest may call sys.exit
        return int(getattr(e, "code", 1) or 0)


def run_tests_path_via_executable(target: Path) -> int | None:
    import shutil
    import subprocess

    if shutil.which("pytest"):
        return subprocess.call(["pytest", str(target)])
    if shutil.which("uv"):
        return subprocess.call(["uv", "run", "pytest", str(target)])
    return None
