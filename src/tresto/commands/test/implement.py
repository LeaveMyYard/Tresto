from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.prompt import Prompt
from typer.models import OptionInfo

from tresto.core.config.main import TrestoConfig
from tresto.core.file_header import FileHeader, TrestoFileHeaderCorrupted
from tresto.core.runner import TrestoRunner
from tresto.core.scaffold import ScaffoldWriter

if TYPE_CHECKING:
    from pathlib import Path

console = Console()


@dataclass(frozen=True)
class ScaffoldedTest:
    test_name: str
    description: str
    path: Path


def implement_scaffold_command(
    limit: int | None = typer.Option(None, "--limit", min=1, help="Maximum number of scaffolded tests to process"),
    start_at: str | None = typer.Option(None, "--start-at", help="Start at a specific Tresto test name"),
) -> None:
    limit = None if isinstance(limit, OptionInfo) else limit
    start_at = None if isinstance(start_at, OptionInfo) else start_at
    asyncio.run(_implement_scaffold_command(limit=limit, start_at=start_at))


async def _implement_scaffold_command(limit: int | None = None, start_at: str | None = None) -> None:
    config = TrestoConfig.load_config()
    tests = discover_scaffolded_tests(config)

    if start_at is not None:
        tests = _tests_starting_at(tests, start_at)
    if limit is not None:
        tests = tests[:limit]

    if not tests:
        console.print("[yellow]No scaffold-generated placeholder tests found.[/yellow]")
        return

    console.print("\n[bold blue]🧭 Implement scaffolded tests[/bold blue]")
    console.print(f"Found {len(tests)} scaffolded placeholder test(s).\n")

    for index, test in enumerate(tests, start=1):
        console.rule(f"[bold]Test {index}/{len(tests)}[/bold]")
        console.print(f"[bold]Name:[/bold] {test.test_name}")
        console.print(f"[bold]File:[/bold] {test.path}")
        console.print(f"[bold]Description:[/bold] {test.description}")

        action = Prompt.ask(
            "Action",
            choices=["record", "skip", "quit"],
            default="record",
            show_choices=True,
        )
        if action == "quit":
            console.print("[yellow]Stopped scaffold implementation.[/yellow]")
            return
        if action == "skip":
            console.print(f"[yellow]Skipped {test.test_name}[/yellow]")
            continue

        runner = TrestoRunner(config=config, test_name=test.test_name, mode="iterate")
        await runner.run()


def discover_scaffolded_tests(config: TrestoConfig) -> list[ScaffoldedTest]:
    test_root = config.project.test_directory
    if not test_root.exists():
        return []

    discovered: list[ScaffoldedTest] = []
    for path in sorted(test_root.rglob("test_*.py")):
        content = path.read_text(encoding="utf-8", errors="ignore")
        if ScaffoldWriter.SCAFFOLD_MARKER not in content:
            continue
        if "@pytest.mark.skip" not in content:
            continue
        try:
            header = FileHeader.read_from_file(path)
        except TrestoFileHeaderCorrupted:
            continue
        discovered.append(ScaffoldedTest(test_name=header.test_name, description=header.test_description, path=path))
    return discovered


def _tests_starting_at(tests: list[ScaffoldedTest], start_at: str) -> list[ScaffoldedTest]:
    for index, test in enumerate(tests):
        if test.test_name == start_at:
            return tests[index:]
    raise typer.BadParameter(f"Unknown scaffolded test: {start_at}", param_hint="--start-at")
