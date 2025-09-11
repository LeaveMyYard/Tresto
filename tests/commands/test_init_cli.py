"""Non-interactive test for `tresto init` using direct function call.

We patch Prompt.ask to feed defaults so the command runs without user input.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import tresto.commands.init as init_mod


def test_tresto_init_creates_config_and_boilerplate(tmp_path: Path, monkeypatch: Any) -> None:
    """Run `tresto init` non-interactively and verify outputs."""

    # Run inside a clean temp cwd
    monkeypatch.chdir(tmp_path)

    # Import sources without installation, then import the command
    project_root: Path = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root / "src"))

    # Feed defaults to all prompts
    def _answer_default(_message: str, *, default: str | None = None, choices: list[str] | None = None) -> str:  # noqa: ARG001
        assert default is not None
        return default

    with patch("rich.prompt.Prompt.ask", side_effect=_answer_default):
        init_mod.init_command(force=True)

    # Config file is written
    config_path = tmp_path / "tresto.yaml"
    assert config_path.exists(), "tresto.yaml was not created"

    content = config_path.read_text(encoding="utf-8")
    # Connector and default model should be saved
    assert "connector: anthropic" in content
    assert "model: claude-3-5-sonnet-20241022" in content

    # Boilerplate copied into default test directory
    tests_dir = tmp_path / "tresto" / "tests"
    assert tests_dir.exists(), "Test directory was not created"
    # Expect at least conftest.py copied from tresto/generated
    assert (tests_dir / "conftest.py").exists()
