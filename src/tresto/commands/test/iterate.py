from __future__ import annotations

import asyncio

from rich.console import Console

from tresto.core.runner import TrestoRunner

console = Console()


def iterate_test_command(test_name: str | None = None) -> None:
    asyncio.run(_iterate_test_command(test_name))


async def _iterate_test_command(test_name: str | None = None) -> None:
    runner = TrestoRunner(test_name=test_name, mode="iterate")
    await runner.run()
