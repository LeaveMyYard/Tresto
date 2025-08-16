from __future__ import annotations

import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.messages import SystemMessage

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


def _build_directory_tree(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
    """Build a directory tree representation."""
    if current_depth >= max_depth:
        return f"{prefix}[...] (max depth reached)\n"
    
    try:# Separate directories and files
        dirs = []
        files = []
        
        for item in sorted(path.iterdir()):
            # Skip hidden files and common uninteresting directories
            if item.name.startswith('.') or item.name in {'__pycache__', 'node_modules', '.git'}:
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
                    tree_output += _build_directory_tree(
                        item, 
                        prefix + next_prefix, 
                        max_depth, 
                        current_depth + 1
                    )
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

    request_path_message = SystemMessage(
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

    path_response = await llm.ainvoke(state.messages + [request_path_message])
    dir_path = Path(path_response.content.strip())

    try:
        if not dir_path.exists():
            result_message = f"Error: Directory '{dir_path}' does not exist."
        elif not dir_path.is_dir():
            result_message = f"Error: '{dir_path}' is not a directory."
        else:
            tree = _build_directory_tree(dir_path.resolve())
            result_message = f"Directory structure of '{dir_path.resolve()}':\n\n```\n{dir_path.name}/\n{tree}```"
            
    except PermissionError:
        result_message = f"Error: Permission denied accessing directory '{dir_path}'."
    except Exception as e:
        result_message = f"Error listing directory '{dir_path}': {e}"

    state.messages.append(SystemMessage(content=result_message))
    await state.output_to_console(f"Listed directory: {dir_path}")
    
    return state 