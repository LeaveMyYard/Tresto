from __future__ import annotations

from unittest.mock import MagicMock

from src.tresto.ai.agent.agent import Agent, _get_last_n_lines


class TestGetLastNLines:
    """Tests for the _get_last_n_lines helper function."""

    def test_get_last_n_lines_basic(self):
        """Test getting last N lines from multi-line text."""
        text = """Line 1
Line 2
Line 3
Line 4
Line 5
Line 6
Line 7
Line 8
Line 9
Line 10"""

        result = _get_last_n_lines(text, 3)
        expected = """Line 8
Line 9
Line 10"""
        assert result == expected

    def test_get_last_n_lines_more_than_available(self):
        """Test requesting more lines than available."""
        text = "Line 1\nLine 2\nLine 3"
        result = _get_last_n_lines(text, 10)
        assert result == text

    def test_get_last_n_lines_exact_match(self):
        """Test requesting exactly the number of lines available."""
        text = "Line 1\nLine 2\nLine 3"
        result = _get_last_n_lines(text, 3)
        assert result == text

    def test_get_last_n_lines_zero_lines(self):
        """Test with max_lines = 0."""
        text = "Line 1\nLine 2\nLine 3"
        result = _get_last_n_lines(text, 0)
        assert result == text

    def test_get_last_n_lines_negative_lines(self):
        """Test with negative max_lines."""
        text = "Line 1\nLine 2\nLine 3"
        result = _get_last_n_lines(text, -5)
        assert result == text

    def test_get_last_n_lines_empty_text(self):
        """Test with empty text."""
        result = _get_last_n_lines("", 5)
        assert result == ""

    def test_get_last_n_lines_whitespace_only(self):
        """Test with whitespace-only text."""
        result = _get_last_n_lines("   \n\t  \n  ", 2)
        assert result == "   \n\t  \n  "

    def test_get_last_n_lines_single_line(self):
        """Test with single line text."""
        text = "Single line"
        result = _get_last_n_lines(text, 1)
        assert result == text

    def test_get_last_n_lines_single_line_request_more(self):
        """Test requesting more lines from single line text."""
        text = "Single line"
        result = _get_last_n_lines(text, 5)
        assert result == text

    def test_get_last_n_lines_trailing_newlines(self):
        """Test with text that has trailing newlines."""
        text = "Line 1\nLine 2\nLine 3\n\n"
        result = _get_last_n_lines(text, 2)
        # When split, "Line 3\n\n" becomes ['Line 1', 'Line 2', 'Line 3', '', '']
        # Last 2 elements are ['', ''] which join to '\n'
        expected = "\n"
        assert result == expected

    def test_get_last_n_lines_realistic_trailing_newline(self):
        """Test with text that has single trailing newline (more realistic case)."""
        text = "Line 1\nLine 2\nLine 3\nLine 4\n"
        result = _get_last_n_lines(text, 2)
        # Last 2 elements after split are ['Line 4', ''] which join to 'Line 4\n'
        expected = "Line 4\n"
        assert result == expected


class TestAgentMaxLines:
    """Tests for the Agent class max_lines functionality."""

    def test_process_message_with_max_lines(self):
        """Test _process_message applies max_lines correctly."""
        # Create a mock message with string content
        mock_message = MagicMock()
        mock_message.content = """Line 1
Line 2
Line 3
Line 4
Line 5"""

        result = Agent._process_message(mock_message, max_lines=3)

        # Should be a Markdown object, check its content
        assert hasattr(result, "markup")
        # The result should contain only the last 3 lines
        expected_content = "Line 3\nLine 4\nLine 5"
        assert result.markup == expected_content

    def test_process_message_with_max_lines_complex_content(self):
        """Test _process_message with complex content structure."""
        mock_message = MagicMock()
        mock_message.content = [
            "First part\nSecond part\nThird part",
            {"type": "tool_call", "name": "test_tool", "args": "{}"},
            {"text": "Text part\nAnother line\nFinal line"},
        ]

        result = Agent._process_message(mock_message, max_lines=2)

        # Should combine all content and then apply line limiting
        assert hasattr(result, "markup")
        # The result should be limited to last 2 lines of the combined content
        lines = result.markup.split("\n")
        assert len(lines) <= 2

    def test_process_message_without_max_lines(self):
        """Test _process_message without max_lines (should not limit)."""
        mock_message = MagicMock()
        mock_message.content = """Line 1
Line 2
Line 3
Line 4
Line 5"""

        result = Agent._process_message(mock_message, max_lines=None)

        # Should contain all lines
        assert hasattr(result, "markup")
        assert "Line 1" in result.markup
        assert "Line 5" in result.markup

    def test_create_response_panel_with_max_lines(self):
        """Test _create_response_panel includes max_lines info in title."""
        mock_result = MagicMock()
        mock_result.text.return_value = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        mock_result.content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"

        panel_title = "Test Panel ({char_count} chars, {total_lines} lines, showing {showing_lines})"

        panel = Agent._create_response_panel(mock_result, panel_title, "blue", max_lines=3)

        # Check that the title includes the line information
        assert "5 lines" in panel.title  # total lines
        assert "showing 3" in panel.title  # showing lines
        assert "chars" in panel.title  # char count

    def test_create_response_panel_without_max_lines(self):
        """Test _create_response_panel without max_lines."""
        mock_result = MagicMock()
        mock_result.text.return_value = "Line 1\nLine 2\nLine 3"
        mock_result.content = "Line 1\nLine 2\nLine 3"

        panel_title = "Test Panel ({char_count} chars)"

        panel = Agent._create_response_panel(mock_result, panel_title, "blue", max_lines=None)

        # Should use the simple title format
        assert "chars" in panel.title
        assert "lines" not in panel.title  # No line info when max_lines is None

    def test_create_response_panel_max_lines_larger_than_content(self):
        """Test when max_lines is larger than actual content lines."""
        mock_result = MagicMock()
        mock_result.text.return_value = "Line 1\nLine 2"
        mock_result.content = "Line 1\nLine 2"

        panel_title = "Test Panel ({char_count} chars, {total_lines} lines, showing {showing_lines})"

        panel = Agent._create_response_panel(mock_result, panel_title, "blue", max_lines=10)

        # Should show actual line count, not the max_lines limit
        assert "2 lines" in panel.title  # total lines
        assert "showing 2" in panel.title  # showing lines (min of max_lines and total)
