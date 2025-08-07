"""Factory for creating AI connectors."""

from __future__ import annotations

from typing import Dict, Type, Any
from rich.console import Console

from .base import AIConnector
from .anthropic import AnthropicConnector
from .openai import OpenAIConnector

console = Console()

# Registry of available connectors
CONNECTOR_REGISTRY: Dict[str, Type[AIConnector]] = {
    "anthropic": AnthropicConnector,
    "claude": AnthropicConnector,  # Alias
    "openai": OpenAIConnector,
    "gpt": OpenAIConnector,  # Alias
}


class ConnectorFactory:
    """Factory for creating AI model connectors."""

    @staticmethod
    def create_connector(provider: str, model_name: str | None = None, **kwargs: Any) -> AIConnector:
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
        if model_name is None:
            if provider_lower in ["anthropic", "claude"]:
                model_name = "claude-3-5-sonnet-20241022"
            elif provider_lower in ["openai", "gpt"]:
                model_name = "o3-mini"  # Using o3-mini as default, can be changed to "o3" for full model

        return connector_class(model_name=model_name, **kwargs)

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
            except Exception:
                # Skip unavailable connectors
                continue
        return available
