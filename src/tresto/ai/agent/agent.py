from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, BaseMessage, BaseMessageChunk, HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel
from rich.console import Console, RenderableType
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from tresto.ai import prompts

if TYPE_CHECKING:
    from langchain.chat_models.base import BaseChatModel
    from langchain_core.tools import BaseTool

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
    task_message: str
    tools: dict[str, BaseTool]

    @property
    def total_messages(self) -> list[BaseMessage]:
        return (
            [SystemMessage(prompts.system(self.state.config.secrets.keys()))]
            + self.state.messages
            + [HumanMessage("== NEW TASK ==\n" + self.task_message)]
        )

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
        """Stream the AI response with retries on transient overloads."""
        max_retries = 3
        base_delay_s = 1.0

        for attempt in range(max_retries + 1):
            result: BaseMessageChunk | None = None
            console.print()
            try:
                with Live(console=console, refresh_per_second=10) as live:
                    async for chunk in self.llm.astream(messages):
                        if result is None:
                            result = chunk
                        else:
                            result += chunk

                        panel = self._create_response_panel(result, panel_title, border_style, max_lines)
                        live.update(panel)
                return result
            except Exception as e:  # noqa: BLE001
                message = str(e).lower()
                overloaded = (
                    "overloaded" in message
                    or "rate limit" in message
                    or "response not read" in message
                    and "stream" in message
                )
                if overloaded and attempt < max_retries:
                    delay = base_delay_s * (2**attempt) + random.uniform(0, 0.5)
                    console.print(
                        Panel(
                            f"Model overloaded. Retrying in {delay:.1f}s (attempt {attempt + 1} of {max_retries})",
                            title="⏳ Retry",
                            title_align="left",
                            border_style="yellow",
                            highlight=True,
                        )
                    )
                    await asyncio.sleep(delay)
                    continue
                raise
        return None

    @staticmethod
    def _process_message(message: BaseMessageChunk, max_lines: int | None = None) -> RenderableType | None:
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
                    elif text := item.get("text"):
                        content.append(text)
                    elif thinking := item.get("thinking"):
                        content.append(f'<span style="color: gray;">{thinking}</span>')
            content_text = "\n".join(content)

        # Apply line limiting if specified
        if max_lines is not None and max_lines > 0:
            content_text = _get_last_n_lines(content_text, max_lines)

        if not content_text:
            return None

        return Markdown(content_text)

    @staticmethod
    def _create_response_panel(
        result: BaseMessageChunk, panel_title: str, border_style: str, max_lines: int | None = None
    ) -> RenderableType:
        """Create a panel for displaying the streaming response."""
        markdown_content = Agent._process_message(result, max_lines)

        if markdown_content is None:
            return ""

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

    async def _run_tool(self, tool_call: dict) -> tuple[str, str]:
        """Run a tool call."""
        tool_name = tool_call.get("name", "")
        tool = self.tools.get(tool_name)

        if not tool:
            raise KeyError(f"Tool {tool_name} not found")

        tool_result = await tool.ainvoke(tool_call)
        tool_message = ToolMessage(content=tool_result.content, tool_call_id=tool_call.get("id", ""))
        self.state.add_message(tool_message)
        return tool_name, tool_result.content

    async def _process_tool_calls(self, tool_calls: list[dict]) -> None:
        """Process and execute tool calls."""
        for tool_call in tool_calls:
            try:
                tool_name, tool_result = await self._run_tool(tool_call)
            except Exception as e:  # noqa: BLE001
                console.print(
                    Panel(
                        f"❌ Error running tool: {e}",
                        title=f"❌ Tool Error [dim]{tool_call['args']}[/dim]",
                        title_align="left",
                        border_style="red",
                        highlight=True,
                        expand=True,
                    )
                )
                self.state.add_message(
                    ToolMessage(content=f"Error running tool: {e}", tool_call_id=tool_call.get("id", ""))
                )
            else:
                console.print(
                    Panel(
                        tool_result,
                        title=f"🔧 Tool {tool_name} [dim]{tool_call['args']}[/dim]",
                        title_align="left",
                        border_style="green",
                        highlight=True,
                        expand=True,
                    )
                )
