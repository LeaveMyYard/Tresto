from __future__ import annotations

import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


console = Console()


def _count_directory_elements(path: Path, max_depth: int = 2, current_depth: int = 0) -> tuple[int, int]:
    """Count directories and total elements in the directory tree."""
    if current_depth >= max_depth:
        return 0, 0

    try:
        dirs_count = 0
        total_count = 0

        for item in path.iterdir():
            # Skip hidden files and common uninteresting directories
            if item.name.startswith(".") or item.name in {"__pycache__", "node_modules", ".git"}:
                continue

            total_count += 1

            if item.is_dir():
                dirs_count += 1
                if current_depth < max_depth - 1:
                    sub_dirs, sub_total = _count_directory_elements(item, max_depth, current_depth + 1)
                    dirs_count += sub_dirs
                    total_count += sub_total

        return dirs_count, total_count

    except PermissionError:
        return 0, 0


def _build_directory_tree(path: Path, prefix: str = "", max_depth: int = 2, current_depth: int = 0) -> str:
    """Build a directory tree representation."""
    if current_depth >= max_depth:
        return f"{prefix}[...] (max depth reached)\n"

    try:  # Separate directories and files
        dirs = []
        files = []

        for item in sorted(path.iterdir()):
            # Skip hidden files and common uninteresting directories
            if item.name.startswith(".") or item.name in {"__pycache__", "node_modules", ".git"}:
                continue

            if item.is_dir():
                dirs.append(item)
            else:
                files.append(item)

        # Show directories first, then files
        all_items = dirs + files

        tree_output = ""
        for i, item in enumerate(all_items):
            is_last = i == len(all_items) - 1
            current_prefix = "└── " if is_last else "├── "
            next_prefix = "    " if is_last else "│   "

            if item.is_dir():
                tree_output += f"{prefix}{current_prefix}{item.name}/\n"
                if current_depth < max_depth - 1:  # Only recurse if we haven't reached max depth
                    tree_output += _build_directory_tree(item, prefix + next_prefix, max_depth, current_depth + 1)
            else:
                # Add file size info for files
                try:
                    size = item.stat().st_size
                    size_str = f" ({size} bytes)" if size < 1024 else f" ({size // 1024}KB)"
                except (OSError, PermissionError):
                    size_str = ""
                tree_output += f"{prefix}{current_prefix}{item.name}{size_str}\n"

        return tree_output

    except PermissionError:
        return f"{prefix}[Permission denied]\n"


async def list_directory(state: TestAgentState) -> TestAgentState:
    llm = state.create_llm()

    request_path_message = HumanMessage(
        textwrap.dedent(
            """\
                You need to see the directory structure.
                Provide the directory path you want to explore.
                The path can be relative to the current working directory or absolute.
                You can also use "." for the current directory.
                Respond with only the directory path and nothing else.
            """
        )
    )

    # Stream the AI's path selection
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
                    title=f"🤖 AI selecting directory path... ({char_count} characters)",
                    title_align="left",
                    border_style="yellow",
                    highlight=True,
                )
                live.update(panel)

    dir_path = Path(path_content.strip())

    console.print(f"📁 Exploring directory: [bold cyan]{dir_path}[/bold cyan]")

    try:
        if not dir_path.exists():
            error_panel = Panel(
                f"Directory '{dir_path}' does not exist.",
                title="❌ Error",
                title_align="left",
                border_style="red",
                highlight=True,
            )
            console.print(error_panel)
            result_message = f"Error: Directory '{dir_path}' does not exist."
        elif not dir_path.is_dir():
            error_panel = Panel(
                f"'{dir_path}' is not a directory.",
                title="❌ Error",
                title_align="left",
                border_style="red",
                highlight=True,
            )
            console.print(error_panel)
            result_message = f"Error: '{dir_path}' is not a directory."
        else:
            # Count elements for summary
            dirs_count, total_count = _count_directory_elements(dir_path.resolve())

            # Build tree for the AI message (still include full tree)
            tree = _build_directory_tree(dir_path.resolve())
            tree_content = f"{dir_path.name}/\n{tree}"

            # Display concise summary instead of full tree
            summary_panel = Panel(
                f"Model checked [bold cyan]{dirs_count}[/bold cyan] directories, total of [bold cyan]{total_count}[/bold cyan] elements",
                title=f"📂 Directory Summary: {dir_path.resolve()}",
                title_align="left",
                border_style="green",
                highlight=True,
                padding=(1, 2),
            )
            console.print(summary_panel)

            result_message = f"Directory structure of '{dir_path.resolve()}':\n\n```\n{tree_content}```"

    except PermissionError:
        error_panel = Panel(
            f"Permission denied accessing directory '{dir_path}'.",
            title="❌ Permission Error",
            title_align="left",
            border_style="red",
            highlight=True,
        )
        console.print(error_panel)
        result_message = f"Error: Permission denied accessing directory '{dir_path}'."
    except Exception as e:  # noqa: BLE001
        error_panel = Panel(
            f"Error listing directory '{dir_path}': {e}",
            title="❌ Unexpected Error",
            title_align="left",
            border_style="red",
            highlight=True,
        )
        console.print(error_panel)
        result_message = f"Error listing directory '{dir_path}': {e}"

    state.messages.append(HumanMessage(content=result_message))

    return state
