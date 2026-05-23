"""Mock utilities for E2E tests."""

from __future__ import annotations

import stat
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


def create_mock_playwright_script(python_executable: str, expected_output: str) -> str:
    """Create a mock playwright script with the given Python executable and expected output."""
    escaped_output = expected_output.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    
    return f'''#!{python_executable}
"""Mock playwright executable for E2E testing."""
import sys
from pathlib import Path

# Parse arguments to find output file
output_file = None
for i, arg in enumerate(sys.argv):
    if arg == "-o" and i + 1 < len(sys.argv):
        output_file = sys.argv[i + 1]
        break

if output_file:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    mock_code = """{escaped_output}"""
    
    output_path.write_text(mock_code, encoding="utf-8")
    sys.exit(0)
else:
    print("Error: No output file specified", file=sys.stderr)
    sys.exit(1)
'''


@contextmanager
def mock_playwright(expected_output: str) -> Iterator[Path]:
    """Context manager that creates a mock playwright executable with expected output.
    
    Args:
        expected_output: The code that the mock playwright should write to the output file
        
    Yields:
        Path to the directory containing the mock playwright executable (to be added to PATH)
        
    Example:
        ```python
        expected_code = '''from playwright.async_api import Page
        
        async def test_login(page: Page):
            await page.goto("http://localhost:3000")
        '''
        
        with mock_playwright(expected_code) as bin_dir:
            result = run_tresto_command(
                ["tresto", "test", "create", "--test-name", "login"],
                cwd=test_dir,
                env={"PATH": str(bin_dir) + ":"},
            )
        ```
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        bin_dir = Path(tmpdir) / "mock_bin"
        bin_dir.mkdir()
        
        playwright_script = bin_dir / "playwright"
        script_content = create_mock_playwright_script(sys.executable, expected_output)
        playwright_script.write_text(script_content, encoding="utf-8")
        
        playwright_script.chmod(playwright_script.stat().st_mode | stat.S_IEXEC)
        
        yield bin_dir
