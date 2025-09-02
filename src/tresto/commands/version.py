import typer
from rich.console import Console

from tresto import __version__ as tresto_version

console = Console()



def version_command() -> None:
    """Print version of Tresto."""

    console.print(f"[bold]Tresto: v{tresto_version}[/bold]")


if __name__ == "__main__":
    typer.run(version_command)
