from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage
from rich.console import Console

from tresto.ai import prompts
from tresto.core.recorder import BrowserRecorder

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def tool_record_user_input(state: TestAgentState) -> TestAgentState:
    recorder = BrowserRecorder(config=state.config)

    with console.status("🔍 Running [bold]`playwright codegen`[/bold] to record user input..."):
        state.current_recording_code = await recorder.start_recording(
            url=state.config.project.url,
            output_file=state.recording_file_path,
        )

    state.messages.append(HumanMessage(prompts.codegen(state.current_recording_code)))

    console.print("✅ User input recorded successfully")

    return state
