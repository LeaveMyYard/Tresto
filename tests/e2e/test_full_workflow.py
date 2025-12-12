"""End-to-end test for full workflow with mocked Playwright."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from .utils import mock_playwright, run_tresto_command

if TYPE_CHECKING:
    pass


MOCK_PLAYWRIGHT_RECORDING = '''from playwright.async_api import Page

async def test_login(page: Page):
    """Test user login functionality."""
    await page.goto("http://localhost:3000")
    await page.get_by_label("Username").fill("testuser")
    await page.get_by_label("Password").fill("password123")
    await page.get_by_role("button", name="Login").click()
    await page.wait_for_url("**/dashboard")
'''


def test_full_workflow_with_mocked_playwright(e2e_test_dir: Path) -> None:
    """Test full workflow: init -> test create with mocked Playwright -> verify files."""
    input_text_init = "\n\n\ntest\n\n"
    result_init = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text_init,
    )
    assert result_init.returncode == 0, f"Init failed. Stderr: {result_init.stderr}"
    assert not result_init.stderr, f"Init should not have errors. Got: {result_init.stderr}"

    test_name = "login.success"
    test_description = "Test user login with valid credentials"
    input_text_create = f"{test_description}\n"

    with mock_playwright(MOCK_PLAYWRIGHT_RECORDING) as bin_dir:
        result_create = run_tresto_command(
            ["tresto", "test", "create", "--test-name", test_name],
            cwd=e2e_test_dir,
            input_text=input_text_create,
            env={"PATH": str(bin_dir) + ":"},
            timeout=30,
        )

    test_file = e2e_test_dir / "tresto" / "tests" / "login" / "test_success.py"
    recording_file = e2e_test_dir / "tresto" / "tests" / ".recordings" / "login" / "recording_success.py"

    assert test_file.exists(), f"Test file should be created at {test_file}"
    test_content = test_file.read_text(encoding="utf-8")

    assert test_name in test_content, "Test file should contain test name in header"
    assert test_description in test_content, "Test file should contain test description"
    assert "test name:" in test_content.lower(), "Should have test name field"
    assert "test description:" in test_content.lower(), "Should have test description field"

    assert recording_file.exists(), f"Recording file should be created at {recording_file}"
    recording_content = recording_file.read_text(encoding="utf-8")
    assert "async def test_login" in recording_content, "Recording should contain the mock Playwright code"
    assert 'await page.goto("http://localhost:3000")' in recording_content


def test_full_workflow_generates_test_code(e2e_test_dir: Path) -> None:
    """Test that the full workflow generates actual test code via AI."""
    input_text_init = "\n\n\ntest\n\n"
    result_init = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text_init,
    )
    assert result_init.returncode == 0
    assert not result_init.stderr

    test_name = "checkout.complete"
    test_description = "Verify user can complete checkout process"
    input_text_create = f"{test_description}\n"

    with mock_playwright(MOCK_PLAYWRIGHT_RECORDING) as bin_dir:
        result_create = run_tresto_command(
            ["tresto", "test", "create", "--test-name", test_name],
            cwd=e2e_test_dir,
            input_text=input_text_create,
            env={"PATH": str(bin_dir) + ":"},
            timeout=30,
        )

    test_file = e2e_test_dir / "tresto" / "tests" / "checkout" / "test_complete.py"
    assert test_file.exists(), f"Test file should be created. Stderr: {result_create.stderr}"

    content = test_file.read_text(encoding="utf-8")

    assert test_name in content, "Test file should contain test name"
    assert test_description in content, "Test file should contain test description"
    
    recording_file = e2e_test_dir / "tresto" / "tests" / ".recordings" / "checkout" / "recording_complete.py"
    assert recording_file.exists(), "Recording file should be created"
    
    recording_content = recording_file.read_text(encoding="utf-8")
    assert "from playwright.async_api import Page" in recording_content, "Recording should have Playwright imports"
    assert "async def test_" in recording_content, "Recording should have test function"


def test_workflow_with_nested_test_path(e2e_test_dir: Path) -> None:
    """Test workflow with deeply nested test path."""
    input_text_init = "\n\n\ntest\n\n"
    result_init = run_tresto_command(
        ["tresto", "init", "--force"],
        cwd=e2e_test_dir,
        input_text=input_text_init,
    )
    assert result_init.returncode == 0
    assert not result_init.stderr

    test_name = "auth.api.oauth.google"
    test_description = "Test Google OAuth authentication flow"
    input_text_create = f"{test_description}\n"

    with mock_playwright(MOCK_PLAYWRIGHT_RECORDING) as bin_dir:
        result_create = run_tresto_command(
            ["tresto", "test", "create", "--test-name", test_name],
            cwd=e2e_test_dir,
            input_text=input_text_create,
            env={"PATH": str(bin_dir) + ":"},
            timeout=30,
        )

    test_file = e2e_test_dir / "tresto" / "tests" / "auth" / "api" / "oauth" / "test_google.py"
    assert test_file.exists(), f"Nested test file should be created at {test_file}"

    for parent_dir in ["auth", "auth/api", "auth/api/oauth"]:
        init_file = e2e_test_dir / "tresto" / "tests" / parent_dir / "__init__.py"
        assert init_file.exists(), f"__init__.py should be created in {parent_dir}"

    content = test_file.read_text(encoding="utf-8")
    assert test_name in content
    assert test_description in content

