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

    assert result.returncode == 0, f"Command should succeed. Stderr: {result.stderr}"
    assert not result.stderr, f"Should not have errors. Got stderr: {result.stderr}"
    
    stdout_lower = result.stdout.lower()
    assert "tresto" in stdout_lower, f"Should mention Tresto. Got: {result.stdout}"
    assert len(result.stdout) > 50, f"Should show substantial welcome message, not just 'tresto'. Got: {result.stdout}"


def test_tresto_no_args_shows_helpful_info(e2e_test_dir: Path) -> None:
    """Test that welcome message contains helpful information."""
    result = run_tresto_command(
        ["tresto"],
        cwd=e2e_test_dir,
    )

    assert result.returncode == 0, f"Command should succeed. Stderr: {result.stderr}"
    assert not result.stderr, f"Should not have errors. Got stderr: {result.stderr}"
    
    stdout_lower = result.stdout.lower()
    has_content = ("tresto" in stdout_lower or "welcome" in stdout_lower or 
                   "testing" in stdout_lower or "e2e" in stdout_lower)
    assert has_content, f"Should show helpful content about Tresto/testing/e2e. Got: {result.stdout}"
    assert len(result.stdout) > 50, f"Should show substantial content. Got: {result.stdout}"


def test_tresto_help_flag(e2e_test_dir: Path) -> None:
    """Test that `tresto --help` shows help information."""
    result = run_tresto_command(
        ["tresto", "--help"],
        cwd=e2e_test_dir,
    )

    assert result.returncode == 0, f"Help should succeed. Stderr: {result.stderr}"
    
    stdout_lower = result.stdout.lower()
    assert "usage" in stdout_lower or "commands" in stdout_lower, \
        f"Should show usage or commands. Got: {result.stdout}"
    assert "init" in stdout_lower, f"Should mention init command. Got: {result.stdout}"
    assert "test" in stdout_lower, f"Should mention test command. Got: {result.stdout}"

