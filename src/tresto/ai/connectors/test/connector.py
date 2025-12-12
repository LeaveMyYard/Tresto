"""Test connector for E2E testing without real API calls."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from tresto.ai.connectors.base import BaseAIConnector

from .chat_model import TestChatModel
from .settings import TestSettings

if TYPE_CHECKING:
    from collections.abc import Sequence


# TODO: We need an ability to hide this connector from the user.
class TestConnector(BaseAIConnector[TestChatModel, TestSettings]):
    """Test AI connector that returns mock responses without making real API calls."""

    DEFAULT_MODEL: ClassVar[str] = "test-model"

    def _create_settings(self) -> TestSettings:
        return TestSettings()

    def _create_client(self) -> TestChatModel:
        return TestChatModel(model_name=self.model_name)

    async def get_available_models(self) -> Sequence[str]:
        """Get list of available test models."""
        return [
            "test-model",
            "test-model-v2",
            "mock-agent",
        ]

