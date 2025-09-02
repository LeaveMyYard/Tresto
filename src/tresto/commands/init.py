"""Init command for Tresto CLI."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from tresto.ai.connectors import connect, get_available_connectors
from tresto.core.boilerplate import generate_boilerplate
from tresto.core.config.main import AIConfig, ProjectConfig, TrestoConfig

console = Console()


def init_command(
    force: bool = typer.Option(False, "--force", help="Overwrite existing configuration"),
    template: str = typer.Option("default", "--template", help="Template to use (default, react, vue, etc.)"),
) -> None:
    """Initialize Tresto in your project."""

    asyncio.run(_init_command(force, template))


async def _init_command(force: bool, template: str) -> None:
    console.print("\n[bold blue]🎭 Welcome to Tresto![/bold blue]")
    console.print("Let's set up AI-powered E2E testing for your project.\n")

    # Check if .trestorc already exists
    config_path = Path.cwd() / ".trestorc"
    if config_path.exists() and not force:
        if not Confirm.ask("Configuration file already exists. Overwrite?"):
            console.print("[yellow]Initialization cancelled.[/yellow]")
            return

    # Gather project information
    project_name = Prompt.ask("Project name", default=Path.cwd().name)

    base_url = Prompt.ask("Base URL for testing", default="http://localhost:3000")

    test_directory = Prompt.ask("Test directory", default="./tresto/tests")

    all_connectors = [alias for c in get_available_connectors() for alias in c.aliases]
    selected_connector_name = Prompt.ask(
        "AI provider",
        default="anthropic",
        choices=all_connectors,
    )

    selected_connector = connect(selected_connector_name)

    available_models = list(await selected_connector.get_available_models())
    assert len(available_models) > 0, "No models available for the selected provider."

    selected_model = Prompt.ask(
        "AI model",
        default=available_models[0],
        choices=available_models,
    )

    # Create configuration
    config = TrestoConfig(
        project=ProjectConfig(
            name=project_name,
            url=base_url,
            test_directory=test_directory,
        ),
        ai=AIConfig(
            connector=selected_model,
            model=selected_model,
        ),
    )

    # Save configuration
    config_path = config.save()

    # Create test directory structure
    test_dir = Path(test_directory)
    test_dir.mkdir(exist_ok=True, parents=True)

    # Generate boilerplate code
    generate_boilerplate(test_dir)

    # Success message
    console.print("\n[green]✅ Tresto initialization complete![/green]\n")
    console.print(f"📁 Created test directory: [bold]{test_directory}[/bold]")
    console.print(f"⚙️  Created configuration: [bold]{config_path.relative_to(Path.cwd())}[/bold]")

    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Set your [bold]ANTHROPIC_API_KEY[/bold] environment variable")
    console.print("2. Run [bold]tresto record[/bold] to create your first AI-powered test")
    console.print("3. Install Playwright browsers: [bold]playwright install[/bold]")

    console.print("\n[dim]Happy testing! 🚀[/dim]")
