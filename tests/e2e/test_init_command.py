"""End-to-end test for `tresto init` command."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .utils import run_tresto_command

if TYPE_CHECKING:
    from pathlib import Path


def test_tresto_init_creates_required_files(e2e_test_dir: Path, monkeypatch: Any) -> None:
    """Test that `tresto init` creates tresto.yaml and test directory structure."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-12345")

    input_text = "\n\n\n\n\n"

    result = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        env={"ANTHROPIC_API_KEY": "test-key-12345"},
        input_text=input_text,
    )

    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}\nstdout: {result.stdout}"

    config_file = e2e_test_dir / "tresto.yaml"
    assert config_file.exists(), "tresto.yaml was not created"

    config_content = config_file.read_text(encoding="utf-8")
    assert "connector:" in config_content
    assert "model:" in config_content
    assert "project:" in config_content
    assert "name:" in config_content
    assert "url:" in config_content
    assert "test_directory:" in config_content

    test_dir = e2e_test_dir / "tresto" / "tests"
    assert test_dir.exists(), "Test directory was not created"
    assert test_dir.is_dir(), "Test directory path is not a directory"

    conftest = test_dir / "conftest.py"
    assert conftest.exists(), "conftest.py was not created in test directory"

    conftest_content = conftest.read_text(encoding="utf-8")
    assert "pytest" in conftest_content
    assert "playwright" in conftest_content or "Browser" in conftest_content


def test_tresto_init_with_defaults(e2e_test_dir: Path, monkeypatch: Any) -> None:
    """Test that `tresto init --force` uses default values successfully."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-12345")

    input_text = "\n\n\n\n\n"

    result = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        env={"ANTHROPIC_API_KEY": "test-key-12345"},
        input_text=input_text,
    )

    assert result.returncode == 0, f"Init command failed: {result.stderr}\nstdout: {result.stdout}"

    config_file = e2e_test_dir / "tresto.yaml"
    config_content = config_file.read_text(encoding="utf-8")

    assert "connector: anthropic" in config_content
    assert "claude" in config_content.lower()
    assert "./tresto/tests" in config_content or "tresto/tests" in config_content
