"""Mock chat model for testing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

if TYPE_CHECKING:
    from collections.abc import Sequence

    from langchain_core.callbacks.manager import CallbackManagerForLLMRun


class TestChatModel(BaseChatModel):
    """A mock chat model that returns canned responses for testing."""

    model_name: str = "test-model"

    @property
    def _llm_type(self) -> str:
        return "test"

    def _generate(
        self,
        messages: Sequence[BaseMessage],
        stop: Sequence[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a mock response."""
        response_text = "I am in test mode, not a real agent. This is a mock response for testing purposes."

        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)

        return ChatResult(generations=[generation])
