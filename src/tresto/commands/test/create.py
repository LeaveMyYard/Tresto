"""Create test command implementation."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

from tresto.core.config.main import TrestoConfig

console = Console()


def _normalize_test_path(raw: str) -> Path:
    # allow dots or slashes as separators; collapse repeated separators
    parts = [p for chunk in raw.split("/") for p in chunk.split(".") if p]
    return Path(*parts)


def create_test_command() -> None:
    """Interactively create a new test skeleton with metadata files."""

    console.print("\n[bold blue]🧪 Create a new Tresto test[/bold blue]")

    # Ensure project config exists
    cfg = TrestoConfig.load_config()
    base_dir = Path(cfg.project.test_directory)

    # 1-2. Ask for test name/path
    raw_name = Prompt.ask("Test name (use dots or slashes for subfolders)")
    rel_test_path = _normalize_test_path(raw_name)
    abs_test_path = base_dir / rel_test_path

    test_name = abs_test_path.stem
    test_module_path = (abs_test_path / "..").resolve()
    target_file_path = (test_module_path / f"test_{test_name}.py").resolve()

    if target_file_path.exists():
        console.print(f"\n[red]❌ Test already exists[/red] at [bold]{target_file_path}[/bold]")
        return

    # 3. Ask for high-level instructions
    instructions = Prompt.ask("What will this test do?")

    # Create directory structure: <test>/test.py, <test>/tresto.yaml, <test>/.tresto/
    test_module_path.mkdir(parents=True, exist_ok=True)

    # We need to place __init__.py to each subdir between the root and the test
    scan_path = test_module_path.relative_to(base_dir.resolve())
    console.print(f"Iterating [bold]{scan_path}[/bold]")
    for subdir in scan_path.parents:
        console.print(f"Creating [bold]{subdir / '__init__.py'}[/bold]")
        (Path.cwd() / base_dir / subdir / "__init__.py").touch(exist_ok=True)

    # Create test.py if not exists
    if not target_file_path.exists():
        target_file_path.touch()
        target_file_path.write_text(f"# TODO: test writing is in progress\n# {instructions}")

    console.print(
        f"\n[green]✅ Created test scaffold[/green] at [bold]{target_file_path.relative_to(Path.cwd())}[/bold]"
    )

    # 5. Recording step will be added later
    console.print("\n[dim]Next: we'll add an interactive recorder to capture the flow.[/dim]")
