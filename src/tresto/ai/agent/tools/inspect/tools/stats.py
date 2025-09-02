from langchain.tools import Tool, tool

from tresto.ai.agent.tools.inspect.recording import RecordingManager


def create_bound_stats_tool(manager: RecordingManager) -> Tool:
    @tool(description="Show recording stats and available timestamp range")
    def recording_stats() -> str:
        # Prefer the formatted text summary
        return manager.to_text()

    return recording_stats
