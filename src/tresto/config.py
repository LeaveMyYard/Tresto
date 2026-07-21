"""Lazy access to Tresto configuration for runtime pytest execution."""

from __future__ import annotations

from typing import Any

from pydantic import ConfigDict

from tresto.core.config.main import TrestoConfig


class LazyConfig:
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _load(self) -> TrestoConfig:
        return TrestoConfig.load_config()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._load(), name)

    def get_secrets(self) -> dict[str, str]:
        return self._load().get_secrets()


class LazySecrets:
    def _load(self) -> dict[str, str]:
        return TrestoConfig.load_config().get_secrets()

    def __getitem__(self, key: str) -> str:
        return self._load()[key]

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._load().get(key, default)

    def items(self) -> Any:
        return self._load().items()

    def __iter__(self) -> Any:
        return iter(self._load())

    def __len__(self) -> int:
        return len(self._load())


config = LazyConfig()
secrets = LazySecrets()


__all__ = ["config", "secrets"]
