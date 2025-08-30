from __future__ import annotations

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

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState

console = Console()


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
    ) -> str:
        """Invoke the AI agent with a message and handle the streaming response."""
        messages = self.total_messages + ([message] if message else [])
        result = await self._stream_response(messages, panel_title, border_style)
        
        if not result:
            return ""
        
        response = result.text()
        
        # Handle AI message and tool calls
        await self._handle_ai_response(result)
        
        return response
    
    async def _stream_response(
        self, 
        messages: list[BaseMessage], 
        panel_title: str, 
        border_style: str
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
                
                panel = self._create_response_panel(result, panel_title, border_style)
                live.update(panel)
        
        return result

    @staticmethod
    def _process_message(message: BaseMessageChunk) -> RenderableType:
        # Return markdown with the message content.
        # Parse each message. Text should be rendered as is. Tool calls should be a text with tool name and args.

        if isinstance(message.content, str):
            return Markdown(message.content)

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

        return Markdown("\n".join(content))
    
    @staticmethod
    def _create_response_panel(
        result: BaseMessageChunk, 
        panel_title: str, 
        border_style: str
    ) -> Panel:
        """Create a panel for displaying the streaming response."""
        markdown_content = Agent._process_message(result)
        char_count = len(result.text())
        
        return Panel(
            markdown_content,
            title=panel_title.format(char_count=char_count),
            title_align="left",
            border_style=border_style,
            highlight=True,
        )
    
    async def _handle_ai_response(self, result: BaseMessageChunk) -> None:
        """Handle the AI response by adding it to state and processing tool calls."""

        tool_calls: list[dict] | None = getattr(result, 'tool_calls', None)

        # Add the AI message to the conversation history
        ai_message = AIMessage(
            content=result.content,
            tool_calls=tool_calls
        )
        self.state.add_message(ai_message)
        
        # Process tool calls if any
        if tool_calls:
            await self._process_tool_calls(tool_calls)
    
    async def _process_tool_calls(self, tool_calls: list[dict]) -> None:
        """Process and execute tool calls."""
        for tool_call in tool_calls:
            console.print(f"Tool call: {tool_call}")
            tool_name = tool_call.get("name", "")
            tool = self.tools.get(tool_name)
            
            if tool:
                tool_result = tool.invoke(tool_call)
                console.print(Panel(tool_result.content))
                
                tool_message = ToolMessage(
                    content=tool_result.content,
                    tool_call_id=tool_call.get("id", "")
                )
                self.state.add_message(tool_message)
            else:
                error_msg = f"Tool call: {tool_name} not found"
                console.print(error_msg)
                self.state.add_message(AIMessage(content=error_msg))
