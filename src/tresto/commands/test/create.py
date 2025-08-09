"""Create test command implementation."""

from __future__ import annotations

from pathlib import Path

import typer
from typing import Any, cast
import importlib
yaml = cast(Any, importlib.import_module("yaml"))
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

	# 1-2. Ask for test name/path
	raw_name = Prompt.ask(
		"Test name (use dots or slashes for subfolders)",
		default="sample.login.flow",
	)
	rel_test_path = _normalize_test_path(raw_name)

	# 3. Ask for high-level instructions
	instructions = Prompt.ask(
		"Brief test instructions",
		default=(
			"We want to test that the login feature works: entering an incorrect password fails, "
			"and with the correct one it passes."
		),
	)

	# 4. Compute target directory under project test_directory
	base_dir = Path(cfg.project.test_directory)
	target_dir = (base_dir / rel_test_path).resolve()

	# Create directory structure: <test>/test.py, <test>/tresto.yaml, <test>/.tresto/
	target_dir.mkdir(parents=True, exist_ok=True)
	hidden_dir = target_dir / ".tresto"
	hidden_dir.mkdir(exist_ok=True)

	# Create test.py if not exists
	test_py = target_dir / "test.py"
	if not test_py.exists():
		test_py.write_text(
			"""
# This is a placeholder for your Tresto test.
# Later, recording and AI will generate and evolve this test based on your instructions in tresto.yaml.

def test_placeholder():
	assert True
""".lstrip()
		)

	# Create tresto.yaml with metadata for this test
	tresto_yaml = target_dir / "tresto.yaml"
	if not tresto_yaml.exists():
		data = {
			"test": {
				"name": str(rel_test_path),
				"instructions": instructions,
			},
			"meta": {
				"created_with": "tresto test create",
				# room for future AI/model metadata, repair context, etc.
			},
		}
		tresto_yaml.write_text(yaml.safe_dump(data, sort_keys=False))

	console.print(
		f"\n[green]✅ Created test scaffold[/green] at [bold]{target_dir.relative_to(Path.cwd())}[/bold]"
	)
	console.print("Files:")
	console.print(f"  - {test_py.relative_to(Path.cwd())}")
	console.print(f"  - {tresto_yaml.relative_to(Path.cwd())}")
	console.print(f"  - {hidden_dir.relative_to(Path.cwd())}/")

	# 5. Recording step will be added later
	console.print("\n[dim]Next: we'll add an interactive recorder to capture the flow.[/dim]")

