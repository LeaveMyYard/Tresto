from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, BaseMessageChunk, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from rich.console import Console, RenderableType
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

if TYPE_CHECKING:
    from collections.abc import Callable

    from tresto.ai.agent.state import TestAgentState

console = Console()


def _strip_markdown_code_fences(text: str) -> str:
    """Extract code from markdown fenced code blocks."""
    # Try to extract the first fenced code block; prefer ```python
    pattern = re.compile(r"```\s*(?:python|py)?\s*\n([\s\S]*?)\n```", re.IGNORECASE)
    m = pattern.search(text)
    if m:
        return m.group(1).strip()
    # Fallback: remove any wrapping triple backticks without language
    pattern2 = re.compile(r"^```\s*\n?([\s\S]*?)\n?```\s*$", re.IGNORECASE)
    m2 = pattern2.match(text.strip())
    if m2:
        return m2.group(1).strip()
    return text.strip()


def _get_last_n_lines(text: str, n: int = 10) -> str:
    """Get the last n lines from text, handling both complete and partial lines."""
    if not text.strip():
        return ""

    lines = text.split("\n")
    # Take the last n lines, but ensure we don't start with empty lines
    last_lines = lines[-n:] if len(lines) >= n else lines

    # If the last line is empty and we have more than one line, remove it
    # This handles cases where the text ends with a newline
    if len(last_lines) > 1 and not last_lines[-1].strip():
        last_lines = last_lines[:-1]

    return "\n".join(last_lines)


def process_message(message: BaseMessageChunk) -> RenderableType:
    # Return markdown with the message content.
    # Parse each message. Text should be rendered as is. Tool calls should be a text with tool name and args.

    content = []
    for item in message.content:
        if isinstance(item, str):
            content.append(item)
        elif isinstance(item, dict):
            content.append(f"Tool call: {item.get('name', '')} with args: {item.get('args', '')}")
    return Markdown("\n".join(content))

@dataclass
class Agent:
    state: TestAgentState
    llm: BaseChatModel
    system_message: SystemMessage
    tools: dict[str, BaseTool]

    @property
    def total_messages(self) -> list[BaseMessage]:
        return [self.system_message] + self.state.messages

    async def structured_process[T: BaseModel](
        self,
        message: BaseMessage | None,
        response_format: type[T],
    ) -> T:
        llm = self.llm.with_structured_output(response_format)
        result = await llm.ainvoke(self.total_messages + ([message] if message else []))
        console.print(result.model_dump_json(indent=2))
        return result

    async def process(
        self,
        message: BaseMessage | None,
        panel_title: str = "🤖 AI processing... ({char_count} characters)",
        border_style: str = "yellow",
        code_generation_mode: bool = False,
        code_lines_to_show: int = 18,
        post_process_callback: Callable[[str], str] | None = None,
    ) -> str:
        result: BaseMessageChunk | None = None

        console.print()  # Add spacing before streaming

        with Live(console=console, refresh_per_second=10) as live:
            async for chunk in self.llm.astream(self.total_messages + ([message] if message else [])):
                if result is None:
                    result = chunk
                else:
                    result += chunk

                response = result.text()
                char_count = len(response)

                if code_generation_mode:
                    # Code generation mode with syntax highlighting
                    preview_code = _strip_markdown_code_fences(response)
                    last_lines = _get_last_n_lines(preview_code, code_lines_to_show)

                    # Create syntax highlighted code
                    if last_lines.strip():
                        syntax = Syntax(
                            last_lines,
                            "python",
                            theme="monokai",
                            line_numbers=False,
                            word_wrap=True,
                            background_color="default",
                        )
                    else:
                        syntax = Syntax("# Generating code...", "python", theme="monokai")

                    # Update the status with character count and code preview
                    total_lines = len(preview_code.split("\n")) if preview_code.strip() else 0

                    panel = Panel(
                        syntax,
                        title=panel_title.format(
                            char_count=char_count,
                            total_lines=total_lines,
                            code_lines_to_show=code_lines_to_show,
                        ),
                        title_align="left",
                        border_style=border_style,
                    )
                else:
                    # Standard markdown mode
                    markdown_content = process_message(result)

                    # Display in a panel with character count
                    panel = Panel(
                        markdown_content,
                        title=panel_title.format(char_count=char_count),
                        title_align="left",
                        border_style=border_style,
                        highlight=True,
                    )
                
                live.update(panel)

        # Apply post-processing if provided
        if post_process_callback:
            response = post_process_callback(response)

        # Print final status for code generation mode
        if code_generation_mode:
            final_char_count = len(response)
            final_code = _strip_markdown_code_fences(response)
            final_lines = len(final_code.split("\n")) if final_code.strip() else 0
            console.print(
                f"✅ Test code generation completed! ({final_char_count} characters, {final_lines} lines total)",
                style="bold green",
            )

        if result:
            # Add the AI message to the conversation history first
            ai_message = AIMessage(
                content=result.content,
                tool_calls=result.tool_calls if hasattr(result, 'tool_calls') else None
            )
            self.state.add_message(ai_message)

            # Call tools if needed
            if result.tool_calls:
                for tool_call in result.tool_calls:
                    console.print(f"Tool call: {tool_call}")
                    tool_name = tool_call.get("name", "")
                    tool = self.tools.get(tool_name)
                    if tool:
                        tool_result = tool.invoke(tool_call)
                        console.print(Panel(tool_result.content))
                        # Create proper ToolMessage with tool_call_id and result content
                        tool_message = ToolMessage(
                            content=tool_result.content,
                            tool_call_id=tool_call.get("id", "")
                        )
                        self.state.add_message(tool_message)
                    else:
                        console.print(f"Tool call: {tool_name} not found")
                        self.state.add_message(AIMessage(content=f"Tool call: {tool_name} not found"))

        return response
