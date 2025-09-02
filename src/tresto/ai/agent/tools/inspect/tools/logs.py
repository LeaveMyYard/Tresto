from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from langchain.tools import Tool, tool
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from tresto.ai.agent.tools.inspect.recording import RecordingManager


class LogsArgs(BaseModel):
    start_time: str = Field(description="Start time (ISO-8601, UTC if no tz)")
    end_time: str | None = Field(None, description="End time (ISO-8601, optional)")


def _parse_iso_to_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def create_bound_logs_tool(manager: RecordingManager) -> Tool:
    @tool(description="Get browser logs between start_time and end_time", args_schema=LogsArgs)
    def logs(start_time: str, end_time: str | None = None) -> str:
        try:
            start_dt = _parse_iso_to_utc(start_time)
            end_dt = _parse_iso_to_utc(end_time) if end_time else None
        except Exception as e:  # noqa: BLE001
            return f"❌ Invalid time format: {e}"

        try:
            entries = manager.get_logs(start_dt, end_dt)
        except ValueError as e:
            return f"❌ {e}"

        if not entries:
            return "📝 No logs in the specified time range"

        lines = [f"{ts.isoformat()} — {text}" for ts, text in sorted(entries, key=lambda x: x[0])]

        return "\n".join(lines[:500])  # guard overly long output

    return logs
