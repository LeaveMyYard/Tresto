"""Anthropic Claude connector using langchain."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from rich.console import Console

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from langchain_anthropic import ChatAnthropic

from .base import AIConnector, ChatMessage, GenerationResult

console = Console()


class AnthropicConnector(AIConnector):
    """Connector for Anthropic Claude models via langchain."""

    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", **kwargs: Any) -> None:
        """Initialize the Anthropic connector."""
        super().__init__(model_name, **kwargs)
        self._client: ChatAnthropic | None = None

    @property
    def client(self) -> ChatAnthropic:
        """Get or create the langchain ChatAnthropic client."""
        if self._client is None:
            try:
                from langchain_anthropic import ChatAnthropic

                self._client = ChatAnthropic(
                    model=self.model_name,
                    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                    **self.config,
                )
            except ImportError:
                console.print("[red]Error: langchain-anthropic not installed[/red]")
                raise
        return self._client

    async def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate a response from Claude."""
        try:
            from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

            # Convert our messages to langchain format
            lc_messages = []
            for msg in messages:
                if msg.role == "user":
                    lc_messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    lc_messages.append(AIMessage(content=msg.content))
                elif msg.role == "system":
                    lc_messages.append(SystemMessage(content=msg.content))

            # Update client with generation parameters
            client = self.client
            client.temperature = temperature
            client.max_tokens = max_tokens

            # Generate response
            response = await client.ainvoke(lc_messages)

            return GenerationResult(
                content=response.content,
                model=self.model_name,
                tokens_used=response.usage_metadata.get("total_tokens")
                if hasattr(response, "usage_metadata")
                else None,
                finish_reason="completed",
            )

        except Exception as e:
            console.print(f"[red]Error generating with Claude: {e}[/red]")
            raise

    async def stream_generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream generate a response from Claude."""
        try:
            from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

            # Convert messages
            lc_messages = []
            for msg in messages:
                if msg.role == "user":
                    lc_messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    lc_messages.append(AIMessage(content=msg.content))
                elif msg.role == "system":
                    lc_messages.append(SystemMessage(content=msg.content))

            # Update client parameters
            client = self.client
            client.temperature = temperature
            client.max_tokens = max_tokens

            # Stream response
            async for chunk in client.astream(lc_messages):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content

        except Exception as e:
            console.print(f"[red]Error streaming with Claude: {e}[/red]")
            raise

    @property
    def is_available(self) -> bool:
        """Check if Anthropic API key is available."""
        return os.getenv("ANTHROPIC_API_KEY") is not None

    @property
    def max_tokens_limit(self) -> int:
        """Maximum tokens for Claude models."""
        if "claude-3-5" in self.model_name:
            return 200_000
        if "claude-3" in self.model_name:
            return 200_000
        return 100_000
