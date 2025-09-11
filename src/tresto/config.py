"""A bunch of utilities for runtime pytest execution."""

from typing import Any

from rich.console import Console

from tresto.core.config.main import ConfigLoadingError, TrestoConfig

console = Console()

try:
    __base_config = TrestoConfig.load_config()
except ConfigLoadingError:
    # If config is not loaded, we need to raise an error at runtime, not at import time
    # This ensures that commands are not failing, for example during `tresto init`
    class RuntimeFailingConfig:
        def __getattribute__(self, name: str) -> Any:
            raise ConfigLoadingError("Could not load configuration.")

    config: TrestoConfig | RuntimeFailingConfig = RuntimeFailingConfig()
    secrets: dict[str, str] | RuntimeFailingConfig = RuntimeFailingConfig()
else:
    config = __base_config
    secrets = __base_config.get_secrets()


__all__ = ["config", "secrets"]
