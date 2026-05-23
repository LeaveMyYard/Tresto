"""Tests for E2E test utilities and mocks."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from .utils import mock_playwright

if TYPE_CHECKING:
    from pathlib import Path


def test_mock_playwright_creates_executable(tmp_path: Path) -> None:
    """Test that mock_playwright creates a working executable."""
    expected_output = '''from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("http://example.com")
'''
    
    with mock_playwright(expected_output) as bin_dir:
        playwright_exe = bin_dir / "playwright"
        
        assert playwright_exe.exists(), "Mock playwright executable should be created"
        assert playwright_exe.is_file(), "Mock playwright should be a file"
        assert playwright_exe.stat().st_mode & 0o111, "Mock playwright should be executable"


def test_mock_playwright_generates_expected_output(tmp_path: Path) -> None:
    """Test that mock playwright generates the expected output file."""
    import os
    
    expected_output = '''from playwright.async_api import Page

async def test_login(page: Page):
    await page.goto("http://localhost:3000")
    await page.fill("#username", "admin")
    await page.click("button[type=submit]")
'''
    
    output_file = tmp_path / "generated_test.py"
    
    with mock_playwright(expected_output) as bin_dir:
        env = os.environ.copy()
        env["PATH"] = str(bin_dir) + ":" + env.get("PATH", "")
        
        result = subprocess.run(
            ["playwright", "codegen", "-o", str(output_file)],
            capture_output=True,
            text=True,
            env=env,
        )
        
        assert result.returncode == 0, f"Mock playwright should exit with 0. Got: {result.returncode}\nStderr: {result.stderr}"
        assert output_file.exists(), f"Output file should be created at {output_file}"
        
        generated_content = output_file.read_text(encoding="utf-8")
        assert generated_content == expected_output, f"Generated content should match expected output.\nExpected:\n{expected_output}\n\nGot:\n{generated_content}"


def test_mock_playwright_with_multiline_output(tmp_path: Path) -> None:
    """Test that mock playwright handles multiline output correctly."""
    import os
    
    expected_output = '''from playwright.async_api import Page, expect

async def test_complex_scenario(page: Page):
    """Complex test scenario with multiple actions."""
    await page.goto("https://example.com")
    await page.get_by_label("Username").fill("testuser")
    await page.get_by_label("Password").fill("secret123")
    await page.get_by_role("button", name="Sign in").click()
    
    # Wait for navigation
    await page.wait_for_url("**/dashboard")
    
    # Verify logged in
    await expect(page.get_by_text("Welcome, testuser")).to_be_visible()
'''
    
    output_file = tmp_path / "complex_test.py"
    
    with mock_playwright(expected_output) as bin_dir:
        env = os.environ.copy()
        env["PATH"] = str(bin_dir) + ":" + env.get("PATH", "")
        
        result = subprocess.run(
            ["playwright", "codegen", "-o", str(output_file)],
            capture_output=True,
            text=True,
            env=env,
        )
        
        assert result.returncode == 0
        assert output_file.exists()
        
        generated_content = output_file.read_text(encoding="utf-8")
        assert generated_content == expected_output


def test_mock_playwright_fails_without_output_flag(tmp_path: Path) -> None:
    """Test that mock playwright fails properly when -o flag is missing."""
    import os
    
    expected_output = "test content"
    
    with mock_playwright(expected_output) as bin_dir:
        env = os.environ.copy()
        env["PATH"] = str(bin_dir) + ":" + env.get("PATH", "")
        
        result = subprocess.run(
            ["playwright", "codegen"],
            capture_output=True,
            text=True,
            env=env,
        )
        
        assert result.returncode != 0, "Should fail without -o flag"
        assert "Error" in result.stderr or "error" in result.stderr.lower(), \
            f"Should have error message. Got stderr: {result.stderr}"


def test_mock_playwright_in_path_env(tmp_path: Path) -> None:
    """Test that mock playwright can be found via PATH environment variable."""
    import os
    
    expected_output = "# test output"
    output_file = tmp_path / "output.py"
    
    with mock_playwright(expected_output) as bin_dir:
        env = os.environ.copy()
        env["PATH"] = str(bin_dir) + ":" + env.get("PATH", "")
        
        result = subprocess.run(
            ["playwright", "codegen", "-o", str(output_file)],
            capture_output=True,
            text=True,
            env=env,
        )
        
        assert result.returncode == 0, f"Should find playwright in PATH. Stderr: {result.stderr}"
        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == expected_output
