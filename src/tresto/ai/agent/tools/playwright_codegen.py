from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from langchain_core.messages import SystemMessage

from tresto.ai.agent.state import PlaywrightRecordingStep
from tresto.core.recorder import BrowserRecorder

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


async def tool_record_user_input(state: TestAgentState) -> TestAgentState:
    recorder = BrowserRecorder(config=state.config)

    recording_step = PlaywrightRecordingStep()
    await state.add_output(recording_step)

    async with recording_step:
        state.current_recording_code = await recorder.start_recording(
            url=state.config.project.base_url,
            output_file=state.recording_file_path,
        )

    state.messages.append(
        SystemMessage(
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

    return state
