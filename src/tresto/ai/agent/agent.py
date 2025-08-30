from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, BaseMessageChunk, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from rich.console import Console, RenderableType
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState

console = Console()


def _get_last_n_lines(text: str, max_lines: int) -> str:
    """Get the last n lines from text."""
    if not text.strip() or max_lines <= 0:
        return text

    lines = text.split("\n")
    if len(lines) <= max_lines:
        return text

    # Take the last max_lines lines
    last_lines = lines[-max_lines:]
    return "\n".join(last_lines)


@dataclass
class Agent:
    state: TestAgentState
    llm: BaseChatModel
    system_message: SystemMessage
    tools: dict[str, BaseTool]

    @property
    def total_messages(self) -> list[BaseMessage]:
        return [self.system_message] + self.state.messages

    async def structured_response[T: BaseModel](
        self,
        response_format: type[T],
        message: BaseMessage | None = None,
    ) -> T:
        llm = self.llm.with_structured_output(response_format)
        result = await llm.ainvoke(self.total_messages + ([message] if message else []))
        console.print(result.model_dump_json(indent=2))
        return result

    async def invoke(
        self,
        message: BaseMessage | None = None,
        panel_title: str = "🤖 AI processing... ({char_count} characters)",
        border_style: str = "yellow",
        max_lines: int | None = None,
    ) -> str:
        """Invoke the AI agent with a message and handle the streaming response.

        Args:
            message: Optional message to send to the agent
            panel_title: Title template for the display panel
            border_style: Style for the panel border
            max_lines: If specified, only show the last N lines in the panel
        """
        messages = self.total_messages + ([message] if message else [])
        result = await self._stream_response(messages, panel_title, border_style, max_lines)

        if not result:
            return ""

        response = result.text()

        # Handle AI message and tool calls
        await self._handle_ai_response(result)

        return response

    async def _stream_response(
        self, messages: list[BaseMessage], panel_title: str, border_style: str, max_lines: int | None = None
    ) -> BaseMessageChunk | None:
        """Stream the AI response with live updates."""
        result: BaseMessageChunk | None = None

        console.print()  # Add spacing before streaming

        with Live(console=console, refresh_per_second=10) as live:
            async for chunk in self.llm.astream(messages):
                if result is None:
                    result = chunk
                else:
                    result += chunk

                panel = self._create_response_panel(result, panel_title, border_style, max_lines)
                live.update(panel)

        return result

    @staticmethod
    def _process_message(message: BaseMessageChunk, max_lines: int | None = None) -> RenderableType:
        # Return markdown with the message content.
        # Parse each message. Text should be rendered as is. Tool calls should be a text with tool name and args.

        if isinstance(message.content, str):
            content_text = message.content
        else:
            content = []
            for item in message.content:
                if isinstance(item, str):
                    content.append(item)
                elif isinstance(item, dict):
                    if item.get("type") == "tool_call":
                        content.append(f"Tool call: {item.get('name', '')} with args: {item.get('args', '')}")
                    elif "text" in item:
                        content.append(item.get("text", ""))
                    else:
                        content.append(f"{item}")
            content_text = "\n".join(content)

        # Apply line limiting if specified
        if max_lines is not None and max_lines > 0:
            content_text = _get_last_n_lines(content_text, max_lines)

        return Markdown(content_text)

    @staticmethod
    def _create_response_panel(
        result: BaseMessageChunk, panel_title: str, border_style: str, max_lines: int | None = None
    ) -> Panel:
        """Create a panel for displaying the streaming response."""
        markdown_content = Agent._process_message(result, max_lines)

        raw_text = result.text()
        char_count = len(raw_text)
        total_lines = len(raw_text.split("\n")) if raw_text else 0

        # Update title to show line info if max_lines is set
        if max_lines is not None and max_lines > 0:
            title = panel_title.format(
                char_count=char_count, total_lines=total_lines, showing_lines=min(max_lines, total_lines)
            )
        else:
            title = panel_title.format(char_count=char_count)

        return Panel(
            markdown_content,
            title=title,
            title_align="left",
            border_style=border_style,
            highlight=True,
        )

    async def _handle_ai_response(self, result: BaseMessageChunk) -> None:
        """Handle the AI response by adding it to state and processing tool calls."""

        tool_calls: list[dict] | None = getattr(result, "tool_calls", None)

        # Add the AI message to the conversation history
        ai_message = AIMessage(content=result.content, tool_calls=tool_calls)
        self.state.add_message(ai_message)

        # Process tool calls if any
        if tool_calls:
            await self._process_tool_calls(tool_calls)

    async def _process_tool_calls(self, tool_calls: list[dict]) -> None:
        """Process and execute tool calls."""
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")
            tool = self.tools.get(tool_name)

            if tool:
                tool_result = tool.invoke(tool_call)
                console.print(
                    Panel(
                        tool_result.content,
                        title=f"🔧 {tool_name}",
                        title_align="left",
                        border_style="green",
                        highlight=True,
                    )
                )

                tool_message = ToolMessage(content=tool_result.content, tool_call_id=tool_call.get("id", ""))
                self.state.add_message(tool_message)
            else:
                error_msg = f"❌ Model tried to call tool {tool_name} but it was not found"
                console.print(
                    Panel(error_msg, title="❌ Tool Not Found", title_align="left", border_style="red", highlight=True)
                )
                self.state.add_message(AIMessage(content=error_msg))
