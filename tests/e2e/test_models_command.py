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

    assert result.returncode == 0, f"Models list should succeed: {result.stderr}"
    
    stdout_lower = result.stdout.lower()
    assert "connector" in stdout_lower or "model" in stdout_lower, "Should show connector information"


def test_tresto_models_list_shows_test_connector(e2e_test_dir: Path) -> None:
    """Test that `tresto models list` includes the test connector."""
    result = run_tresto_command(
        ["tresto", "models", "list"],
        cwd=e2e_test_dir,
        timeout=15,
    )

    assert result.returncode == 0
    
    stdout_lower = result.stdout.lower()
    assert "test" in stdout_lower, "Should include test connector"
    assert "mock" in stdout_lower, "Should include mock alias"


def test_tresto_models_list_shows_anthropic_connector(e2e_test_dir: Path) -> None:
    """Test that `tresto models list` includes Anthropic connector."""
    result = run_tresto_command(
        ["tresto", "models", "list"],
        cwd=e2e_test_dir,
        timeout=15,
    )

    assert result.returncode == 0
    
    stdout_lower = result.stdout.lower()
    assert "anthropic" in stdout_lower or "claude" in stdout_lower, "Should include Anthropic/Claude"


def test_tresto_models_list_shows_openai_connector(e2e_test_dir: Path) -> None:
    """Test that `tresto models list` includes OpenAI connector."""
    result = run_tresto_command(
        ["tresto", "models", "list"],
        cwd=e2e_test_dir,
        timeout=15,
    )

    assert result.returncode == 0
    
    stdout_lower = result.stdout.lower()
    assert "openai" in stdout_lower or "gpt" in stdout_lower, "Should include OpenAI/GPT"


def test_tresto_models_list_shows_available_models(e2e_test_dir: Path) -> None:
    """Test that `tresto models list` shows model names for each connector."""
    result = run_tresto_command(
        ["tresto", "models", "list"],
        cwd=e2e_test_dir,
        timeout=15,
    )

    assert result.returncode == 0
    
    stdout_lower = result.stdout.lower()
    assert "test-model" in stdout_lower, "Should show test connector models"

