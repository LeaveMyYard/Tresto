"""Factory for creating AI connectors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from rich.console import Console

from .anthropic.connector import AnthropicConnector
from .openai.connector import OpenAIConnector

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .base import AIConnector

console = Console()

# Registry of available connectors
CONNECTOR_REGISTRY: dict[str, type[AIConnector]] = {
    "anthropic": AnthropicConnector,
    "claude": AnthropicConnector,  # Alias
    "openai": OpenAIConnector,
    "gpt": OpenAIConnector,  # Alias
}


def connect(connector_name: str, model_name: str | None = None) -> AIConnector:
    """Create an instance of the specified AI connector."""

    connector_class = CONNECTOR_REGISTRY.get(connector_name.lower())

    if not connector_class:
        raise KeyError(f"Unknown connector: {connector_name}")

    return connector_class(model_name=model_name)


class ConnectorInformation(BaseModel):
    name: str
    aliases: list[str] = []
    description: str


def get_available_connectors() -> Iterable[ConnectorInformation]:
    """Get information about all available AI connectors."""
    connectors = set(CONNECTOR_REGISTRY.values())

    for connector in connectors:
        aliases = [name for name, cls in CONNECTOR_REGISTRY.items() if cls is connector]
        name = aliases[0]
        yield ConnectorInformation(name=name, aliases=aliases, description=connector.get_description())
