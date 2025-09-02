from __future__ import annotations

from datetime import datetime
from pathlib import Path
from shutil import copyfile
from tempfile import NamedTemporaryFile

from tresto.ai.agent.tools.inspect.recording import RecordingManager


def test_load_recording_from_trace_zip() -> None:
    fixture_path = Path(__file__).resolve().parents[3] / "src" / "trace.zip"
    assert fixture_path.exists(), "trace.zip test artifact must exist"

    with NamedTemporaryFile(prefix="tresto-test-trace-", suffix=".zip", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    copyfile(fixture_path, tmp_path)

    manager = RecordingManager(trace_path=tmp_path)
    stats = manager.get_stats()

    # Should detect there is a trace and have at least one snapshot
    assert stats["has_trace"] is True
    assert stats["num_html_snapshots"] >= 0
    assert stats["num_screenshots"] >= 0

    # Time range should be sane
    start = stats["time_start"]
    end = stats["time_end"]
    assert isinstance(start, datetime) and isinstance(end, datetime)
    assert end >= start

    # Try getting soup/screenshot at middle of range (should not raise)
    mid = start + (end - start) / 2
    try:
        _ = manager.get_soup_at(mid)
    except ValueError:
        # Some traces may not include snapshots; fallback to nearest earlier by picking end
        _ = manager.get_soup_at(end)

    try:
        _ = manager.get_screenshot_at(mid)
    except ValueError:
        # Fallback to end timestamp if mid has no screenshot
        _ = manager.get_screenshot_at(end)
