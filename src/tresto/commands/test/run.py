"""Run tests command implementation."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from tresto.core.config.main import TrestoConfig
from tresto.core.test import resolve_tests_root

console = Console()


def _resolve_tests_root() -> Path:
    config_path = TrestoConfig.get_config_path()
    if config_path.exists():
        try:
            cfg = TrestoConfig.load_config()
        except typer.Exit:
            return resolve_tests_root(None)
        return resolve_tests_root(cfg)
    return resolve_tests_root(None)


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
    raise NotImplementedError("Not implemented")
    code = _run_via_pytest_module(target)
    if code is None:
        code = _run_via_executable(target)

    if code is None:
        console.print("[red]pytest is not available.[/red]")
        console.print("Install it or run via uv: [bold]uv run pytest[/bold]")
        raise typer.Exit(1)

    # Exit with pytest's return code
    raise typer.Exit(code)
