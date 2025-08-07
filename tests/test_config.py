"""Tests for configuration management."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tresto.core.config import TrestoConfig, get_anthropic_api_key, load_config, save_config


def test_default_config() -> None:
    """Test default configuration values."""
    config = TrestoConfig()

    assert config.project.name == "my-project"
    assert config.project.base_url == "http://localhost:3000"
    assert config.project.test_directory == "./tests"

    assert config.browser.headless is False
    assert config.browser.timeout == 30000
    assert config.browser.viewport == {"width": 1280, "height": 720}

    assert config.ai.model == "claude-3-5-sonnet-20241022"
    assert config.ai.max_iterations == 5
    assert config.ai.temperature == 0.1


def test_save_and_load_config() -> None:
    """Test saving and loading configuration."""
    with TemporaryDirectory() as tmpdir:
        # Change to temp directory
        original_cwd = Path.cwd()
        os.chdir(tmpdir)

        try:
            # Create custom config
            config = TrestoConfig()
            config.project.name = "test-project"
            config.project.base_url = "http://localhost:8080"

            # Save config
            save_config(config)

            # Load config
            loaded_config = load_config()

            assert loaded_config.project.name == "test-project"
            assert loaded_config.project.base_url == "http://localhost:8080"

        finally:
            os.chdir(original_cwd)


def test_get_anthropic_api_key() -> None:
    """Test getting Anthropic API key from environment."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        assert get_anthropic_api_key() == "test-key"

    with patch.dict(os.environ, {}, clear=True):
        assert get_anthropic_api_key() is None
