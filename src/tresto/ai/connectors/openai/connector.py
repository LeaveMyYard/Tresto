"""OpenAI connector using langchain."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from langchain_openai import ChatOpenAI

from tresto.ai.connectors.base import BaseAIConnector
from tresto.utils.errors import InitError

from .settings import OpenAISettings

if TYPE_CHECKING:
    from collections.abc import Sequence


class OpenAIConnector(BaseAIConnector[ChatOpenAI, OpenAISettings]):
    """OpenAI API models, including GPT and Codex coding models."""

    DEFAULT_MODEL: ClassVar[str] = "gpt-5.3-codex"

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
            "gpt-5.3-codex",
            "gpt-5.2-codex",
            "gpt-5.1-codex",
            "gpt-5-codex",
            "gpt-5.1",
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-vision-preview",
            "gpt-4o",
            "gpt-4o-mini",
        ]
