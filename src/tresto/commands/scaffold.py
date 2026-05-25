from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from tresto.core.config.main import ConfigLoadingError, TrestoConfig
from tresto.core.scaffold import (
    CodebaseSnapshotBuilder,
    ExistingScaffoldError,
    ScaffoldWriter,
    generate_scaffold_plan,
)

console = Console()


def scaffold_command(
    force: bool = typer.Option(False, "--force", help="Replace scaffold-generated files"),
    yes_db_cleanup: bool = typer.Option(False, "--yes-db-cleanup", help="Enable recommended app database cleanup"),
    no_db_cleanup: bool = typer.Option(False, "--no-db-cleanup", help="Disable recommended app database cleanup"),
    max_files: int = typer.Option(35, "--max-files", help="Maximum project files to send to the model"),
) -> None:
    asyncio.run(
        _scaffold_command(
            force=force,
            yes_db_cleanup=yes_db_cleanup,
            no_db_cleanup=no_db_cleanup,
            max_files=max_files,
        )
    )


async def _scaffold_command(force: bool, yes_db_cleanup: bool, no_db_cleanup: bool, max_files: int) -> None:
    force = force is True
    yes_db_cleanup = yes_db_cleanup is True
    no_db_cleanup = no_db_cleanup is True
    max_files = max_files if isinstance(max_files, int) else 35

    if yes_db_cleanup and no_db_cleanup:
        console.print("[red]Error:[/red] Use only one of --yes-db-cleanup or --no-db-cleanup.")
        raise typer.Exit(1)

    try:
        config = TrestoConfig.load_config()
    except ConfigLoadingError as e:
        console.print("[red]Error:[/red] Could not load configuration. Run 'tresto init' first.")
        raise typer.Exit(1) from e

    console.print("\n[bold blue]🧱 Scaffolding Tresto test plan[/bold blue]")
    snapshot = CodebaseSnapshotBuilder(Path.cwd(), config.project.test_directory).build(max_files=max_files)
    console.print(f"📁 Scanned project snapshot with {len(snapshot.files)} selected files")

    plan = await generate_scaffold_plan(config, snapshot)
    enable_cleanup = _resolve_db_cleanup(plan.database_cleanup.beneficial, yes_db_cleanup, no_db_cleanup)

    writer = ScaffoldWriter(config=config, plan=plan, force=force)
    try:
        result = writer.write(enable_db_cleanup=enable_cleanup)
    except ExistingScaffoldError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    console.print(f"[green]✅ Scaffold README written:[/green] {result.readme_path}")
    console.print(f"[green]✅ Planned test files created:[/green] {len(result.test_files)}")
    if result.db_cleanup_enabled:
        console.print("[green]✅ Application database cleanup hook scaffolded[/green]")
    elif plan.database_cleanup.beneficial:
        console.print("[yellow]Database cleanup was recommended but not enabled[/yellow]")


def _resolve_db_cleanup(beneficial: bool, yes_db_cleanup: bool, no_db_cleanup: bool) -> bool:
    if not beneficial:
        return False
    if yes_db_cleanup:
        return True
    if no_db_cleanup:
        return False
    return Confirm.ask("The model recommends cleaning app data between tests. Enable the pytest cleanup hook?")
