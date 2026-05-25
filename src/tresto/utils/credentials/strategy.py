from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

    from .store import CredentialStore


class CredentialStrategy(ABC):
    connectors: set[str]

    def __init__(self, store: CredentialStore, console: Console) -> None:
        self.store = store
        self.console = console

    @abstractmethod
    def ensure(self) -> None:
        """Ensure credentials for this provider are available to SDKs in-process."""

    def refresh(self, reason: str | None = None) -> None:
        """Refresh credentials after a provider rejects the current value."""
        if reason:
            self.console.print(f"[yellow]{reason}[/yellow]")
        self.ensure()
