"""Record command for Tresto CLI."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from typing import Optional

from ..core.config import load_config, get_api_key_for_provider, get_required_env_var_name

console = Console()


def record_command(
    name: Optional[str] = typer.Option(None, "--name", help="Pre-specify the test name"),
    description: Optional[str] = typer.Option(None, "--description", help="Pre-specify what the test should do"),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
    iterations: int = typer.Option(5, "--iterations", help="Maximum AI iterations for code improvement"),
) -> None:
    """Record and generate AI-powered tests."""
    
    console.print("\n[bold blue]🎬 Starting Tresto Recording Session[/bold blue]")
    console.print("Let's create an intelligent E2E test together!\n")
    
    # Load configuration
    config = load_config()
    
    # Check API key for the configured provider
    provider = config.ai.provider
    api_key = get_api_key_for_provider(provider)
    if not api_key:
        env_var = get_required_env_var_name(provider)
        console.print(f"[red]❌ Error:[/red] {env_var} environment variable not set.")
        console.print(f"Please set your {provider.title()} API key:")
        console.print(f"[dim]export {env_var}=your_api_key_here[/dim]")
        raise typer.Exit(1)
    
    # Get test information
    if not name:
        name = Prompt.ask("What should we call this test?", default="test_user_flow")
    
    if not description:
        description = Prompt.ask(
            "What should this test do? (Be specific about the user flow)", 
            default="Test basic user interaction flow"
        )
    
    console.print(f"\n[bold]Test Name:[/bold] {name}")
    console.print(f"[bold]Description:[/bold] {description}")
    console.print(f"[bold]Target URL:[/bold] {config.project.base_url}")
    console.print(f"[bold]AI Provider:[/bold] {config.ai.provider}")
    console.print(f"[bold]AI Model:[/bold] {config.ai.model}")
    console.print(f"[bold]Max Iterations:[/bold] {config.ai.max_iterations}")
    
    if not Confirm.ask("\nProceed with recording?"):
        console.print("[yellow]Recording cancelled.[/yellow]")
        return
    
    # For now, show a message about the feature being in development
    console.print("\n[yellow]🚧 Recording feature is currently in development![/yellow]")
    console.print("This will be implemented in the next version.")
    console.print("\n[bold]What will happen when implemented:[/bold]")
    console.print("1. 🎭 Launch Playwright browser")
    console.print("2. 📹 Record your interactions")  
    console.print("3. 🤖 AI agent analyzes and writes test code")
    console.print("4. 📝 Save optimized test to your project")
    
    console.print(f"\n[dim]Your test would be saved as: tests/e2e/{name}.py[/dim]")
    console.print("[dim]Coming soon! 🚀[/dim]")
