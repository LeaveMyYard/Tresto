"""A bunch of utilities for runtime pytest execution."""

import typer
from pydantic import ValidationError
from rich.console import Console

from tresto.core.config.main import TrestoConfig

console = Console()

try:
    __base_config = TrestoConfig.load_config()
except ValidationError as e:
    console.print("[red]Error: Could not load configuration file.[/red]")
    console.print(str(e))
    raise typer.Exit(1) from e

config = __base_config.project
secrets = __base_config.secrets


__all__ = ["config", "secrets"]
