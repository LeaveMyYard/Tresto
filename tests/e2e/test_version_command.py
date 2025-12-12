"""End-to-end tests for `tresto version` command."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import run_tresto_command

if TYPE_CHECKING:
    from pathlib import Path


def test_tresto_version_shows_version(e2e_test_dir: Path) -> None:
    """Test that `tresto version` displays version information."""
    result = run_tresto_command(
        ["tresto", "version"],
        cwd=e2e_test_dir,
    )

    assert result.returncode == 0, f"Version command should succeed: {result.stderr}"
    assert "tresto" in result.stdout.lower(), "Should mention Tresto"
    assert "v" in result.stdout.lower() or "version" in result.stdout.lower()


def test_tresto_version_flag(e2e_test_dir: Path) -> None:
    """Test that `tresto --version` displays version information."""
    result = run_tresto_command(
        ["tresto", "--version"],
        cwd=e2e_test_dir,
    )

    assert result.returncode == 0, f"Version flag should succeed: {result.stderr}"
    assert "tresto" in result.stdout.lower()


def test_tresto_version_short_flag(e2e_test_dir: Path) -> None:
    """Test that `tresto -v` displays version information."""
    result = run_tresto_command(
        ["tresto", "-v"],
        cwd=e2e_test_dir,
    )

    assert result.returncode == 0, f"Short version flag should succeed: {result.stderr}"
    assert "tresto" in result.stdout.lower()

