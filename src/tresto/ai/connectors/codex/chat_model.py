from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, ConfigDict

from tresto.utils.credentials import CodexAuthProvider, CredentialError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from langchain_core.callbacks.manager import CallbackManagerForLLMRun
    from langchain_core.runnables import Runnable

CODEX_RESPONSES_URL = "https://chatgpt.com/backend-api/codex/responses"
OPENAI_BETA_HEADER = "responses=experimental"
ORIGINATOR = "codex_cli_rs"
DEFAULT_REASONING_EFFORT = "medium"


class CodexChatModel(BaseChatModel):
    """LangChain chat model backed by Codex browser auth and the ChatGPT Codex backend."""

    model_name: str = "gpt-5.2-codex"
    temperature: float | None = None
    max_tokens: int | None = None
    max_retries: int = 3
    request_timeout: float = 120.0
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] | None = None
    auth_file: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def _llm_type(self) -> str:
        return "codex-chatgpt"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model_name": self.model_name}

    def _generate(
        self,
        messages: Sequence[BaseMessage],
        stop: Sequence[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        del stop, run_manager
        response = self._request(messages, kwargs)
        content = _extract_response_text(response)
        message = AIMessage(content=content)
        generation = ChatGeneration(message=message, generation_info={"raw_response": response})
        return ChatResult(generations=[generation])

    def with_structured_output(
        self,
        schema: dict[str, Any] | type,
        *,
        include_raw: bool = False,
        **kwargs: Any,
    ) -> Runnable[Any, Any]:
        if include_raw:
            raise NotImplementedError("CodexChatModel does not support include_raw structured output yet.")

        async def parse_structured(input_value: Any) -> Any:
            messages = _coerce_messages(input_value)
            schema_instruction = _structured_output_instruction(schema)
            result = await self.ainvoke([*messages, schema_instruction], **kwargs)
            return _parse_structured_content(str(result.content), schema)

        return RunnableLambda(parse_structured)

    def bind_tools(
        self,
        tools: Sequence[Any],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> CodexChatModel:
        del tool_choice, kwargs
        if tools:
            raise NotImplementedError("The Codex browser-auth connector does not support LangChain tool calls yet.")
        return self

    def _request(self, messages: Sequence[BaseMessage], kwargs: dict[str, Any]) -> dict[str, Any]:
        auth = CodexAuthProvider(Path(self.auth_file) if self.auth_file else None)
        access_token = auth.get_access_token()
        if not access_token:
            raise CredentialError("Codex browser auth is missing or expired. Run `codex login`.")
        account_id = auth.get_account_id(access_token)
        if not account_id:
            raise CredentialError("Codex browser auth token does not include a ChatGPT account id.")

        body = {
            "model": _normalize_model(self.model_name),
            "stream": True,
            "store": False,
            "instructions": _instructions_from_messages(messages),
            "input": [_message_to_response_input(message) for message in messages],
            "reasoning": {"effort": kwargs.get("reasoning_effort") or self.reasoning_effort or DEFAULT_REASONING_EFFORT},
            "text": {"verbosity": kwargs.get("text_verbosity", "medium")},
            "include": ["reasoning.encrypted_content"],
        }
        if self.temperature is not None:
            body["temperature"] = self.temperature

        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            CODEX_RESPONSES_URL,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {access_token}",
                "chatgpt-account-id": account_id,
                "OpenAI-Beta": OPENAI_BETA_HEADER,
                "originator": ORIGINATOR,
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.request_timeout) as response:
                return _parse_sse_response(response.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            raise CredentialError(f"Codex backend rejected the request: {e.code} {body_text}") from e
        except OSError as e:
            raise CredentialError(f"Could not reach Codex backend: {e}") from e


def _normalize_model(model_name: str) -> str:
    if model_name == "codex-5.3":
        return "gpt-5.3-codex"
    if model_name == "gpt-5-codex":
        return "gpt-5.1-codex"
    return model_name


def _message_to_response_input(message: BaseMessage) -> dict[str, Any]:
    role = {
        "system": "developer",
        "human": "user",
        "ai": "assistant",
        "tool": "user",
    }.get(message.type, "user")
    return {
        "type": "message",
        "role": role,
        "content": [{"type": "input_text", "text": _message_content_to_text(message.content)}],
    }


def _instructions_from_messages(messages: Sequence[BaseMessage]) -> str:
    instructions = [
        _message_content_to_text(message.content)
        for message in messages
        if message.type in {"system", "developer"} and _message_content_to_text(message.content).strip()
    ]
    if instructions:
        return "\n\n".join(instructions)
    return "You are Tresto's coding and testing assistant. Follow the user's instructions precisely."


def _message_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                value = item.get("text") or item.get("content")
                if isinstance(value, str):
                    parts.append(value)
        return "\n".join(parts)
    return str(content)


def _parse_sse_response(raw: str) -> dict[str, Any]:
    final_response: dict[str, Any] | None = None
    output_text_parts: list[str] = []
    for line in raw.splitlines():
        if not line.startswith("data: "):
            continue
        data = line.removeprefix("data: ").strip()
        if not data or data == "[DONE]":
            continue
        event = json.loads(data)
        event_type = event.get("type")
        if event_type == "response.output_text.delta" and isinstance(event.get("delta"), str):
            output_text_parts.append(event["delta"])
        elif event_type == "response.output_text.done" and isinstance(event.get("text"), str):
            output_text_parts = [event["text"]]
        elif event_type == "response.output_item.done":
            item = event.get("item")
            if isinstance(item, dict):
                item_text = _extract_response_text({"output": [item]})
                if item_text:
                    output_text_parts = [item_text]
        if event_type in {"response.done", "response.completed"}:
            response = event.get("response")
            if isinstance(response, dict):
                final_response = response
    if final_response is None:
        raise CredentialError("Codex backend returned no final response event.")
    if output_text_parts and not _extract_response_text(final_response):
        final_response["output_text"] = "".join(output_text_parts)
    return final_response


def _extract_response_text(response: dict[str, Any]) -> str:
    output_text = response.get("output_text")
    if isinstance(output_text, str):
        return output_text

    text_parts: list[str] = []
    for output_item in response.get("output", []):
        if not isinstance(output_item, dict):
            continue
        for content_item in output_item.get("content", []):
            if not isinstance(content_item, dict):
                continue
            text = content_item.get("text")
            if isinstance(text, str):
                text_parts.append(text)
    return "\n".join(text_parts)


def _coerce_messages(input_value: Any) -> list[BaseMessage]:
    if isinstance(input_value, BaseMessage):
        return [input_value]
    if isinstance(input_value, list) and all(isinstance(item, BaseMessage) for item in input_value):
        return cast("list[BaseMessage]", input_value)
    raise TypeError("Codex structured output expects a LangChain message or a list of messages.")


def _structured_output_instruction(schema: dict[str, Any] | type) -> BaseMessage:
    from langchain_core.messages import HumanMessage

    schema_json = json.dumps(_schema_to_json_schema(schema), indent=2)
    return HumanMessage(
        content=(
            "Return only valid JSON. Do not wrap it in markdown. "
            "The JSON must match this schema:\n"
            f"{schema_json}"
        )
    )


def _schema_to_json_schema(schema: dict[str, Any] | type) -> dict[str, Any]:
    if isinstance(schema, dict):
        return schema
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        return schema.model_json_schema()
    raise TypeError("Structured output schema must be a dict or Pydantic model class.")


def _parse_structured_content(content: str, schema: dict[str, Any] | type) -> Any:
    data = json.loads(_strip_json_fences(content))
    if isinstance(schema, dict):
        return data
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        return schema.model_validate(data)
    raise TypeError("Structured output schema must be a dict or Pydantic model class.")


def _strip_json_fences(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped
