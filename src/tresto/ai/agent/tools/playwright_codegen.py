from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage
from rich.console import Console

from tresto.core.recorder import BrowserRecorder

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


async def tool_record_user_input(state: TestAgentState) -> TestAgentState:
    recorder = BrowserRecorder(config=state.config)

    console.print("🔍 Running [bold]`playwright codegen`[/bold] to record user input...")

    state.current_recording_code = await recorder.start_recording(
        url=state.config.project.base_url,
        output_file=state.recording_file_path,
    )

    state.messages.append(
        HumanMessage(
            content=textwrap.dedent(
                f"""\
                    User conducted the test manually using playwright codegen. Resulting code:
                    
                    ```python
                    {state.current_recording_code}
                    ```
                """
            ),
        )
    )

    console.print("✅ User input recorded successfully")

    return state
