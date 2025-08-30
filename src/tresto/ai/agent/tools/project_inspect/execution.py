"""Execution utilities for file exploration and inspection."""

from __future__ import annotations

import os
from pathlib import Path

from .models import FileExplorationResult


def execute_file_exploration_command(command: str, project_path: Path) -> FileExplorationResult:
    """Execute file exploration command and return result."""
    try:
        command = command.strip()

        # Split command into parts but preserve case for file paths
        parts = command.split(" ", 1)
        cmd_keyword = parts[0].lower()
        cmd_args = parts[1] if len(parts) > 1 else ""

        if cmd_keyword == "list":
            # List directory contents
            path_str = cmd_args.strip()
            if not path_str or path_str == ".":
                target_path = project_path
            else:
                target_path = project_path / path_str

            return _list_directory(target_path)

        if cmd_keyword == "read":
            # Read file contents
            file_path_str = cmd_args.strip()
            target_file = project_path / file_path_str

            return _read_file(target_file)

        if cmd_keyword == "find":
            # Find files by pattern
            pattern = cmd_args.strip()
            return _find_files(project_path, pattern)

        if cmd_keyword in ["help", "?"]:
            return FileExplorationResult(
                success=True,
                output="""📁 File Exploration Commands:
                
• list <path> - List directory contents (e.g., 'list src', 'list .')
• read <file> - Read file contents (e.g., 'read package.json', 'read src/App.js')
• find <pattern> - Find files matching pattern (e.g., 'find *.py', 'find component')
• finish - Complete exploration and generate report
• help - Show this help

Examples:
• list . - List project root
• list src - List src directory  
• read src/components/Login.tsx - Read login component
• find *.test.* - Find test files
• find login - Find files with 'login' in name""",
            )

        if cmd_keyword in ["finish", "done", "complete"]:
            return FileExplorationResult(
                success=True, output="🏁 EXPLORATION_FINISHED - Project inspection complete, ready to generate report"
            )

        return FileExplorationResult(
            success=False, output="", error=f"Unknown command: {cmd_keyword}. Use 'help' to see available commands."
        )

    except Exception as e:  # noqa: BLE001
        return FileExplorationResult(success=False, output="", error=str(e))


def _list_directory(path: Path) -> FileExplorationResult:
    """List directory contents with file information."""
    try:
        if not path.exists():
            return FileExplorationResult(success=False, output="", error=f"Directory does not exist: {path}")

        if not path.is_dir():
            return FileExplorationResult(success=False, output="", error=f"Path is not a directory: {path}")

        items = []
        for item in sorted(path.iterdir()):
            if item.name.startswith("."):
                continue  # Skip hidden files

            if item.is_dir():
                items.append(f"📁 {item.name}/")
            else:
                # Get file size
                try:
                    size = item.stat().st_size
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024 * 1024:
                        size_str = f"{size // 1024}KB"
                    else:
                        size_str = f"{size // (1024 * 1024)}MB"
                except Exception:  # noqa: BLE001
                    size_str = "?"

                items.append(f"📄 {item.name} ({size_str})")

        if not items:
            output = f"📁 Directory '{path}' is empty"
        else:
            output = f"📁 Contents of '{path}':\n\n" + "\n".join(items)

        return FileExplorationResult(success=True, output=output)

    except Exception as e:  # noqa: BLE001
        return FileExplorationResult(success=False, output="", error=str(e))


def _read_file(file_path: Path) -> FileExplorationResult:
    """Read and return file contents."""
    try:
        if not file_path.exists():
            return FileExplorationResult(success=False, output="", error=f"File does not exist: {file_path}")

        if not file_path.is_file():
            return FileExplorationResult(success=False, output="", error=f"Path is not a file: {file_path}")

        # Check file size
        size = file_path.stat().st_size
        if size > 100 * 1024:  # 100KB limit
            return FileExplorationResult(
                success=False,
                output="",
                error=f"File too large ({size // 1024}KB). Only files under 100KB can be read.",
            )

        # Try to read as text
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return FileExplorationResult(
                success=False, output="", error=f"File is not a text file (binary content): {file_path}"
            )

        # Limit output length
        if len(content) > 10000:  # 10K chars limit for display
            content = (
                content[:10000] + f"\n\n... (file truncated, showing first 10K characters of {len(content)} total)"
            )

        return FileExplorationResult(success=True, output=f"📄 Contents of '{file_path}':\n\n{content}")

    except Exception as e:  # noqa: BLE001
        return FileExplorationResult(success=False, output="", error=str(e))


def _find_files(project_path: Path, pattern: str) -> FileExplorationResult:
    """Find files matching pattern."""
    try:
        import fnmatch

        matches = []
        pattern_lower = pattern.lower()

        # Walk through project directory
        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            root_path = Path(root)

            for file in files:
                if file.startswith("."):
                    continue

                file_path = root_path / file
                relative_path = file_path.relative_to(project_path)

                # Match by pattern or substring
                if (
                    fnmatch.fnmatch(file.lower(), pattern_lower)
                    or pattern_lower in file.lower()
                    or pattern_lower in str(relative_path).lower()
                ):
                    # Get file size
                    try:
                        size = file_path.stat().st_size
                        if size < 1024:
                            size_str = f"{size}B"
                        elif size < 1024 * 1024:
                            size_str = f"{size // 1024}KB"
                        else:
                            size_str = f"{size // (1024 * 1024)}MB"
                    except Exception:  # noqa: BLE001
                        size_str = "?"

                    matches.append(f"📄 {relative_path} ({size_str})")

        if not matches:
            output = f"🔍 No files found matching pattern: {pattern}"
        else:
            output = f"🔍 Found {len(matches)} files matching '{pattern}':\n\n" + "\n".join(matches[:20])
            if len(matches) > 20:
                output += f"\n\n... and {len(matches) - 20} more files (showing first 20)"

        return FileExplorationResult(success=True, output=output)

    except Exception as e:  # noqa: BLE001
        return FileExplorationResult(success=False, output="", error=str(e))
