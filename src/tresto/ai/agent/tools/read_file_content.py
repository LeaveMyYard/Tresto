from __future__ import annotations

import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


def _get_file_language(file_path: Path) -> str:
    """Determine the language for syntax highlighting based on file extension."""
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".md": "markdown",
        ".txt": "text",
        ".log": "text",
        ".cfg": "text",
        ".ini": "ini",
        ".xml": "xml",
        ".sql": "sql",
        ".sh": "bash",
        ".bash": "bash",
    }

    suffix = file_path.suffix.lower()
    return extension_map.get(suffix, "text")


async def read_file_content(state: TestAgentState) -> TestAgentState:
    llm = state.create_llm()

    request_path_message = HumanMessage(
        textwrap.dedent(
            """\
                You need to read the content of a file.
                Provide the file path you want to read.
                The path can be relative to the current working directory or absolute.
                Respond with only the file path and nothing else.
            """
        )
    )

    # Stream the AI's file path selection
    path_content = ""

    console.print()  # Add spacing before streaming

    with Live(console=console, refresh_per_second=10) as live:
        async for chunk in llm.astream(state.messages + [request_path_message]):
            if chunk.content:
                path_content += str(chunk.content)

                # Create markdown content for the path selection
                markdown_content = Markdown(path_content)
                char_count = len(path_content)

                # Display in a panel with character count
                panel = Panel(
                    markdown_content,
                    title=f"🤖 AI selecting file path... ({char_count} characters)",
                    title_align="left",
                    border_style="yellow",
                    highlight=True,
                )
                live.update(panel)

    file_path = Path(path_content.strip())

    console.print(f"📄 Reading file: [bold cyan]{file_path}[/bold cyan]")

    try:
        content = file_path.read_text(encoding="utf-8")

        # Truncate very long files to prevent context overflow
        max_chars = 10000
        was_truncated = False
        if len(content) > max_chars:
            original_length = len(content)
            content = content[:max_chars]
            was_truncated = True

        # Get appropriate language for syntax highlighting
        language = _get_file_language(file_path)

        # Create syntax highlighted content
        syntax = Syntax(
            content,
            language,
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
            background_color="default",
        )

        # Build title with file info
        file_size = file_path.stat().st_size
        size_str = f"{file_size} bytes" if file_size < 1024 else f"{file_size // 1024}KB"
        title = f"📄 File Content: {file_path} ({size_str})"

        if was_truncated:
            title += f" [dim][Truncated - showing first {max_chars} chars of {original_length}][/dim]"

        file_panel = Panel(
            syntax,
            title=title,
            title_align="left",
            border_style="green",
            highlight=True,
            padding=(1, 2),
        )
        console.print(file_panel)

        result_message = f"File content of '{file_path}':\n\n```{language}\n{content}\n```"
        if was_truncated:
            result_message += (
                f"\n\n... [File truncated - showing first {max_chars} characters of {original_length} total]"
            )

    except FileNotFoundError:
        error_panel = Panel(
            f"File '{file_path}' not found.",
            title="❌ File Not Found",
            title_align="left",
            border_style="red",
            highlight=True,
        )
        console.print(error_panel)
        result_message = f"Error: File '{file_path}' not found."
    except PermissionError:
        error_panel = Panel(
            f"Permission denied reading file '{file_path}'.",
            title="❌ Permission Error",
            title_align="left",
            border_style="red",
            highlight=True,
        )
        console.print(error_panel)
        result_message = f"Error: Permission denied reading file '{file_path}'."
    except UnicodeDecodeError:
        error_panel = Panel(
            f"File '{file_path}' is not a text file or uses an unsupported encoding.",
            title="❌ Encoding Error",
            title_align="left",
            border_style="red",
            highlight=True,
        )
        console.print(error_panel)
        result_message = f"Error: File '{file_path}' is not a text file or uses an unsupported encoding."
    except Exception as e:  # noqa: BLE001
        error_panel = Panel(
            f"Error reading file '{file_path}': {e}",
            title="❌ Unexpected Error",
            title_align="left",
            border_style="red",
            highlight=True,
        )
        console.print(error_panel)
        result_message = f"Error reading file '{file_path}': {e}"

    state.messages.append(HumanMessage(content=result_message))

    return state
