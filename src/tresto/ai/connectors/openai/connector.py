"""Anthropic Claude connector using langchain."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from langchain_openai import ChatOpenAI

from tresto.ai.connectors.base import AIConnector
from tresto.utils.errors import InitError

from ..base import AIConnector
from .settings import OpenAISettings

if TYPE_CHECKING:
    from collections.abc import Sequence


class OpenAIConnector(AIConnector[ChatOpenAI, OpenAISettings]):
    """Connector for OpenAI models via langchain."""

    DEFAULT_MODEL: ClassVar[str] = "chat"

    def _create_settings(self) -> OpenAISettings:
        return OpenAISettings()

    def _create_client(self) -> ChatOpenAI:
        if not self._settings.api_key:
            raise InitError("API key must be set in settings")

        return ChatOpenAI(
            model=self.model_name,
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
