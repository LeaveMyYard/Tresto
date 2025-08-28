from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from tresto.core.config.main import TrestoConfig


# Test suite runners (used by CLI)
def resolve_tests_root(config: TrestoConfig | None = None) -> Path:
    if config is not None:
        return Path(config.project.test_directory).resolve()
    cwd = Path.cwd()
    for d in (cwd / "tresto" / "tests", cwd / "tests"):
        if d.exists():
            return d.resolve()
    return cwd
