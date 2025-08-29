"""HTML inspection tools."""

from bs4 import BeautifulSoup
from langchain.tools import Tool

from .attrs import create_bound_attrs_tool
from .expand import create_bound_expand_tool
from .show import create_bound_show_tool
from .text import create_bound_text_tool


def create_bound_tools(soup: BeautifulSoup) -> list[Tool]:
    return [
        create_bound_attrs_tool(soup),
        create_bound_expand_tool(soup),
        create_bound_show_tool(soup),
        create_bound_text_tool(soup),
    ]

__all__ = [
    "create_bound_tools",
]
