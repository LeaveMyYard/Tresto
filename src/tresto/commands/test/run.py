"""Run tests command implementation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console

from tresto.core.config.main import TrestoConfig

console = Console()


def _resolve_tests_root() -> Path:
    """Resolve the directory to run tests from.

    Priority:
    - tresto.yaml -> project.test_directory
    - ./tresto/tests
    - ./tests
    - current working directory
    """
    config_path = TrestoConfig.get_config_path()
    if config_path.exists():
        try:
            cfg = TrestoConfig.load_config()
            return Path(cfg.project.test_directory).resolve()
        except typer.Exit:
            # fall back to defaults below
            pass

    cwd = Path.cwd()
    for d in (cwd / "tresto" / "tests", cwd / "tests"):
        if d.exists():
            return d.resolve()
    return cwd


def _run_via_pytest_module(target: Path) -> int | None:
    """Try running tests via pytest Python API, return exit code or None if unavailable."""
    try:
        import pytest
    except ImportError:
        return None

    try:
        return int(pytest.main([str(target) + "/tresto"]))
    except SystemExit as e:  # pytest may call sys.exit
        return int(getattr(e, "code", 1) or 0)


def _run_via_executable(target: Path) -> int | None:
    """Try running tests via a pytest executable or uv fallback; return exit code or None if not found."""
    if shutil.which("pytest"):
        return subprocess.call(["pytest", str(target)])
    if shutil.which("uv"):
        return subprocess.call(["uv", "run", "pytest", str(target)])
    return None


def run_tests_command() -> None:
    """Run all tests using pytest and show results."""
    console.print("\n[bold blue]🧪 Running tests with pytest[/bold blue]")

    target = _resolve_tests_root()
    if not target.exists():
        console.print(f"[red]No tests directory found at {target}[/red]")
        raise typer.Exit(1)

    try:
        rel = target.relative_to(Path.cwd())
        shown = rel
    except ValueError:
        shown = target
    console.print(f"📁 Test root: [bold]{shown}[/bold]")

    # Prefer Python API to avoid external dependency on executables
    code = _run_via_pytest_module(target)
    if code is None:
        code = _run_via_executable(target)

    if code is None:
        console.print("[red]pytest is not available.[/red]")
        console.print("Install it or run via uv: [bold]uv run pytest[/bold]")
        raise typer.Exit(1)

    # Exit with pytest's return code
    raise typer.Exit(code)
