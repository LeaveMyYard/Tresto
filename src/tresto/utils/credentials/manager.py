from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console

from .codex import CodexCredentialStrategy
from .openai import OpenAICredentialStrategy
from .store import CredentialStore

if TYPE_CHECKING:
    from .strategy import CredentialStrategy

STRATEGY_TYPES: tuple[type[CredentialStrategy], ...] = (OpenAICredentialStrategy, CodexCredentialStrategy)


def ensure_provider_credentials(connector: str, console: Console | None = None) -> None:
    normalized = connector.lower()
    strategy = _strategy_for_connector(normalized, console or Console())
    if strategy is None:
        return
    strategy.ensure()


def refresh_provider_credentials(connector: str, reason: str | None = None, console: Console | None = None) -> None:
    normalized = connector.lower()
    strategy = _strategy_for_connector(normalized, console or Console())
    if strategy is None:
        return
    strategy.refresh(reason)


def _strategy_for_connector(connector: str, console: Console) -> CredentialStrategy | None:
    store = CredentialStore()
    for strategy_type in STRATEGY_TYPES:
        if connector in strategy_type.connectors:
            return strategy_type(store=store, console=console)
    return None
