from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from tresto.ai.connectors.base import BaseAIConnector

from .chat_model import CodexChatModel
from .settings import CodexSettings

if TYPE_CHECKING:
    from collections.abc import Sequence


class CodexConnector(BaseAIConnector[CodexChatModel, CodexSettings]):
    """ChatGPT Codex backend via Codex browser auth."""

    DEFAULT_MODEL: ClassVar[str] = "gpt-5.2-codex"

    def _create_settings(self) -> CodexSettings:
        return CodexSettings()

    def _create_client(self) -> CodexChatModel:
        return CodexChatModel(
            model_name=self.model_name,
            auth_file=self._settings.auth_file,
            **self.config,
        )

    async def get_available_models(self) -> Sequence[str]:
        return [
            "gpt-5.3-codex",
            "gpt-5.2-codex",
            "gpt-5.1-codex-max",
            "gpt-5.1-codex",
            "gpt-5.1-codex-mini",
            "gpt-5-codex",
            "codex-5.3",
            "gpt-5.5",
            "gpt-5.2",
            "gpt-5.1",
        ]
