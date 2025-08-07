"""OpenAI GPT connector using langchain."""

from __future__ import annotations

import os
from typing import List, Any, AsyncIterator, Optional, TYPE_CHECKING
from rich.console import Console

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI

from .base import AIConnector, ChatMessage, GenerationResult

console = Console()


class OpenAIConnector(AIConnector):
    """Connector for OpenAI GPT models via langchain."""

    def __init__(self, model_name: str = "gpt-4o", **kwargs: Any) -> None:
        """Initialize the OpenAI connector."""
        super().__init__(model_name, **kwargs)
        self._client: Optional[ChatOpenAI] = None

    @property
    def client(self) -> ChatOpenAI:
        """Get or create the langchain ChatOpenAI client."""
        if self._client is None:
            try:
                from langchain_openai import ChatOpenAI

                self._client = ChatOpenAI(
                    model=self.model_name,
                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                    **self.config,
                )
            except ImportError:
                console.print("[red]Error: langchain-openai not installed[/red]")
                raise
        return self._client

    async def generate(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate a response from GPT."""
        try:
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

            # Convert messages to langchain format
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

            # Generate response
            response = await client.ainvoke(lc_messages)

            return GenerationResult(
                content=response.content,
                model=self.model_name,
                tokens_used=response.usage_metadata.get("total_tokens") if hasattr(response, "usage_metadata") else None,
                finish_reason="completed",
            )

        except Exception as e:
            console.print(f"[red]Error generating with GPT: {e}[/red]")
            raise

    async def stream_generate(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream generate a response from GPT."""
        try:
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

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
            console.print(f"[red]Error streaming with GPT: {e}[/red]")
            raise

    @property
    def is_available(self) -> bool:
        """Check if OpenAI API key is available."""
        return os.getenv("OPENAI_API_KEY") is not None

    @property
    def max_tokens_limit(self) -> int:
        """Maximum tokens for GPT models."""
        if "gpt-4" in self.model_name:
            return 128_000
        elif "gpt-3.5" in self.model_name:
            return 16_385
        else:
            return 8_000
