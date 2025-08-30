"""Database management commands for Tresto."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tresto.core.config.main import TrestoConfig
from tresto.core.database import TestDatabase

console = Console()

app = typer.Typer(name="db", help="Manage test database")


@app.command()
def list_tests() -> None:
    """List all tests with stored data."""
    try:
        config = TrestoConfig.load_config()
    except typer.Exit:
        console.print("[red]Error:[/red] Could not load configuration. Run 'tresto init' first.")
        return

    tests = TestDatabase.list_all_tests(config.project.test_directory)

    if not tests:
        console.print("📂 No test data found in database")
        return

    table = Table(title="🗄️ Test Database")
    table.add_column("Test Name", style="cyan")
    table.add_column("Hash", style="dim")
    table.add_column("Data Files", style="green")

    for test in tests:
        test_db = TestDatabase(test_directory=config.project.test_directory, test_name=test["test_name"])
        data_files = test_db.list_stored_data()
        table.add_row(test["test_name"], test["test_hash"], ", ".join(data_files) if data_files else "none")

    console.print(table)


@app.command()
def show(test_name: str, data_type: str = "project_inspection") -> None:
    """Show stored data for a specific test.

    Args:
        test_name: Name of the test (e.g., 'user/auth/login')
        data_type: Type of data to show ('project_inspection', 'playwright_investigation', 'test_insights')
    """
    try:
        config = TrestoConfig.load_config()
    except typer.Exit:
        console.print("[red]Error:[/red] Could not load configuration. Run 'tresto init' first.")
        return

    test_db = TestDatabase(test_directory=config.project.test_directory, test_name=test_name)

    if data_type == "project_inspection":
        data = test_db.get_project_inspection_report()
        title = "📁 Project Inspection Report"
    elif data_type == "playwright_investigation":
        data = test_db.get_playwright_investigation()
        title = "🎭 Playwright Investigation"
    elif data_type == "test_insights":
        data = test_db.get_test_insights()
        title = "💡 Test Insights"
    else:
        console.print(
            f"[red]Error:[/red] Unknown data type '{data_type}'. Use: project_inspection, playwright_investigation, test_insights"
        )
        return

    if data:
        console.print(f"\n{title} for '{test_name}':")
        console.print("=" * 60)
        console.print(data)
    else:
        console.print(f"[yellow]No {data_type} data found for test '{test_name}'[/yellow]")


@app.command()
def clear(test_name: str, confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")) -> None:
    """Clear all stored data for a specific test."""
    try:
        config = TrestoConfig.load_config()
    except typer.Exit:
        console.print("[red]Error:[/red] Could not load configuration. Run 'tresto init' first.")
        return

    test_db = TestDatabase(test_directory=config.project.test_directory, test_name=test_name)

    if not test_db.test_data_dir.exists():
        console.print(f"[yellow]No data found for test '{test_name}'[/yellow]")
        return

    stored_files = test_db.list_stored_data()

    if not confirm:
        console.print(f"About to clear data for test '{test_name}':")
        for file in stored_files:
            console.print(f"  • {file}")

        if not typer.confirm("Are you sure?"):
            console.print("Cancelled.")
            return

    test_db.clear_test_data()
    console.print(f"[green]✅ Cleared data for test '{test_name}'[/green]")


@app.command()
def info() -> None:
    """Show database information and statistics."""
    try:
        config = TrestoConfig.load_config()
    except typer.Exit:
        console.print("[red]Error:[/red] Could not load configuration. Run 'tresto init' first.")
        return

    test_dir = Path(config.project.test_directory)
    database_dir = test_dir / ".database"

    console.print("🗄️ **Database Information**")
    console.print(f"📂 Database directory: {database_dir}")
    console.print(f"📁 Database exists: {'✅ Yes' if database_dir.exists() else '❌ No'}")

    if database_dir.exists():
        tests = TestDatabase.list_all_tests(config.project.test_directory)
        console.print(f"📊 Total tests with data: {len(tests)}")

        total_files = 0
        for test in tests:
            test_db = TestDatabase(test_directory=config.project.test_directory, test_name=test["test_name"])
            total_files += len(test_db.list_stored_data())

        console.print(f"📄 Total data files: {total_files}")

    console.print("\n💡 **Usage:**")
    console.print("  • tresto db list-tests     - List all tests with data")
    console.print("  • tresto db show <test>    - Show project inspection for test")
    console.print("  • tresto db clear <test>   - Clear data for test")


if __name__ == "__main__":
    app()
