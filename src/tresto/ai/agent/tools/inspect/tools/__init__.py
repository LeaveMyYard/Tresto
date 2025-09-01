"""HTML inspection tools bound to a RecordingManager."""

from langchain.tools import Tool

from tresto.ai.agent.tools.inspect.recording import RecordingManager

from .attrs import create_bound_attrs_tool
from .expand import create_bound_expand_tool
from .logs import create_bound_logs_tool  # type: ignore[import-not-found]
from .screenshot import create_bound_screenshot_tool  # type: ignore[import-not-found]
from .show import create_bound_show_tool
from .stats import create_bound_stats_tool  # type: ignore[import-not-found]
from .text import create_bound_text_tool


def create_bound_tools(manager: RecordingManager) -> list[Tool]:
    return [
        create_bound_attrs_tool(manager),
        create_bound_expand_tool(manager),
        create_bound_show_tool(manager),
        create_bound_text_tool(manager),
        create_bound_screenshot_tool(manager),
        create_bound_stats_tool(manager),
        create_bound_logs_tool(manager),
    ]


__all__ = [
    "create_bound_tools",
]
