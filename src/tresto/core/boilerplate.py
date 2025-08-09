"""Boilerplate generation utilities for Tresto."""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

console = Console()


def generate_boilerplate(target_dir: Path) -> None:
    """
    Copy boilerplate content from tresto/generated to target directory.

    Args:
        target_dir: Target directory to copy boilerplate files to
        **kwargs: Additional parameters for customization

    Raises:
        FileNotFoundError: If source directory doesn't exist
        NotADirectoryError: If source path is not a directory
        PermissionError: If target directory is not writable
    """
    # Convert target_dir to Path object
    target_path = Path(target_dir).resolve()

    # Get the source directory (tresto/generated)
    # This should be relative to the tresto package
    tresto_root = Path(__file__).parent.parent
    source_path = tresto_root / "generated"

    if not source_path.exists():
        console.print(f"[red]Error: Source directory not found: {source_path}[/red]")
        raise FileNotFoundError(f"Source directory {source_path} does not exist.")

    if not source_path.is_dir():
        console.print(f"[red]Error: Source path is not a directory: {source_path}[/red]")
        raise NotADirectoryError(f"Source path {source_path} is not a directory.")

    # Create target directory if it doesn't exist
    target_path.mkdir(parents=True, exist_ok=True)

    # Copy all files and directories from source to target
    console.print(f"[blue]Copying boilerplate from {source_path} to {target_path}...[/blue]")

    copied_files = 0
    for source_item in source_path.rglob("*"):
        if source_item.is_file():
            # Calculate relative path from source root
            relative_path = source_item.relative_to(source_path)
            target_item = target_path / relative_path

            # Create parent directories if they don't exist
            target_item.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(source_item, target_item)
            copied_files += 1
            console.print(f"[dim]  Copied: {relative_path}[/dim]")

    console.print(f"[green]✅ Successfully copied {copied_files} files to {target_path}[/green]")


def list_boilerplate_files() -> list[Path]:
    """
    List all files available in the boilerplate directory.

    Returns:
        list[Path]: List of relative paths to boilerplate files
    """
    tresto_root = Path(__file__).parent.parent
    source_path = tresto_root / "generated"

    if not source_path.exists():
        return []

    return [file_path.relative_to(source_path) for file_path in source_path.rglob("*") if file_path.is_file()]


def preview_boilerplate() -> None:
    """Preview what files would be copied by generate_boilerplate."""
    files = list_boilerplate_files()

    if not files:
        console.print("[yellow]No boilerplate files found.[/yellow]")
        return

    console.print("[bold blue]Available boilerplate files:[/bold blue]")
    for file_path in sorted(files):
        console.print(f"  📄 {file_path}")

    console.print(f"\n[dim]Total: {len(files)} files[/dim]")
