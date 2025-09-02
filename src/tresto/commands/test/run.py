"""Run tests command implementation."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer
from rich.console import Console

from tresto.config import config

console = Console()



def run_tests_command(ctx: typer.Context | None = None) -> None:
    """Run all tests using pytest and show results.

    If invoked via the CLI with extra/unknown options, they are forwarded to pytest.
    """
    console.print("\n[bold blue]🧪 Running tests with pytest[/bold blue]")

    target = config.test_directory
    if not target.exists():
        console.print(f"[red]No tests directory found at {target}[/red]")
        raise typer.Exit(1)

    try:
        rel = target.relative_to(Path.cwd())
        shown = rel
    except ValueError:
        shown = target
    console.print(f"📁 Test root: [bold]{shown}[/bold]")

    # Build pytest arguments: test root + any extra CLI args
    extra_args: list[str] = list(ctx.args) if ctx is not None else []
    pytest_args: list[str] = [str(target), *extra_args]

    code: int = pytest.main(pytest_args)

    # Exit with pytest's return code
    raise typer.Exit(code)
