"""End-to-end tests for `tresto version` command."""

from __future__ import annotations

import re
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

    assert result.returncode == 0, f"Version command should succeed. Stderr: {result.stderr}"
    assert not result.stderr, f"Should not have errors. Got stderr: {result.stderr}"
    
    stdout_lower = result.stdout.lower()
    assert "tresto" in stdout_lower, f"Should mention Tresto. Got: {result.stdout}"
    
    assert re.search(r"v?\d+\.\d+\.\d+", result.stdout), \
        f"Should show version number format (e.g., v1.0.0 or 1.0.0). Got: {result.stdout}"


def test_tresto_version_flag(e2e_test_dir: Path) -> None:
    """Test that `tresto --version` displays version information."""
    result = run_tresto_command(
        ["tresto", "--version"],
        cwd=e2e_test_dir,
    )

    assert result.returncode == 0, f"Version flag should succeed. Stderr: {result.stderr}"
    assert not result.stderr, f"Should not have errors. Got stderr: {result.stderr}"
    
    stdout_lower = result.stdout.lower()
    assert "tresto" in stdout_lower, f"Should mention Tresto. Got: {result.stdout}"
    assert re.search(r"v?\d+\.\d+\.\d+", result.stdout), \
        f"Should show version number. Got: {result.stdout}"


def test_tresto_version_short_flag(e2e_test_dir: Path) -> None:
    """Test that `tresto -v` displays version information."""
    result = run_tresto_command(
        ["tresto", "-v"],
        cwd=e2e_test_dir,
    )

    assert result.returncode == 0, f"Short version flag should succeed. Stderr: {result.stderr}"
    assert not result.stderr, f"Should not have errors. Got stderr: {result.stderr}"
    
    stdout_lower = result.stdout.lower()
    assert "tresto" in stdout_lower, f"Should mention Tresto. Got: {result.stdout}"
    assert re.search(r"v?\d+\.\d+\.\d+", result.stdout), \
        f"Should show version number. Got: {result.stdout}"
