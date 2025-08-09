"""Models command module."""

import typer

from .list import list_models

app = typer.Typer(help="Manage AI models and connectors")

app.command("list", help="List available AI connectors and models")(list_models)
