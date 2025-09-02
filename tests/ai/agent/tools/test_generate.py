from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tresto.ai.agent.tools.generate import (
    MAX_RETRIES,
    _strip_markdown_code_fences,
    _validate_test_code,
    generate_or_update_code,
)


class TestStripMarkdownCodeFences:
    """Tests for the _strip_markdown_code_fences function."""

    def test_extract_python_code_block(self):
        """Test extracting code from ```python blocks."""
        text = """Here's some code:
```python
from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("https://example.com")
```
That's the code."""

        expected = """from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("https://example.com")"""

        result = _strip_markdown_code_fences(text)
        assert result == expected

    def test_extract_py_code_block(self):
        """Test extracting code from ```py blocks."""
        text = """```py
from playwright.async_api import Page
async def test_example(page: Page):
    pass
```"""

        expected = """from playwright.async_api import Page
async def test_example(page: Page):
    pass"""

        result = _strip_markdown_code_fences(text)
        assert result == expected

    def test_extract_generic_code_block(self):
        """Test extracting code from generic ``` blocks."""
        text = """```
from playwright.async_api import Page
async def test_example(page: Page):
    pass
```"""

        expected = """from playwright.async_api import Page
async def test_example(page: Page):
    pass"""

        result = _strip_markdown_code_fences(text)
        assert result == expected

    def test_extract_code_with_whitespace(self):
        """Test extracting code with various whitespace patterns."""
        text = """```python

from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("https://example.com")

```"""

        expected = """from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("https://example.com")"""

        result = _strip_markdown_code_fences(text)
        assert result == expected

    def test_no_code_block_returns_original(self):
        """Test that text without code blocks returns original text stripped."""
        text = """from playwright.async_api import Page
async def test_example(page: Page):
    pass"""

        result = _strip_markdown_code_fences(text)
        assert result == text.strip()

    def test_multiple_code_blocks_returns_first(self):
        """Test that multiple code blocks returns the first one."""
        text = """```python
first_code_block = True
```

Some text

```python
second_code_block = True
```"""

        result = _strip_markdown_code_fences(text)
        assert result == "first_code_block = True"

    def test_empty_code_block(self):
        """Test handling of empty code blocks."""
        text = """```python
```"""

        result = _strip_markdown_code_fences(text)
        assert result == ""

    def test_malformed_code_blocks(self):
        """Test handling of malformed code blocks."""
        # Missing closing fence - this is now treated as incomplete code block
        text = """```python
from playwright.async_api import Page
async def test_example(page: Page):
    pass"""

        result = _strip_markdown_code_fences(text)
        # Should extract the code without the opening ```python line
        expected = """from playwright.async_api import Page
async def test_example(page: Page):
    pass"""
        assert result == expected

    def test_nested_backticks_in_code(self):
        """Test code blocks containing backticks."""
        text = """```python
def test_example():
    code = "```python\\nprint('hello')\\n```"
    return code
```"""

        expected = """def test_example():
    code = "```python\\nprint('hello')\\n```"
    return code"""

        result = _strip_markdown_code_fences(text)
        assert result == expected

    def test_code_block_with_windows_line_endings(self):
        """Test code blocks with Windows-style line endings."""
        text = "```python\r\nfrom playwright.async_api import Page\r\n\r\nasync def test_example(page: Page):\r\n    pass\r\n```"

        expected = "from playwright.async_api import Page\r\n\r\nasync def test_example(page: Page):\r\n    pass"

        result = _strip_markdown_code_fences(text)
        assert result == expected

    def test_code_block_entire_text(self):
        """Test when the entire text is wrapped in code blocks."""
        text = """```python
from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("https://example.com")
```"""

        expected = """from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("https://example.com")"""

        result = _strip_markdown_code_fences(text)
        assert result == expected

    def test_code_block_with_extra_backticks(self):
        """Test handling of blocks with 4 backticks (should still extract code)."""
        text = """````python
from playwright.async_api import Page

async def test_example(page: Page):
    pass
````"""

        # Our function handles this by the fallback logic, extracts the code
        expected = """from playwright.async_api import Page

async def test_example(page: Page):
    pass"""

        result = _strip_markdown_code_fences(text)
        assert result == expected

    def test_empty_string_input(self):
        """Test handling of empty string input."""
        result = _strip_markdown_code_fences("")
        assert result == ""

    def test_whitespace_only_input(self):
        """Test handling of whitespace-only input."""
        result = _strip_markdown_code_fences("   \n\t  \n  ")
        assert result == ""

    def test_prevents_code_fence_leakage(self):
        """Test that code fences don't leak into the final output."""
        # This specific case was causing ```python to appear in output
        text = """```python
from playwright.async_api import Page

async def test_login_form(page: Page):
    await page.goto("https://example.com")
    await page.fill("#username", "testuser")
    await page.fill("#password", "testpass")
    await page.click("#login-button")
```"""

        result = _strip_markdown_code_fences(text)

        # Ensure no backticks remain in the output
        assert "```" not in result
        assert "python" not in result or "from playwright.async_api import Page" in result
        assert result.startswith("from playwright.async_api import Page")
        assert "async def test_login_form(page: Page):" in result

    def test_incomplete_code_block_missing_closing(self):
        """Test handling of incomplete code blocks (missing closing ```)."""
        # This simulates the truncation issue you described
        text = """```python
from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("https://example.com")
    await page.get_by_role("button", name="Open").click()
    await page.get_by_role("combobox", name="Add Country").fill("austra")
    await page.get_by_role("option", name="Australia").click()
    await page.get_by_role"""

        result = _strip_markdown_code_fences(text)

        # Should extract the code even without closing ```
        assert "```python" not in result
        assert "from playwright.async_api import Page" in result
        assert result.endswith("await page.get_by_role")

    def test_incomplete_code_block_just_opening(self):
        """Test handling of just opening code fence."""
        text = """```python
from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("https://example.com")"""

        result = _strip_markdown_code_fences(text)

        # Should extract the code even without closing ```
        assert "```python" not in result
        assert "from playwright.async_api import Page" in result
        assert 'await page.goto("https://example.com")' in result


class TestValidateTestCode:
    """Tests for the _validate_test_code function."""

    def test_valid_playwright_test(self):
        """Test validation of a valid Playwright test."""
        code = """from playwright.async_api import Page

async def test_login(page: Page):
    await page.goto("https://example.com")
    await page.click("#login")"""

        is_valid, error = _validate_test_code(code)
        assert is_valid is True
        assert error == ""

    def test_empty_code(self):
        """Test validation of empty code."""
        is_valid, error = _validate_test_code("")
        assert is_valid is False
        assert error == "No code content found"

    def test_whitespace_only_code(self):
        """Test validation of whitespace-only code."""
        is_valid, error = _validate_test_code("   \n\t  \n  ")
        assert is_valid is False
        assert error == "No code content found"

    def test_missing_playwright_import(self):
        """Test validation when Playwright import is missing."""
        code = """import asyncio

async def test_example(page):
    await page.goto("https://example.com")"""

        is_valid, error = _validate_test_code(code)
        assert is_valid is False
        assert error == "Missing required test function definition: async def test_<name>(page: Page):"

    def test_missing_test_function(self):
        """Test validation when test function is missing."""
        code = """from playwright.async_api import Page

def some_helper_function():
    pass"""

        is_valid, error = _validate_test_code(code)
        assert is_valid is False
        assert error == "Missing required test function definition: async def test_<name>(page: Page):"

    def test_wrong_function_signature(self):
        """Test validation with wrong function signature."""
        code = """from playwright.async_api import Page

async def test_example():  # Missing page parameter
    pass"""

        is_valid, error = _validate_test_code(code)
        assert is_valid is False
        assert error == "Missing required test function definition: async def test_<name>(page: Page):"

    def test_non_async_test_function(self):
        """Test validation with non-async test function."""
        code = """from playwright.async_api import Page

def test_example(page: Page):  # Not async
    pass"""

        is_valid, error = _validate_test_code(code)
        assert is_valid is False
        assert error == "Missing required test function definition: async def test_<name>(page: Page):"

    def test_valid_with_extra_spacing(self):
        """Test validation with extra spacing in function signature."""
        code = """from playwright.async_api import Page

async def test_example(page:   Page):
    await page.goto("https://example.com")"""

        is_valid, error = _validate_test_code(code)
        assert is_valid is True
        assert error == ""

    def test_multiple_test_functions(self):
        """Test validation with multiple test functions (should pass)."""
        code = """from playwright.async_api import Page

async def test_login(page: Page):
    await page.goto("https://example.com/login")

async def test_signup(page: Page):
    await page.goto("https://example.com/signup")"""

        is_valid, error = _validate_test_code(code)
        assert is_valid is True
        assert error == ""


class TestGenerateOrUpdateCode:
    """Tests for the generate_or_update_code function."""

    @pytest.fixture
    def mock_state(self):
        """Create a mock TestAgentState."""
        state = MagicMock()
        state.current_test_code = None
        return state

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_successful_generation_first_attempt(self, mock_state, mock_agent):
        """Test successful code generation on first attempt."""
        # Mock the agent creation and response
        mock_state.create_agent.return_value = mock_agent
        mock_agent.invoke.return_value = """```python
from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("https://example.com")
```"""

        result = await generate_or_update_code(mock_state)

        # Verify the code was extracted and set
        expected_code = """from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("https://example.com")"""

        assert result.current_test_code == expected_code
        assert mock_agent.invoke.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_invalid_code(self, mock_state, mock_agent):
        """Test retry logic when code is invalid."""
        mock_state.create_agent.return_value = mock_agent

        # First call returns invalid code, second returns valid code
        mock_agent.invoke.side_effect = [
            "```python\n# Missing required import\nasync def test_example(page):\n    pass\n```",
            "```python\nfrom playwright.async_api import Page\n\nasync def test_example(page: Page):\n    await page.goto('https://example.com')\n```",
        ]

        with patch("src.tresto.ai.agent.tools.generate.console"):
            result = await generate_or_update_code(mock_state)

        # Should have made 2 calls and succeeded on second attempt
        assert mock_agent.invoke.call_count == 2
        assert "from playwright.async_api import Page" in result.current_test_code
        assert "async def test_example(page: Page):" in result.current_test_code

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_state, mock_agent):
        """Test behavior when max retries are exceeded."""
        mock_state.create_agent.return_value = mock_agent

        # All calls return invalid code
        invalid_response = "```python\n# Invalid code without proper structure\n```"
        mock_agent.invoke.return_value = invalid_response

        with patch("src.tresto.ai.agent.tools.generate.console"):
            result = await generate_or_update_code(mock_state)

        # Should have made MAX_RETRIES calls
        assert mock_agent.invoke.call_count == MAX_RETRIES
        # Should use raw response as fallback
        assert result.current_test_code == invalid_response

    @pytest.mark.asyncio
    async def test_retry_prompt_includes_error(self, mock_state, mock_agent):
        """Test that retry prompts include the previous error."""
        mock_state.create_agent.return_value = mock_agent

        # First call returns code without import, second succeeds
        mock_agent.invoke.side_effect = [
            "```python\nasync def test_example(page):\n    pass\n```",
            "```python\nfrom playwright.async_api import Page\n\nasync def test_example(page: Page):\n    pass\n```",
        ]

        with patch("src.tresto.ai.agent.tools.generate.console"):
            await generate_or_update_code(mock_state)

            # Check that the second call includes error information
        second_call_args = mock_agent.invoke.call_args_list[1]
        message_content = second_call_args[1]["message"].content

        assert "The previous attempt failed with error:" in message_content
        assert "Missing required test function definition" in message_content

    @pytest.mark.asyncio
    async def test_code_without_fences_handled(self, mock_state, mock_agent):
        """Test handling of code without markdown fences."""
        mock_state.create_agent.return_value = mock_agent
        mock_agent.invoke.return_value = """from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("https://example.com")"""

        result = await generate_or_update_code(mock_state)

        # Should still work even without code fences
        assert "from playwright.async_api import Page" in result.current_test_code
        assert "async def test_example(page: Page):" in result.current_test_code

    @pytest.mark.asyncio
    async def test_system_prompt_created_correctly(self, mock_state, mock_agent):
        """Test that the system prompt is created with correct instructions."""
        mock_state.create_agent.return_value = mock_agent
        mock_agent.invoke.return_value = """```python
from playwright.async_api import Page

async def test_example(page: Page):
    await page.goto("https://example.com")
```"""

        await generate_or_update_code(mock_state)

        # Verify the agent was created with proper system message
        create_agent_call = mock_state.create_agent.call_args[0][0]

        assert "test code generator" in create_agent_call
        assert "```python code blocks" in create_agent_call
        assert "from playwright.async_api import Page" in create_agent_call
        assert "async def test_" in create_agent_call
