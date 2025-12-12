"""End-to-end test for `tresto init` command."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from .utils import run_tresto_command

if TYPE_CHECKING:
    from pathlib import Path


def test_tresto_init_creates_required_files(e2e_test_dir: Path, monkeypatch: Any) -> None:
    """Test that `tresto init` creates tresto.yaml and test directory structure."""
    input_text = "\n\n\ntest\n\n"

    result = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
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
    input_text = "\n\n\ntest\n\n"

    result = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text,
    )

    assert result.returncode == 0, f"Init command failed: {result.stderr}\nstdout: {result.stdout}"

    config_file = e2e_test_dir / "tresto.yaml"
    config_content = config_file.read_text(encoding="utf-8")

    assert "connector: test" in config_content
    assert "test-model" in config_content.lower()
    assert "./tresto/tests" in config_content or "tresto/tests" in config_content


@pytest.mark.parametrize(
    ("project_name", "base_url", "test_directory"),
    [
        ("my-test-app", "http://localhost:3000", "./tresto/tests"),
        ("custom_project", "http://localhost:8080", "./tests/e2e"),
        ("Another-App", "https://example.com", "./custom/test/dir"),
        ("app123", "http://127.0.0.1:5000", "./playwright_tests"),
    ],
)
def test_tresto_init_with_custom_project_settings(
    e2e_test_dir: Path,
    monkeypatch: Any,
    project_name: str,
    base_url: str,
    test_directory: str,
) -> None:
    """Test that `tresto init` correctly saves custom project settings."""
    input_text = f"{project_name}\n{base_url}\n{test_directory}\ntest\n\n"

    result = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text,
    )

    assert result.returncode == 0, f"Init failed: {result.stderr}\nstdout: {result.stdout}"

    config_file = e2e_test_dir / "tresto.yaml"
    config_content = config_file.read_text(encoding="utf-8")

    assert f"name: {project_name}" in config_content
    assert f"url: {base_url}" in config_content
    assert test_directory.lstrip("./") in config_content

    test_dir = e2e_test_dir / test_directory.lstrip("./")
    assert test_dir.exists(), f"Test directory {test_directory} was not created"
    assert (test_dir / "conftest.py").exists()


@pytest.mark.parametrize(
    ("connector", "expected_model_prefix"),
    [
        ("test", "test"),
        ("mock", "test"),
    ],
)
def test_tresto_init_with_different_connectors(
    e2e_test_dir: Path,
    monkeypatch: Any,
    connector: str,
    expected_model_prefix: str,
) -> None:
    """Test that `tresto init` works with different AI connectors."""
    input_text = f"\n\n\n{connector}\n\n"

    result = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text,
    )

    assert result.returncode == 0, f"Init failed: {result.stderr}\nstdout: {result.stdout}"

    config_file = e2e_test_dir / "tresto.yaml"
    config_content = config_file.read_text(encoding="utf-8")

    assert "connector:" in config_content
    assert expected_model_prefix in config_content.lower()


@pytest.mark.parametrize(
    "test_directory",
    [
        "./tests",
        "./e2e_tests",
        "./playwright/tests",
        "./integration_tests",
    ],
)
def test_tresto_init_creates_nested_directories(
    e2e_test_dir: Path,
    monkeypatch: Any,
    test_directory: str,
) -> None:
    """Test that `tresto init` creates nested test directories correctly."""
    input_text = f"\n\n{test_directory}\ntest\n\n"

    result = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text,
    )

    assert result.returncode == 0, f"Init failed: {result.stderr}\nstdout: {result.stdout}"

    test_dir = e2e_test_dir / test_directory.lstrip("./")
    assert test_dir.exists(), f"Directory {test_directory} was not created"
    assert test_dir.is_dir()

    conftest = test_dir / "conftest.py"
    assert conftest.exists(), f"conftest.py not found in {test_directory}"

    conftest_content = conftest.read_text(encoding="utf-8")
    assert "pytest" in conftest_content
    assert "Browser" in conftest_content or "playwright" in conftest_content


def test_tresto_init_overwrite_with_force(
    e2e_test_dir: Path,
    monkeypatch: Any,
) -> None:
    """Test that `tresto init --force` overwrites existing config."""
    input_text = "\n\n\ntest\n\n"

    result1 = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text,
    )

    assert result1.returncode == 0

    config_file = e2e_test_dir / "tresto.yaml"
    original_content = config_file.read_text(encoding="utf-8")

    input_text2 = "different-project\nhttp://localhost:9999\n./other/tests\ntest\n\n"

    result2 = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text2,
    )

    assert result2.returncode == 0

    new_content = config_file.read_text(encoding="utf-8")
    assert new_content != original_content
    assert "name: different-project" in new_content
    assert "url: http://localhost:9999" in new_content
    assert "other/tests" in new_content


def test_tresto_init_without_force_aborts_on_existing_config(
    e2e_test_dir: Path,
    monkeypatch: Any,
) -> None:
    """Test that `tresto init` without --force aborts when user declines overwrite."""
    input_text = "\n\n\ntest\n\n"

    result1 = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text,
    )

    assert result1.returncode == 0

    config_file = e2e_test_dir / "tresto.yaml"
    original_content = config_file.read_text(encoding="utf-8")

    trestorc_file = e2e_test_dir / ".trestorc"
    trestorc_file.write_text(original_content, encoding="utf-8")

    input_text_decline = "n\n"

    result2 = run_tresto_command(
        ["tresto", "init"],
        cwd=e2e_test_dir,
        input_text=input_text_decline,
    )

    assert "cancelled" in result2.stdout.lower(), "Expected cancellation message"

    new_content = config_file.read_text(encoding="utf-8")
    assert new_content == original_content, "Config should not have changed"


def test_tresto_init_without_force_succeeds_on_confirmation(
    e2e_test_dir: Path,
    monkeypatch: Any,
) -> None:
    """Test that `tresto init` without --force succeeds when user confirms overwrite."""
    input_text = "\n\n\ntest\n\n"

    result1 = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text,
    )

    assert result1.returncode == 0

    config_file = e2e_test_dir / "tresto.yaml"
    original_content = config_file.read_text(encoding="utf-8")

    trestorc_file = e2e_test_dir / ".trestorc"
    trestorc_file.write_text(original_content, encoding="utf-8")

    input_text_accept = "y\ndifferent-project\nhttp://localhost:9999\n./other/tests\ntest\n\n"

    result2 = run_tresto_command(
        ["tresto", "init"],
        cwd=e2e_test_dir,
        input_text=input_text_accept,
    )

    assert result2.returncode == 0, f"Init should succeed with confirmation: {result2.stderr}\nstdout: {result2.stdout}"

    new_content = config_file.read_text(encoding="utf-8")
    assert new_content != original_content, "Config should have changed"
    assert "name: different-project" in new_content
    assert "url: http://localhost:9999" in new_content
