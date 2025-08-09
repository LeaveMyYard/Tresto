"""Command to list available AI connectors and models."""

from __future__ import annotations

import asyncio

from rich.console import Console
from rich.table import Table

from tresto.ai.connectors.factory import connect, get_available_connectors

console = Console()


async def _list_models_async() -> None:
    """Async implementation to list all available AI connectors and their models."""
    console.print("[bold blue]Available AI Connectors and Models[/bold blue]\n")

    # Create a single table with all connectors
    table = Table(
        show_header=True,
        header_style="bold cyan",
        row_styles=["", "dim"],
    )

    table.add_column("Connector", style="bold green")
    table.add_column("Aliases", style="dim")
    table.add_column("Description", style="white")
    table.add_column("Available Models", style="yellow")

    connector_list = list(get_available_connectors())

    for i, connector_info in enumerate(connector_list):
        # Get aliases (excluding the main name)
        aliases = [alias for alias in connector_info.aliases if alias != connector_info.name]
        aliases_str = ", ".join(aliases) if aliases else "-"

        # Create a connector instance just to get the available models list
        connector = connect(connector_info.name)
        models = await connector.get_available_models()
        models_str = "\n".join(models)

        table.add_row(connector_info.name, aliases_str, connector_info.description, models_str)

        # Add a separator row between connectors (except after the last one)
        if i < len(connector_list) - 1:
            table.add_row("", "", "", "", end_section=True)

    console.print(table)


def list_models() -> None:
    """List all available AI connectors and their models."""
    asyncio.run(_list_models_async())
