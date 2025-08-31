from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from PIL.Image import Image

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


@dataclass
class RecordingSources:
    html_snapshots: dict[datetime, str]
    screenshots: dict[datetime, Image]

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
        latest_html: str | None = None,
        latest_screenshot: Image | None = None,
        sources: RecordingSources | None = None,
    ) -> None:
        self._trace_path = trace_path
        self._time_range = time_range
        self._latest_html = latest_html
        self._latest_screenshot = latest_screenshot
        self._sources = sources or RecordingSources(html_snapshots={}, screenshots={})

        # If no explicit range, infer from sources or latest artifacts
        if self._time_range is None:
            if self._sources.html_snapshots or self._sources.screenshots:
                self._time_range = self._sources.time_range
            else:
                # Default to [now, now] if nothing else; consumers must validate
                now = datetime.now(UTC)
                self._time_range = (now, now)

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

        # Prefer exact snapshot
        if ts in self._sources.html_snapshots:
            return self._sources.html_snapshots[ts]

        # Fallback to the closest earlier snapshot
        if self._sources.html_snapshots:
            earlier_times = [t for t in self._sources.html_snapshots.keys() if t <= ts]
            if earlier_times:
                closest = max(earlier_times)
                return self._sources.html_snapshots[closest]

        # Fallback to latest html at end of run
        if self._latest_html is not None:
            return self._latest_html

        raise ValueError("No HTML available for the requested timestamp")

    def get_soup_at(self, timestamp: datetime | None) -> BeautifulSoup:
        return BeautifulSoup(self.get_html_at(timestamp), "html.parser")

    def get_screenshot_at(self, timestamp: datetime | None) -> Image:
        ts = self.validate_timestamp(timestamp)

        # Prefer exact snapshot
        if ts in self._sources.screenshots:
            return self._sources.screenshots[ts]

        # Fallback to closest earlier screenshot
        if self._sources.screenshots:
            earlier_times = [t for t in self._sources.screenshots.keys() if t <= ts]
            if earlier_times:
                closest = max(earlier_times)
                return self._sources.screenshots[closest]

        # Fallback to latest end-of-run screenshot
        if self._latest_screenshot is not None:
            return self._latest_screenshot

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
            "has_latest_html": self._latest_html is not None,
            "has_latest_screenshot": self._latest_screenshot is not None,
        }

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



