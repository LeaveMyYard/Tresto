"""End-to-end tests for `tresto models list` command."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import run_tresto_command

if TYPE_CHECKING:
    from pathlib import Path


def test_tresto_models_list_shows_connectors(e2e_test_dir: Path) -> None:
    """Test that `tresto models list` displays available connectors."""
    result = run_tresto_command(
        ["tresto", "models", "list"],
        cwd=e2e_test_dir,
        timeout=15,
    )

    assert result.returncode == 0, f"Models list should succeed. Stderr: {result.stderr}"
    assert not result.stderr, f"Should not have errors. Got stderr: {result.stderr}"
    
    stdout_lower = result.stdout.lower()
    assert "connector" in stdout_lower, f"Should show connector column. Got: {result.stdout}"
    assert "model" in stdout_lower, f"Should show model column. Got: {result.stdout}"
    assert len(result.stdout) > 100, f"Should show substantial output with table. Got: {result.stdout}"


def test_tresto_models_list_shows_test_connector(e2e_test_dir: Path) -> None:
    """Test that `tresto models list` includes the test connector."""
    result = run_tresto_command(
        ["tresto", "models", "list"],
        cwd=e2e_test_dir,
        timeout=15,
    )

    assert result.returncode == 0, f"Command should succeed. Stderr: {result.stderr}"
    assert not result.stderr, f"Should not have errors. Got stderr: {result.stderr}"
    
    stdout_lower = result.stdout.lower()
    assert "test" in stdout_lower, f"Should include test connector. Got: {result.stdout}"
    assert "mock" in stdout_lower, f"Should include mock alias. Got: {result.stdout}"


def test_tresto_models_list_shows_anthropic_connector(e2e_test_dir: Path) -> None:
    """Test that `tresto models list` includes Anthropic connector."""
    result = run_tresto_command(
        ["tresto", "models", "list"],
        cwd=e2e_test_dir,
        timeout=15,
    )

    assert result.returncode == 0, f"Command should succeed. Stderr: {result.stderr}"
    assert not result.stderr, f"Should not have errors. Got stderr: {result.stderr}"
    
    stdout_lower = result.stdout.lower()
    assert "anthropic" in stdout_lower or "claude" in stdout_lower, \
        f"Should include Anthropic/Claude connector. Got: {result.stdout}"


def test_tresto_models_list_shows_openai_connector(e2e_test_dir: Path) -> None:
    """Test that `tresto models list` includes OpenAI connector."""
    result = run_tresto_command(
        ["tresto", "models", "list"],
        cwd=e2e_test_dir,
        timeout=15,
    )

    assert result.returncode == 0, f"Command should succeed. Stderr: {result.stderr}"
    assert not result.stderr, f"Should not have errors. Got stderr: {result.stderr}"
    
    stdout_lower = result.stdout.lower()
    assert "openai" in stdout_lower or "gpt" in stdout_lower, \
        f"Should include OpenAI/GPT connector. Got: {result.stdout}"


def test_tresto_models_list_shows_all_connector_models(e2e_test_dir: Path) -> None:
    """Test that `tresto models list` shows model names for all connectors."""
    result = run_tresto_command(
        ["tresto", "models", "list"],
        cwd=e2e_test_dir,
        timeout=15,
    )

    assert result.returncode == 0, f"Command should succeed. Stderr: {result.stderr}"
    assert not result.stderr, f"Should not have errors. Got stderr: {result.stderr}"
    
    stdout_lower = result.stdout.lower()
    
    assert "test-model" in stdout_lower, f"Should show test connector models. Got: {result.stdout}"
    
    has_claude = "claude-3" in stdout_lower or "claude" in stdout_lower
    assert has_claude, f"Should show Claude models. Got: {result.stdout}"
    
    assert "gpt-5.3-codex" in stdout_lower, f"Should show Codex models through OpenAI. Got: {result.stdout}"
    has_gpt = "gpt-4" in stdout_lower or "gpt-3" in stdout_lower or "gpt-5" in stdout_lower
    assert has_gpt, f"Should show GPT/OpenAI models. Got: {result.stdout}"
