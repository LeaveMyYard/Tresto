"""Main CLI application for Tresto."""

import typer
from rich.console import Console

from . import __version__

console = Console()
app = typer.Typer(
    name="tresto",
    help="AI-powered E2E testing CLI inspired by Playwright codegen",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Show version information."""
    if value:
        console.print(f"Tresto v{__version__}")
        console.print("AI-powered E2E testing CLI")
        console.print("Made with ❤️ by developers, for developers")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version information",
    ),
) -> None:
    """
    Tresto: AI-powered E2E testing CLI.

    Create intelligent E2E tests with AI agents that understand your testing intent,
    not just your clicks. Built on Playwright with Claude AI integration.
    """


# Import and register commands after app creation to avoid circular imports
def register_commands() -> None:
    """Register CLI commands."""
    try:
        from .commands import models
        from .commands.init import init_command
        from .commands.record import record_command

        app.command("init", help="Initialize Tresto in your project")(init_command)
        app.command("record", help="Record and generate AI-powered tests")(record_command)
        app.add_typer(models.app, name="models")
    except ImportError as e:
        console.print(f"[red]Warning: Could not load all commands: {e}[/red]")


# Register commands when module is imported
register_commands()


if __name__ == "__main__":
    app()
