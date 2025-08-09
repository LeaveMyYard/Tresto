"""Anthropic Claude connector using langchain."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from langchain_openai import ChatOpenAI

from tresto.ai.connectors.base import BaseAIConnector
from tresto.utils.errors import InitError

from .settings import OpenAISettings

if TYPE_CHECKING:
    from collections.abc import Sequence


class OpenAIConnector(BaseAIConnector[ChatOpenAI, OpenAISettings]):
    """OpenAI Cloud GPT-based models."""

    DEFAULT_MODEL: ClassVar[str] = "chatgpt-4-turbo"

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
        return [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-vision-preview",
            "gpt-4o",
            "gpt-4o-mini",
        ]
