"""End-to-end tests for `tresto` command (no arguments)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import run_tresto_command

if TYPE_CHECKING:
    from pathlib import Path


def test_tresto_no_args_shows_welcome(e2e_test_dir: Path) -> None:
    """Test that `tresto` without arguments shows welcome message."""
    result = run_tresto_command(
        ["tresto"],
        cwd=e2e_test_dir,
    )

    assert result.returncode == 0, f"Command should succeed: {result.stderr}"
    assert "tresto" in result.stdout.lower(), "Should mention Tresto"


def test_tresto_no_args_shows_helpful_info(e2e_test_dir: Path) -> None:
    """Test that welcome message contains helpful information."""
    result = run_tresto_command(
        ["tresto"],
        cwd=e2e_test_dir,
    )

    assert result.returncode == 0
    
    stdout_lower = result.stdout.lower()
    assert "tresto" in stdout_lower or "welcome" in stdout_lower or "testing" in stdout_lower


def test_tresto_help_flag(e2e_test_dir: Path) -> None:
    """Test that `tresto --help` shows help information."""
    result = run_tresto_command(
        ["tresto", "--help"],
        cwd=e2e_test_dir,
    )

    assert result.returncode == 0, f"Help should succeed: {result.stderr}"
    assert "usage" in result.stdout.lower() or "commands" in result.stdout.lower()
    assert "init" in result.stdout.lower(), "Should mention init command"

