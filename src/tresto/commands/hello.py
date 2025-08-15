"""Hello command for Tresto CLI - welcome message with ASCII art."""

import textwrap

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from tresto import __version__

console = Console()


def hello_command() -> None:
    """Show welcome message with ASCII art."""

    # ASCII art for Tresto
    ascii_art = textwrap.dedent("""\
        ████████╗██████╗ ███████╗███████╗████████╗ ██████╗ 
        ╚══██╔══╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔═══██╗
           ██║   ██████╔╝█████╗  ███████╗   ██║   ██║   ██║
           ██║   ██╔══██╗██╔══╝  ╚════██║   ██║   ██║   ██║
           ██║   ██║  ██║███████╗███████║   ██║   ╚██████╔╝
           ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝    ╚═════╝ 
    """).strip()

    # Create colorful title
    title = Text()
    title.append("T", style="bold red")
    title.append("R", style="bold yellow")
    title.append("E", style="bold green")
    title.append("S", style="bold blue")
    title.append("T", style="bold magenta")
    title.append("O", style="bold cyan")

    # Create the main content
    content = Text()
    content.append(ascii_art, style="bold cyan")
    content.append("\n\n")
    content.append("🤖 AI-Powered E2E Testing CLI", style="bold white")
    content.append(f" v{__version__}\n", style="bold blue")
    content.append("Create intelligent tests with AI agents that understand your testing intent,\n", style="white")
    content.append("not just your clicks. Built on Playwright with AI integration.\n\n", style="white")

    content.append("✨ Features:\n", style="bold yellow")
    content.append("  • ", style="white")
    content.append("AI-generated test scenarios", style="green")
    content.append(" from natural language descriptions\n", style="white")
    content.append("  • ", style="white")
    content.append("Smart element selectors", style="green")
    content.append(" that adapt to UI changes\n", style="white")
    content.append("  • ", style="white")
    content.append("Multi-provider AI support", style="green")
    content.append(" (Anthropic Claude, OpenAI GPT)\n", style="white")
    content.append("  • ", style="white")
    content.append("Playwright integration", style="green")
    content.append(" for robust browser automation\n\n", style="white")

    content.append("🚀 Quick Start:\n", style="bold yellow")
    content.append("  1. ", style="white")
    content.append("tresto init", style="bold cyan")
    content.append("          # Initialize your project\n", style="white")
    content.append("  2. ", style="white")
    content.append("tresto models list", style="bold cyan")
    content.append("   # See available AI models\n", style="white")
    content.append("  3. ", style="white")
    content.append("tresto record", style="bold cyan")
    content.append("        # Record AI-powered tests\n\n", style="white")

    content.append("💡 Need help? Use ", style="white")
    content.append("tresto --help", style="bold cyan")
    content.append(" or ", style="white")
    content.append("tresto [command] --help", style="bold cyan")
    content.append("\n\n", style="white")

    content.append("Made with ❤️  by developers, for developers", style="bold magenta")

    # Create a panel with the content
    panel = Panel(
        content,
        title=title,
        subtitle="[dim]The future of E2E testing is here[/dim]",
        border_style="bright_blue",
        padding=(1, 2),
    )

    console.print(panel)


if __name__ == "__main__":
    typer.run(hello_command)
