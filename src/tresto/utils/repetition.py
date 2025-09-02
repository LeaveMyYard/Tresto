from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def collapse_repeated_lines(text: str, min_repeat: int = 5) -> str:
    """Collapse contiguous repeated lines into a single line with a repetition marker.

    Example:
        A\nA\nA\nB -> A\n<!-- Previous line repeated 2 more times -->\nB

    Args:
        text: Multiline string to process.
        min_repeat: Minimum number of contiguous repeats required to collapse.

    Returns:
        Collapsed multiline string.
    """
    if not text:
        return text

    lines: list[str] = text.splitlines()
    if not lines:
        return text

    out: list[str] = []
    idx = 0
    n = len(lines)

    while idx < n:
        current = lines[idx]
        run_len = 1
        j = idx + 1
        while j < n and lines[j] == current:
            run_len += 1
            j += 1

        if run_len >= min_repeat:
            out.append(current)
            out.append(f"<!-- Previous line repeated {run_len - 1} more times -->")
        else:
            out.extend(lines[idx : idx + run_len])

        idx += run_len

    return "\n".join(out)


def collapse_repeated_blocks(text: str, block_tokens: Iterable[str], min_repeat: int = 5) -> str:
    """Collapse simple repeated single-line blocks if they equal to any of block_tokens.

    Useful when we want to target tokens like "<style>" specifically.
    """
    targets = set(block_tokens)
    if not text:
        return text
    lines = text.splitlines()
    out: list[str] = []
    idx = 0
    n = len(lines)
    while idx < n:
        line = lines[idx]
        if line in targets:
            run_len = 1
            j = idx + 1
            while j < n and lines[j] == line:
                run_len += 1
                j += 1
            if run_len >= min_repeat:
                out.append(line)
                out.append(f"<!-- Previous line repeated {run_len - 1} more times -->")
                idx += run_len
                continue
        out.append(line)
        idx += 1
    return "\n".join(out)
