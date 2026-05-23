"""Factory for creating AI connectors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from rich.console import Console

from .anthropic.connector import AnthropicConnector
from .openai.connector import OpenAIConnector
from .test.connector import TestConnector

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .base import AIConnector

console = Console()

# Registry of available connectors
CONNECTOR_REGISTRY: dict[str, type[AIConnector]] = {
    "openai": OpenAIConnector,
    "gpt": OpenAIConnector,  # Alias
    "anthropic": AnthropicConnector,
    "claude": AnthropicConnector,  # Alias
    "test": TestConnector,
    "mock": TestConnector,  # Alias
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
    connectors: list[type[AIConnector]] = []
    for connector in CONNECTOR_REGISTRY.values():
        if connector not in connectors:
            connectors.append(connector)

    for connector in connectors:
        aliases = [name for name, cls in CONNECTOR_REGISTRY.items() if cls is connector]
        name = aliases[0]
        yield ConnectorInformation(name=name, aliases=aliases, description=connector.get_description())
