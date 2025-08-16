from __future__ import annotations

import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.messages import SystemMessage

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


async def read_file_content(state: TestAgentState) -> TestAgentState:
    llm = state.create_llm()

    request_path_message = SystemMessage(
        textwrap.dedent(
            """\
                You need to read the content of a file.
                Provide the file path you want to read.
                The path can be relative to the current working directory or absolute.
                Respond with only the file path and nothing else.
            """
        )
    )

    path_response = await llm.ainvoke(state.messages + [request_path_message])
    file_path = Path(path_response.content.strip())

    try:
        content = file_path.read_text(encoding="utf-8")
        
        # Truncate very long files to prevent context overflow
        max_chars = 10000
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n... [File truncated - showing first {max_chars} characters of {len(content)} total]"
        
        result_message = f"File content of '{file_path}':\n\n```\n{content}\n```"
        
    except FileNotFoundError:
        result_message = f"Error: File '{file_path}' not found."
    except PermissionError:
        result_message = f"Error: Permission denied reading file '{file_path}'."
    except UnicodeDecodeError:
        result_message = f"Error: File '{file_path}' is not a text file or uses an unsupported encoding."
    except Exception as e:
        result_message = f"Error reading file '{file_path}': {e}"

    state.messages.append(SystemMessage(content=result_message))
    await state.output_to_console(f"Read file: {file_path}")
    
    return state 