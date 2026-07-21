from __future__ import annotations

from tresto.mcp_server import main


def mcp_command() -> None:
    """Run the Tresto MCP server over stdio."""

    main()
