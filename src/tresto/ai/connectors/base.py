"""Base connector interface for AI models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from rich.console import Console

if TYPE_CHECKING:
    from collections.abc import Sequence

console = Console()


class ChatMessage(BaseModel):
    """Represents a chat message."""

    role: str  # "user", "assistant", "system"
    content: str


class GenerationResult(BaseModel):
    """Result from AI generation."""

    content: str
    model: str
    tokens_used: int | None = None
    finish_reason: str | None = None


class BaseAIConnector[ChatModel: BaseChatModel, Settings: BaseSettings](ABC):
    DEFAULT_MODEL: ClassVar[str]

    def __init__(self, model_name: str | None = None, **kwargs: Any) -> None:
        """Initialize the connector."""
        self.model_name = model_name or self.DEFAULT_MODEL
        self.config = kwargs
        self._client: BaseChatModel | None = None
        self._settings = self._create_settings()

    @abstractmethod
    def _create_settings(self) -> Settings:
        """Create settings instance for this connector."""

    @abstractmethod
    def _create_client(self) -> ChatModel:
        """Create and return the langchain client instance."""

    @classmethod
    def get_description(cls) -> str:
        """Get a brief description of the connector. By default, returns the class docstring."""

        return cls.__doc__ or "No description available."

    @property
    def client(self) -> BaseChatModel:
        """Get or create the langchain client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    @abstractmethod
    async def get_available_models(self) -> Sequence[str]:
        """Get list of available models for this connector."""


AIConnector = BaseAIConnector[BaseChatModel, BaseSettings]
