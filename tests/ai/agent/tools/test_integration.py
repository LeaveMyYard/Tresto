"""Integration tests for playwright iteration tool."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from tresto.ai.agent.state import TestAgentState
from tresto.ai.agent.tools.playwright_iterate import playwright_iterate_cycle
from tresto.core.config.main import TrestoConfig


class TestPlaywrightIterateIntegration:
    """Integration tests for the playwright iteration cycle."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"),
        reason="Requires API key for LLM integration test",
    )
    async def test_real_llm_integration(self) -> None:
        """Test with real LLM API (requires API key)."""
        config = TrestoConfig()
        config.project.url = "https://example.com"
        config.browser.headless = True

        # Use a real API key if available
        if os.getenv("ANTHROPIC_API_KEY"):
            config.ai.connector = "anthropic"
            config.ai.model = "claude-3-haiku-20240307"  # Use faster/cheaper model for testing
        elif os.getenv("OPENAI_API_KEY"):
            config.ai.connector = "openai"
            config.ai.model = "gpt-3.5-turbo"

        state = TestAgentState(
            test_name="integration_test",
            test_instructions="Navigate to example.com and check the page title",
            test_file_path=Path("integration_test.py"),
            recording_file_path=Path("integration_recording.py"),
            config=config,
        )

        state.messages.append(
            HumanMessage(
                content="Please navigate to the example.com website and examine its basic structure. "
                "Check the page title and look for any key elements."
            )
        )

        # This will make real API calls and execute real playwright code
        result_state = await playwright_iterate_cycle(state)

        # Verify the cycle completed successfully
        assert len(result_state.messages) > len(state.messages)
        final_message = result_state.messages[-1].content
        assert "Investigation Report" in final_message
        assert len(final_message) > 100  # Should be a substantial report

    @pytest.mark.asyncio
    async def test_mocked_full_cycle(self) -> None:
        """Test full cycle with mocked LLM responses but real playwright execution."""
        config = TrestoConfig()
        config.project.url = (
            "data:text/html,<html><head><title>Test Page</title></head><body><h1>Hello World</h1></body></html>"
        )
        config.browser.headless = True

        state = TestAgentState(
            test_name="mock_test",
            test_instructions="Test a simple HTML page",
            test_file_path=Path("mock_test.py"),
            recording_file_path=Path("mock_recording.py"),
            config=config,
        )

        # Mock LLM responses for code generation
        mock_llm = AsyncMock()

        # First call: generate code
        code_response = [
            MagicMock(content="```python\n"),
            MagicMock(content="async def run(page):\n"),
            MagicMock(content="    title = await page.title()\n"),
            MagicMock(content="    print(f'Page title: {title}')\n"),
            MagicMock(content="```"),
        ]

        # Second call: decision to finish
        decision_response = [MagicMock(content="FINISH")]

        # Third call: investigation report
        report_response = [
            MagicMock(content="# Investigation Report\n\n"),
            MagicMock(content="## Summary\n"),
            MagicMock(content="Successfully navigated to the test page and extracted the title.\n\n"),
            MagicMock(content="## Findings\n"),
            MagicMock(content="- Page title: 'Test Page'\n"),
            MagicMock(content="- Basic HTML structure confirmed\n\n"),
            MagicMock(content="## Recommendations\n"),
            MagicMock(content="The page is accessible and automation-friendly."),
        ]

        mock_llm.astream.side_effect = [iter(code_response), iter(decision_response), iter(report_response)]

        with patch.object(state, "create_llm", return_value=mock_llm):
            result_state = await playwright_iterate_cycle(state)

        # Verify the cycle worked
        assert len(result_state.messages) > len(state.messages)
        final_message = result_state.messages[-1].content
        assert "Investigation Report" in final_message
        assert "Test Page" in final_message
        assert "Successfully navigated" in final_message

        # Verify LLM was called the expected number of times
        assert mock_llm.astream.call_count == 3

    @pytest.mark.asyncio
    async def test_error_handling_integration(self) -> None:
        """Test error handling in integration scenarios."""
        config = TrestoConfig()
        config.project.url = "https://nonexistent-domain-12345.com"
        config.browser.headless = True

        state = TestAgentState(
            test_name="error_test",
            test_instructions="Test error handling",
            test_file_path=Path("error_test.py"),
            recording_file_path=Path("error_recording.py"),
            config=config,
        )

        # Mock LLM to generate code that will fail
        mock_llm = AsyncMock()

        # Generate code that tries to navigate to non-existent domain
        code_response = [
            MagicMock(content="```python\n"),
            MagicMock(content="async def run(page):\n"),
            MagicMock(content="    await page.goto('https://nonexistent-domain-12345.com')\n"),
            MagicMock(content="    await page.wait_for_timeout(1000)\n"),
            MagicMock(content="```"),
        ]

        # Decision to finish after error
        decision_response = [MagicMock(content="FINISH")]

        # Report generation
        report_response = [
            MagicMock(content="# Error Investigation Report\n\n"),
            MagicMock(content="Navigation to the target domain failed.\n"),
            MagicMock(content="This suggests the domain is not accessible."),
        ]

        mock_llm.astream.side_effect = [iter(code_response), iter(decision_response), iter(report_response)]

        with patch.object(state, "create_llm", return_value=mock_llm):
            result_state = await playwright_iterate_cycle(state)

        # Should complete despite the error
        assert len(result_state.messages) > len(state.messages)

        # Should have recorded the error
        error_messages = [msg for msg in result_state.messages if "failed with error" in msg.content]
        assert len(error_messages) > 0

    @pytest.mark.asyncio
    async def test_multiple_iterations_integration(self) -> None:
        """Test multiple iterations with different actions."""
        config = TrestoConfig()
        config.project.url = "data:text/html,<html><head><title>Multi Test</title></head><body><button id='test-btn'>Click Me</button></body></html>"
        config.browser.headless = True

        state = TestAgentState(
            test_name="multi_test",
            test_instructions="Test multiple interactions",
            test_file_path=Path("multi_test.py"),
            recording_file_path=Path("multi_recording.py"),
            config=config,
        )

        mock_llm = AsyncMock()

        # Iteration 1: Check title
        code1_response = [
            MagicMock(content="```python\n"),
            MagicMock(content="async def run(page):\n"),
            MagicMock(content="    title = await page.title()\n"),
            MagicMock(content="    print(f'Title: {title}')\n"),
            MagicMock(content="```"),
        ]

        # Decision 1: Continue
        decision1_response = [MagicMock(content="CONTINUE")]

        # Iteration 2: Click button
        code2_response = [
            MagicMock(content="```python\n"),
            MagicMock(content="async def run(page):\n"),
            MagicMock(content="    await page.click('#test-btn')\n"),
            MagicMock(content="    print('Button clicked')\n"),
            MagicMock(content="```"),
        ]

        # Decision 2: Finish
        decision2_response = [MagicMock(content="FINISH")]

        # Final report
        report_response = [
            MagicMock(content="# Multi-Iteration Report\n\n"),
            MagicMock(content="Completed 2 iterations successfully.\n"),
            MagicMock(content="1. Extracted page title\n"),
            MagicMock(content="2. Interacted with button element"),
        ]

        mock_llm.astream.side_effect = [
            iter(code1_response),
            iter(decision1_response),
            iter(code2_response),
            iter(decision2_response),
            iter(report_response),
        ]

        with patch.object(state, "create_llm", return_value=mock_llm):
            result_state = await playwright_iterate_cycle(state)

        # Should have completed multiple iterations
        assert mock_llm.astream.call_count == 5  # 2 code + 2 decisions + 1 report

        final_message = result_state.messages[-1].content
        assert "2 iterations" in final_message
        assert "Multi-Iteration Report" in final_message
