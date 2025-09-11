"""Tests for AI agent state modifications."""

from pathlib import Path

from tresto.ai.agent.state import Decision, TestAgentState
from tresto.core.config.main import AIConfig, BrowserConfig, ProjectConfig, TrestoConfig


def create_test_config() -> TrestoConfig:
    """Create a test configuration with all required fields."""
    return TrestoConfig(
        project=ProjectConfig(name="test_project", url="https://example.com", test_directory="tests"),
        ai=AIConfig(connector="anthropic", model="claude-3-sonnet-20240229", temperature=0.7),
        browser=BrowserConfig.default(),
    )


class TestDecision:
    """Test cases for Decision enum."""

    def test_playwright_iterate_decision_exists(self) -> None:
        """Test that expected core decisions are available."""
        assert Decision.MODIFY_CODE in Decision
        assert Decision.RUN_TEST in Decision
        assert Decision.INSPECT in Decision

    def test_all_decisions_valid(self) -> None:
        """Test that all decisions are valid string enums."""
        expected_decisions = {
            "record_user_input",
            "decide_next_action",
            "ask_user",
            "run_test",
            "modify_code",
            "inspect",
            "finish",
        }

        actual_decisions = {decision.value for decision in Decision}
        assert actual_decisions == expected_decisions

    def test_decision_membership(self) -> None:
        """Test decision membership operations."""
        # Test set operations work correctly with new decision
        all_decisions = set(Decision)
        assert Decision.INSPECT in all_decisions

        # Test exclusion operations
        non_action_decisions = {Decision.FINISH, Decision.DESIDE_NEXT_ACTION}
        action_decisions = all_decisions - non_action_decisions
        assert Decision.INSPECT in action_decisions


class TestTestAgentStateWithPlaywrightIterate:
    """Test cases for TestAgentState with playwright iteration functionality."""

    def test_agent_state_creation(self) -> None:
        """Test that agent state can be created with all required fields."""
        config = create_test_config()
        config.project.url = "https://example.com"

        state = TestAgentState(
            test_name="test_playwright_iterate",
            test_instructions="Test the playwright iteration functionality",
            test_file_path=Path("test_playwright.py"),
            recording_file_path=Path("recording_playwright.py"),
            config=config,
        )

        assert state.test_name == "test_playwright_iterate"
        assert state.test_instructions == "Test the playwright iteration functionality"
        assert state.config.project.url == "https://example.com"
        assert state.last_decision is None
        assert len(state.messages) >= 0

    def test_decision_setting(self) -> None:
        """Test setting and retrieving decisions including PLAYWRIGHT_ITERATE."""
        config = create_test_config()
        state = TestAgentState(
            test_name="test",
            test_instructions="Test instructions",
            test_file_path=Path("test.py"),
            recording_file_path=Path("recording.py"),
            config=config,
        )

        # Test setting inspect decision
        state.last_decision = Decision.INSPECT
        assert state.last_decision == Decision.INSPECT
        assert state.last_decision.value == "inspect"

        # Test setting other decisions
        state.last_decision = Decision.ASK_USER
        assert state.last_decision == Decision.ASK_USER

        state.last_decision = Decision.FINISH
        assert state.last_decision == Decision.FINISH

    def test_llm_creation(self) -> None:
        """Test that LLM can be created from state."""
        config = create_test_config()
        config.ai.connector = "anthropic"
        config.ai.model = "claude-3-sonnet-20240229"
        config.ai.temperature = 0.7

        state = TestAgentState(
            test_name="test",
            test_instructions="Test instructions",
            test_file_path=Path("test.py"),
            recording_file_path=Path("recording.py"),
            config=config,
        )

        # This should not raise an exception
        llm = state.create_llm()
        assert llm is not None
        # Can't easily test the actual model without API keys
        # but we can verify the method works
