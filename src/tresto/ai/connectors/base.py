"""Base connector interface for AI models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Represents a chat message."""

    role: str  # "user", "assistant", "system"
    content: str


class GenerationResult(BaseModel):
    """Result from AI generation."""

    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None


class AIConnector(ABC):
    """Abstract base class for AI model connectors."""

    def __init__(self, model_name: str, **kwargs: Any) -> None:
        """Initialize the connector."""
        self.model_name = model_name
        self.config = kwargs

    @abstractmethod
    async def generate(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate a response from the AI model."""
        pass

    @abstractmethod
    async def stream_generate(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs: Any,
    ):
        """Stream generate a response from the AI model."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the connector is available (API key set, etc.)."""
        pass

    @property
    @abstractmethod
    def max_tokens_limit(self) -> int:
        """Maximum tokens supported by the model."""
        pass
