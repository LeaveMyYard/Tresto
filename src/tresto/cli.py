"""Main CLI application for Tresto."""

import typer
from rich.console import Console

from . import __version__
from .commands import models
from .commands import test as test_commands
from .commands.db import app as db_app
from .commands.hello import hello_command
from .commands.init import init_command
from .commands.version import version_command

console = Console()
app = typer.Typer(
    name="tresto",
    help="AI-powered E2E testing CLI inspired by Playwright codegen",
    add_completion=False,
    pretty_exceptions_show_locals=False,
)


def version_callback(value: bool) -> None:
    """Show version information."""
    if value:
        console.print(f"Tresto v{__version__}")
        console.print("AI-powered E2E testing CLI")
        console.print("Made with ❤️ by developers, for developers")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
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
    if ctx.invoked_subcommand is None:
        hello_command()


# Import and register commands after app creation to avoid circular imports
def register_commands() -> None:
    """Register CLI commands."""
    app.command("init", help="Initialize Tresto in your project")(init_command)
    app.add_typer(models.app, name="models")
    app.add_typer(test_commands.app, name="test")
    app.add_typer(db_app, name="db")
    app.command("version", help="Show versions of tresto, Playwright, and pytest")(version_command)


# Register commands when module is imported
register_commands()


if __name__ == "__main__":
    app()
