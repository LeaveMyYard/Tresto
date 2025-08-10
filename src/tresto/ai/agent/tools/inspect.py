from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tresto.core.test import inspect_site

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


async def inspect(state: TestAgentState) -> dict[str, Any]:
    notes = await inspect_site(state["config"], state.get("recording_path"))
    return {"inspection_notes": notes, "debug_inspect": notes[:1200]}
