"""Factory for creating AI connectors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.console import Console

from .anthropic.connector import AnthropicConnector
from .openai.connector import OpenAIConnector

if TYPE_CHECKING:
    from .base import AIConnector, AnyAIConnector

console = Console()

# Registry of available connectors
CONNECTOR_REGISTRY: dict[str, type[AnyAIConnector]] = {
    "anthropic": AnthropicConnector,
    "claude": AnthropicConnector,  # Alias
    "openai": OpenAIConnector,
    "gpt": OpenAIConnector,  # Alias
}


class ConnectorFactory:
    """Factory for creating AI model connectors."""

    @staticmethod
    def create_connector(provider: str, model_name: str | None = None, **kwargs: Any) -> AnyAIConnector:
        """Create a connector for the specified provider.

        Args:
            provider: The AI provider (anthropic, openai, etc.)
            model_name: Optional specific model name
            **kwargs: Additional configuration for the connector

        Returns:
            AIConnector instance

        Raises:
            ValueError: If provider is not supported
        """
        provider_lower = provider.lower()

        if provider_lower not in CONNECTOR_REGISTRY:
            available = ", ".join(CONNECTOR_REGISTRY.keys())
            raise ValueError(f"Unsupported provider '{provider}'. Available: {available}")

        connector_class = CONNECTOR_REGISTRY[provider_lower]

        # Set default model names if not provided
        default_model: str
        if model_name is None:
            if provider_lower in ["anthropic", "claude"]:
                default_model = "claude-3-5-sonnet-20241022"
            elif provider_lower in ["openai", "gpt"]:
                default_model = "o3-mini"  # Using o3-mini as default
            else:
                default_model = "unknown-model"
            model_to_use = default_model
        else:
            model_to_use = model_name

        return connector_class(model_name=model_to_use, **kwargs)

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available providers."""
        return list(CONNECTOR_REGISTRY.keys())

    @staticmethod
    def get_available_connectors() -> list[AIConnector]:
        """Get list of available and configured connectors."""
        available = []
        for provider in ["anthropic", "openai"]:  # Check main providers only
            try:
                connector = ConnectorFactory.create_connector(provider)
                if connector.is_available:
                    available.append(connector)
            except (ValueError, ImportError, OSError):
                # Skip unavailable connectors
                continue
        return available
