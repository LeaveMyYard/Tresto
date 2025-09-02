from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from PIL.Image import Image


@dataclass
class RecordingSources:
    html_snapshots: dict[datetime, str]
    screenshots: dict[datetime, Image]
    logs: list[tuple[datetime, str]] = field(default_factory=list)

    @property
    def time_range(self) -> tuple[datetime, datetime]:
        if not self.html_snapshots and not self.screenshots:
            now = datetime.now(UTC)
            return (now, now)
        times: Iterable[datetime] = list(self.html_snapshots.keys()) + list(self.screenshots.keys())
        return (min(times), max(times))


class RecordingManager:
    """Recording manager that provides time-based access to HTML and screenshots.

    Supports two sources:
    - Loaded from a Playwright trace file (future extension)
    - Provided in-memory via RecordingSources (used for tests and synthetic data)
    - Latest artifacts (HTML/screenshot) from the end of the run
    """

    def __init__(
        self,
        trace_path: Path | None = None,
        time_range: tuple[datetime, datetime] | None = None,
        sources: RecordingSources | None = None,
    ) -> None:
        self._trace_path = trace_path
        self._time_range = time_range
        if sources is not None:
            self._sources = sources
        elif trace_path is not None:
            loaded = self._load_sources_from_trace(trace_path)
            self._sources = loaded
        else:
            self._sources = RecordingSources(html_snapshots={}, screenshots={})

        # If no explicit range, infer from sources or latest artifacts
        if self._time_range is None:
            if self._sources.html_snapshots or self._sources.screenshots:
                self._time_range = self._sources.time_range
            else:
                # Default to [now, now] if nothing else; consumers must validate
                now = datetime.now(UTC)
                self._time_range = (now, now)

    def to_text(self) -> str:
        stats = self.get_stats()
        start = stats["time_start"]
        end = stats["time_end"]
        duration_s = stats["duration_s"]
        start_str = start.isoformat() if start else "n/a"
        end_str = end.isoformat() if end else "n/a"
        return (
            "🎞️ Recording Stats:\n"
            f"Trace: {'yes' if stats['has_trace'] else 'no'}\n"
            f"Trace path: {stats['trace_path']}\n"
            f"Time range: {start_str} — {end_str} (duration {duration_s:.3f}s)\n"
            f"HTML snapshots: {stats['num_html_snapshots']}\n"
            f"Screenshots: {stats['num_screenshots']}\n"
            f"Logs: {stats['num_logs']}"
        )

    # --- Trace loading ---
    def _load_sources_from_trace(self, trace_path: Path) -> RecordingSources:
        html_snapshots: dict[datetime, str] = {}
        screenshots: dict[datetime, Image] = {}
        logs: list[tuple[datetime, str]] = []

        try:
            with zipfile.ZipFile(trace_path, "r") as zf:
                # Find a trace JSON file; commonly named trace.trace
                trace_files = [n for n in zf.namelist() if n.endswith(".trace")]
                if not trace_files:
                    return RecordingSources(html_snapshots=html_snapshots, screenshots=screenshots)

                # Load all events from all .trace files
                events: list[dict] = []
                for tf in trace_files:
                    with zf.open(tf) as f:
                        data = f.read()
                        try:
                            # Some traces are a single JSON (array or object)
                            obj = json.loads(data)
                            if isinstance(obj, list):
                                events.extend(obj)
                            elif isinstance(obj, dict) and "events" in obj:
                                events.extend(obj["events"])  # type: ignore[index]
                            else:
                                # Maybe it's NDJSON lines
                                raise ValueError("Unexpected JSON structure")
                        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                            # Try NDJSON parsing
                            for line in data.splitlines():
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    events.append(json.loads(line))
                                except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                                    continue

                # Build a map of sha1 -> resource path for images
                resource_names = {n.split("/")[-1]: n for n in zf.namelist() if n.startswith("resources/")}

                def to_dt(val: int | float) -> datetime:
                    # Convert numeric timestamp to UTC datetime by heuristics
                    # Epoch seconds ~ 1e9, milliseconds ~ 1e12, microseconds ~ 1e15, nanoseconds ~ 1e18
                    x = float(val)
                    if x > 1e17:
                        # nanoseconds
                        return datetime.fromtimestamp(x / 1e9, tz=UTC)
                    if x > 1e14:
                        # microseconds
                        return datetime.fromtimestamp(x / 1e6, tz=UTC)
                    if x > 1e11:
                        # milliseconds
                        return datetime.fromtimestamp(x / 1e3, tz=UTC)
                    # seconds
                    return datetime.fromtimestamp(x, tz=UTC)

                # Helper to choose the best wall clock timestamp for an event
                def choose_event_dt(ev_obj: dict) -> datetime | None:
                    # Prefer wall-clock times when available (epoch ms)
                    # Common fields in Playwright traces across event shapes
                    wall = (
                        ev_obj.get("wallTime")
                        or ev_obj.get("frameSwapWallTime")
                        or (ev_obj.get("snapshot") or {}).get("wallTime")
                    )
                    if isinstance(wall, int | float):
                        return to_dt(wall)

                    # Fallback to relative/monotonic timestamps
                    ts_val_local = (
                        ev_obj.get("timestamp")
                        or ev_obj.get("time")
                        or ev_obj.get("ts")
                        or ev_obj.get("endTime")
                        or ev_obj.get("startTime")
                    )
                    if isinstance(ts_val_local, int | float):
                        return to_dt(ts_val_local)
                    return None

                # Parse events and extract html, screenshots, and logs
                for ev in events:
                    ts: datetime | None = choose_event_dt(ev)

                    # HTML snapshots: look for common shapes
                    # 1) ev.get("snapshot", {}).get("html")
                    snap = ev.get("snapshot")
                    if isinstance(snap, dict) and ts is not None:
                        html_val = snap.get("html")
                        html_str = self._html_value_to_string(html_val)
                        if html_str is not None:
                            html_snapshots[ts] = html_str
                            continue

                    # 2) ev.get("data", {}).get("snapshot", {}).get("html")
                    data = ev.get("data")
                    if isinstance(data, dict) and isinstance(data.get("snapshot"), dict) and ts is not None:
                        html_val = data["snapshot"].get("html")
                        html_str = self._html_value_to_string(html_val)
                        if html_str is not None:
                            html_snapshots[ts] = html_str
                            continue

                    # 3) "after" events for Frame.content often have result.value with full HTML string
                    result_obj = ev.get("result")
                    if isinstance(result_obj, dict) and isinstance(result_obj.get("value"), str) and ts is not None:
                        val = result_obj["value"]
                        # Heuristic: looks like HTML content
                        if "<html" in val or "<body" in val or val.strip().startswith("<"):
                            html_snapshots[ts] = val
                            continue

                    # Screenshots: look for screencast frame with sha1
                    sha1 = ev.get("sha1")
                    if not sha1 and isinstance(data, dict):
                        sha1 = data.get("sha1")
                    if isinstance(sha1, str) and ts is not None:
                        res_name = resource_names.get(sha1)
                        if res_name:
                            try:
                                with zf.open(res_name) as rf:
                                    buf = io.BytesIO(rf.read())
                                    from PIL import Image as PILImage

                                    img = PILImage.open(buf)
                                    screenshots[ts] = img
                            except (OSError, zipfile.BadZipFile):
                                # Ignore unreadable resource
                                pass

                    # Logs: console/page errors/network summaries
                    if ts is not None:
                        level: str | None = None
                        msg: str | None = None

                        ev_type = ev.get("type")
                        ev_event = ev.get("event")
                        ev_name = ev.get("name")

                        # Console messages
                        if (
                            (isinstance(ev_type, str) and "console" in ev_type.lower())
                            or (isinstance(ev_event, str) and "console" in ev_event.lower())
                            or (isinstance(ev_name, str) and "console" in ev_name.lower())
                        ):
                            level = (
                                (ev.get("level") or (data or {}).get("type") or "log")
                                if isinstance(data, dict)
                                else (ev.get("level") or "log")
                            )
                            msg = (
                                ((data or {}).get("text") if isinstance(data, dict) else None)
                                or ev.get("text")
                                or ev.get("message")
                            )

                        # Page errors
                        if msg is None and (
                            (isinstance(ev_type, str) and "error" in ev_type.lower())
                            or (isinstance(ev_event, str) and "error" in ev_event.lower())
                        ):
                            level = "error"
                            if isinstance(data, dict):
                                msg = data.get("error") or data.get("message") or data.get("name")
                            msg = msg or ev.get("error") or ev.get("message")

                        # Network requests (basic summary)
                        if msg is None and isinstance(data, dict):
                            url = data.get("url")
                            method = data.get("method")
                            status = data.get("status") or data.get("statusCode")
                            if url and (method or status):
                                level = "network"
                                if method and status:
                                    msg = f"{method} {url} -> {status}"
                                elif method:
                                    msg = f"{method} {url}"
                                else:
                                    msg = f"{url} -> {status}"

                        if msg:
                            text = str(msg)
                            if level:
                                text = f"[{level}] {text}"
                            logs.append((ts, text))

        except (OSError, zipfile.BadZipFile, KeyError, ValueError):
            # If anything fails, return what we managed to parse (possibly empty)
            return RecordingSources(html_snapshots=html_snapshots, screenshots=screenshots, logs=logs)

        return RecordingSources(html_snapshots=html_snapshots, screenshots=screenshots, logs=logs)

    @staticmethod
    def _html_value_to_string(value: object) -> str | None:
        """Convert Playwright snapshot html payload to a string, if possible.

        Payload may be a string (ready to use) or a nested list representation like
        ["HTML", {attrs}, [children...]]. We try to serialize the latter into HTML.
        """
        if isinstance(value, str):
            return value

        def render(node: object) -> str:
            if isinstance(node, str):
                return node
            if isinstance(node, list) and node:
                # If first element is a tag name
                head = node[0]
                if isinstance(head, str):
                    tag = head.lower()
                    attrs: dict[str, object] = {}
                    children: list[object] = []
                    # Optional attrs in second position
                    idx_after_attrs = 1
                    if len(node) > 1 and isinstance(node[1], dict):
                        attrs = node[1]  # type: ignore[assignment]
                        idx_after_attrs = 2
                    # Children may be represented either as a single list at position 2,
                    # or as a sequence of child nodes spread across positions >= 2.
                    if len(node) > idx_after_attrs:
                        maybe_children = node[idx_after_attrs]
                        if (
                            isinstance(maybe_children, list)
                            and not (
                                maybe_children
                                and isinstance(maybe_children[0], str)
                                and maybe_children[0].lower()
                                in {"html", "head", "body", "div", "span", "style", "script"}
                            )
                            and len(node) == idx_after_attrs + 1
                        ):
                            # Likely a dedicated children list container
                            children = maybe_children
                        else:
                            # Treat everything from idx_after_attrs onward as children
                            children = list(node[idx_after_attrs:])
                    # serialize attributes
                    attr_str = "".join(f' {k}="{str(v)}"' for k, v in attrs.items())
                    inner = "".join(render(child) for child in children)
                    return f"<{tag}{attr_str}>{inner}</{tag}>"
                # Otherwise, it's a list of nodes
                return "".join(render(child) for child in node)
            return ""

        if isinstance(value, list):
            try:
                html = render(value)
                return html if html else None
            except Exception:  # noqa: BLE001
                return None
        return None

    @property
    def trace_path(self) -> Path | None:
        return self._trace_path

    @property
    def time_range(self) -> tuple[datetime, datetime]:
        assert self._time_range is not None
        return self._time_range

    def validate_timestamp(self, timestamp: datetime | None) -> datetime:
        """Validate timestamp against the available range.

        If timestamp is None, returns the end of the range.
        Raises ValueError if outside range.
        """
        start, end = self.time_range
        ts = end if timestamp is None else timestamp
        if ts < start or ts > end:
            raise ValueError(
                f"Timestamp {ts.isoformat()} is outside of recording range [{start.isoformat()}, {end.isoformat()}]"
            )
        return ts

    def get_html_at(self, timestamp: datetime | None) -> str:
        ts = self.validate_timestamp(timestamp)

        # Prefer exact snapshot or nearest neighbor (by absolute delta, tie -> earlier)
        snaps = self._sources.html_snapshots
        if ts in snaps:
            return snaps[ts]
        if snaps:

            def keyfunc(t: datetime) -> tuple[float, int]:
                return (abs((t - ts).total_seconds()), 0 if t <= ts else 1)

            closest = min(snaps.keys(), key=keyfunc)
            return snaps[closest]

        raise ValueError("No HTML available for the requested timestamp")

    def get_soup_at(self, timestamp: datetime | None) -> BeautifulSoup:
        return BeautifulSoup(self.get_html_at(timestamp), "html.parser")

    def get_screenshot_at(self, timestamp: datetime | None) -> Image:
        ts = self.validate_timestamp(timestamp)

        # Prefer exact snapshot or nearest neighbor (by absolute delta, tie -> earlier)
        shots = self._sources.screenshots
        if ts in shots:
            return shots[ts]
        if shots:

            def keyfunc(t: datetime) -> tuple[float, int]:
                return (abs((t - ts).total_seconds()), 0 if t <= ts else 1)

            closest = min(shots.keys(), key=keyfunc)
            return shots[closest]

        raise ValueError("No screenshot available for the requested timestamp")

    def get_stats(self) -> dict:
        start, end = self.time_range
        return {
            "has_trace": self._trace_path is not None,
            "trace_path": str(self._trace_path) if self._trace_path else None,
            "time_start": start,
            "time_end": end,
            "duration_s": max(0.0, (end - start).total_seconds()),
            "num_html_snapshots": len(self._sources.html_snapshots),
            "num_screenshots": len(self._sources.screenshots),
            "num_logs": len(self._sources.logs),
        }

    def get_logs(self, start_time: datetime, end_time: datetime | None) -> list[tuple[datetime, str]]:
        start, end_default = self.time_range
        end = end_default if end_time is None else end_time
        if start_time > end:
            return []
        return [(ts, text) for ts, text in self._sources.logs if start_time <= ts <= end]

    # Snapshot accessors
    def __getitem__(self, timestamp: datetime | None) -> RecordingSnapshot:
        ts = self.validate_timestamp(timestamp)
        return RecordingSnapshot(manager=self, timestamp_s=ts)


@dataclass
class RecordingSnapshot:
    """A point-in-time snapshot from a recording, providing unified access to artifacts."""

    manager: RecordingManager
    timestamp_s: datetime

    @property
    def soup(self) -> BeautifulSoup:
        return self.manager.get_soup_at(self.timestamp_s)

    @property
    def screenshot(self) -> Image:
        return self.manager.get_screenshot_at(self.timestamp_s)
