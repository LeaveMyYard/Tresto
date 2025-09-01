"""AI package for Tresto.

Avoid heavy side-effect imports at package import time to keep lightweight modules
importable in environments without full optional dependencies.
"""

try:  # pragma: no cover - optional import for convenience
    from .agent import state as state  # noqa: F401
except Exception:  # noqa: BLE001
    # Optional during lightweight imports/tests
    state = None  # type: ignore[assignment]
