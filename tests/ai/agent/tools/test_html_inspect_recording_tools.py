from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from PIL import Image

from tresto.ai.agent.tools.inspect.recording import RecordingManager, RecordingSources
from tresto.ai.agent.tools.inspect.tools import create_bound_tools


def _img(w: int = 10, h: int = 10) -> Image.Image:
    return Image.new("RGB", (w, h), color=(255, 0, 0))


def _manager() -> RecordingManager:
    html0 = """
    <html><body>
      <div id="root">
        <h1 class="title">Hello</h1>
        <button id="go">Go</button>
      </div>
    </body></html>
    """
    html1 = """
    <html><body>
      <div id="root">
        <h1 class="title">Hello World</h1>
        <button id="go">Go!</button>
      </div>
    </body></html>
    """
    t0 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    t1 = t0.replace(second=1, microsecond=500_000)
    t2 = t0.replace(second=2)
    sources = RecordingSources(
        html_snapshots={t0.replace(microsecond=200_000): html0, t1: html1},
        screenshots={t0.replace(microsecond=300_000): _img(10, 10), t0.replace(second=1): _img(20, 10)},
    )
    return RecordingManager(trace_path=None, time_range=(t0, t2), sources=sources)


def _tool_dict(manager: RecordingManager) -> dict[str, Any]:
    tools = create_bound_tools(manager)
    return {t.name: t for t in tools}


def test_stats_tool() -> None:
    manager = _manager()
    tools = _tool_dict(manager)
    out = tools["recording_stats"].invoke({})
    assert "Recording Stats" in out
    assert "Time range" in out


def test_screenshot_tool_at_time() -> None:
    manager = _manager()
    tools = _tool_dict(manager)
    ts = datetime(2024, 1, 1, 12, 0, 0, 400_000, tzinfo=UTC)
    out = tools["screenshot"].invoke({"timestamp": ts})
    assert "Screenshot available" in out


def test_show_with_timestamp() -> None:
    manager = _manager()
    tools = _tool_dict(manager)
    ts = datetime(2024, 1, 1, 12, 0, 0, 200_000, tzinfo=UTC)
    out = tools["show"].invoke({"depth": 2, "timestamp": ts})
    assert "html" in out.lower()


def test_expand_with_timestamp_and_selector() -> None:
    manager = _manager()
    tools = _tool_dict(manager)
    ts = datetime(2024, 1, 1, 12, 0, 1, 600_000, tzinfo=UTC)
    out = tools["expand"].invoke({"selector": "#root", "depth": 2, "timestamp": ts})
    assert "Expanded view" in out


def test_attrs_with_timestamp() -> None:
    manager = _manager()
    tools = _tool_dict(manager)
    ts = datetime(2024, 1, 1, 12, 0, 0, 200_000, tzinfo=UTC)
    out = tools["attrs"].invoke({"selector": "h1.title", "timestamp": ts})
    assert "Attributes" in out


def test_text_with_timestamp() -> None:
    manager = _manager()
    tools = _tool_dict(manager)
    ts = datetime(2024, 1, 1, 12, 0, 1, 500_000, tzinfo=UTC)
    out = tools["text"].invoke({"selector": "button#go", "timestamp": ts})
    assert "Text content" in out


def test_timestamp_out_of_range_error() -> None:
    manager = _manager()
    tools = _tool_dict(manager)
    ts = datetime(2024, 1, 1, 12, 0, 5, tzinfo=UTC)
    out = tools["text"].invoke({"selector": "button#go", "timestamp": ts})
    assert out.startswith("❌")


def test_snapshot_indexing_returns_unified_point() -> None:
    manager = _manager()
    snap = manager[datetime(2024, 1, 1, 12, 0, 1, tzinfo=UTC)]
    # soup access should work
    assert "Hello World" in snap.soup.get_text()
    # screenshot access should work
    img = snap.screenshot
    assert img.width == 20 and img.height == 10
