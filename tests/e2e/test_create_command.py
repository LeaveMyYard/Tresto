"""End-to-end tests for `tresto test create` command."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import run_tresto_command

if TYPE_CHECKING:
    from pathlib import Path


MOCK_PLAYWRIGHT_RECORDING = '''from playwright.async_api import Page

async def test_example(page: Page):
    """Generated test code."""
    await page.goto("http://localhost:3000")
    await page.click("button")
'''


def test_tresto_test_create_requires_config(e2e_test_dir: Path) -> None:
    """Test that `tresto test create` fails without tresto.yaml."""
    result = run_tresto_command(
        ["tresto", "test", "create", "--test-name", "login.success"],
        cwd=e2e_test_dir,
        input_text="Test login functionality\n",
    )

    assert result.returncode != 0, f"Should fail without config. Got returncode: {result.returncode}"
    
    output = (result.stdout + result.stderr).lower()
    assert "tresto.yaml" in output or "config" in output, \
        f"Should mention config file. Got stdout: {result.stdout}, stderr: {result.stderr}"


def test_tresto_test_create_creates_file_structure(e2e_test_dir: Path) -> None:
    """Test that `tresto test create` creates test file with proper header."""
    input_text_init = "\n\n\ntest\n\n"
    result_init = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text_init,
    )
    assert result_init.returncode == 0, f"Init failed. Stderr: {result_init.stderr}"
    assert not result_init.stderr, f"Init should not have errors. Got stderr: {result_init.stderr}"

    test_name = "auth.login"
    test_description = "Test user login with valid credentials"

    input_text_create = f"{test_description}\n"

    run_tresto_command(
        ["tresto", "test", "create", "--test-name", test_name],
        cwd=e2e_test_dir,
        input_text=input_text_create,
        timeout=10,
    )

    test_dir = e2e_test_dir / "tresto" / "tests"
    test_file = test_dir / "auth" / "test_login.py"

    assert test_file.exists(), f"Test file should be created at {test_file}"

    content = test_file.read_text(encoding="utf-8")
    
    assert test_name in content, f"Test name '{test_name}' should be in file header"
    assert test_description in content, "Test description should be in file header"
    
    assert "test name:" in content.lower(), "Header should contain test name field"
    assert "test description:" in content.lower(), "Header should contain test description field"


def test_tresto_test_create_accepts_description_input(e2e_test_dir: Path) -> None:
    """Test that `tresto test create` accepts and stores test description."""
    input_text_init = "\n\n\ntest\n\n"
    result_init = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text_init,
    )
    assert result_init.returncode == 0, f"Init failed. Stderr: {result_init.stderr}"
    assert not result_init.stderr, f"Init should not have errors. Got stderr: {result_init.stderr}"

    test_description = "Verify user can successfully complete checkout"

    input_text_create = f"{test_description}\n"

    run_tresto_command(
        ["tresto", "test", "create", "--test-name", "checkout"],
        cwd=e2e_test_dir,
        input_text=input_text_create,
        timeout=10,
    )

    test_file = e2e_test_dir / "tresto" / "tests" / "test_checkout.py"
    assert test_file.exists(), f"Test file should be created at {test_file}"

    content = test_file.read_text(encoding="utf-8")
    assert test_description in content, "Test description should be in file header"


def test_tresto_test_create_fails_on_duplicate(e2e_test_dir: Path) -> None:
    """Test that `tresto test create` fails when test file already exists."""
    input_text_init = "\n\n\ntest\n\n"
    result_init = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text_init,
    )
    assert result_init.returncode == 0, f"Init should succeed. Stderr: {result_init.stderr}"
    assert not result_init.stderr, f"Init should not have errors. Got stderr: {result_init.stderr}"

    test_name = "duplicate_test"

    test_dir = e2e_test_dir / "tresto" / "tests"
    test_file = test_dir / f"test_{test_name}.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text('"""Existing test"""')

    input_text_create = "Test description\n"

    result = run_tresto_command(
        ["tresto", "test", "create", "--test-name", test_name],
        cwd=e2e_test_dir,
        input_text=input_text_create,
        timeout=10,
    )

    assert result.returncode != 0, f"Second create should fail. Got returncode: {result.returncode}"
    
    output = (result.stdout + result.stderr).lower()
    assert "already exists" in output or "iterate" in output, \
        f"Should mention file exists or suggest iterate. Got stdout: {result.stdout}, stderr: {result.stderr}"


def test_tresto_test_create_interactive_mode(e2e_test_dir: Path) -> None:
    """Test that `tresto test create` accepts test name interactively."""
    input_text_init = "\n\n\ntest\n\n"
    result_init = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text_init,
    )
    assert result_init.returncode == 0, f"Init failed. Stderr: {result_init.stderr}"
    assert not result_init.stderr, f"Init should not have errors. Got stderr: {result_init.stderr}"

    test_name = "interactive"
    test_description = "Test created interactively"
    input_text_create = f"{test_name}\n{test_description}\n"

    result = run_tresto_command(
        ["tresto", "test", "create"],
        cwd=e2e_test_dir,
        input_text=input_text_create,
        timeout=10,
    )

    stdout_lower = result.stdout.lower()
    assert "enter the test name" in stdout_lower or "test name" in stdout_lower, \
        f"Should prompt for test name. Got: {result.stdout}"
    assert "describe what this test should do" in stdout_lower or "test description" in stdout_lower, \
        f"Should prompt for description. Got: {result.stdout}"
    
    test_file = e2e_test_dir / "tresto" / "tests" / f"test_{test_name}.py"
    assert test_file.exists(), f"Test file should be created at {test_file}. Stderr: {result.stderr}"
    
    content = test_file.read_text(encoding="utf-8")
    assert test_name in content, f"Test name should be in file. Got: {content}"
    assert test_description in content, f"Test description should be in file. Got: {content}"

