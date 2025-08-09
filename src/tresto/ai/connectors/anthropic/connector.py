"""Anthropic Claude connector using langchain."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from langchain_anthropic import ChatAnthropic

from tresto.ai.connectors.base import BaseAIConnector
from tresto.utils.errors import InitError

from .settings import AnthropicSettings

if TYPE_CHECKING:
    from collections.abc import Sequence


class AnthropicConnector(BaseAIConnector[ChatAnthropic, AnthropicSettings]):
    """Anthropic Claude models."""

    DEFAULT_MODEL: ClassVar[str] = "claude-3-5-sonnet-20241022"

    def _create_settings(self) -> AnthropicSettings:
        return AnthropicSettings()

    def _create_client(self) -> ChatAnthropic:
        if not self._settings.api_key:
            raise InitError("API key must be set in settings")

        return ChatAnthropic(
            model_name=self.model_name,
            api_key=self._settings.api_key,
            **self.config,
        )

    async def get_available_models(self) -> Sequence[str]:
        """Get list of available Anthropic models."""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
