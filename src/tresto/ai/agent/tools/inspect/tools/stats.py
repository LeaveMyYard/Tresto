from langchain.tools import Tool, tool

from tresto.ai.agent.tools.inspect.recording import RecordingManager


def create_bound_stats_tool(manager: RecordingManager) -> Tool:
    @tool(description="Show recording stats and available timestamp range")
    def recording_stats() -> str:
        stats = manager.get_stats()
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
        )

    return recording_stats


