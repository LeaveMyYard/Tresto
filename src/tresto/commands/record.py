"""Record command for Tresto CLI."""

from __future__ import annotations

import typer
from rich.console import Console

from tresto.core.config.main import TrestoConfig

console = Console()


def record_command(
    name: str | None = typer.Option(None, "--name", help="Pre-specify the test name"),
    description: str | None = typer.Option(None, "--description", help="Pre-specify what the test should do"),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
    iterations: int = typer.Option(5, "--iterations", help="Maximum AI iterations for code improvement"),
) -> None:
    """Record and generate AI-powered tests."""

    console.print("\n[bold blue]🎬 Starting Tresto Recording Session[/bold blue]")
    console.print("Let's create an intelligent E2E test together!\n")

    # Load configuration
    TrestoConfig.load_config()
