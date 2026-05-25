from __future__ import annotations

import json
from typing import Any

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from tresto.ai.connectors.codex.chat_model import (
    CodexChatModel,
    _instructions_from_messages,
    _message_to_response_input,
    _normalize_model,
    _parse_sse_response,
)
from tresto.ai.connectors.factory import connect, init_tresto_chat_model


class StructuredAnswer(BaseModel):
    title: str
    count: int


def test_codex_connector_is_available() -> None:
    connector = connect("codex")

    assert connector.model_name == "gpt-5.2-codex"
    assert init_tresto_chat_model("chatgpt", "gpt-5.1-codex")._llm_type == "codex-chatgpt"


@pytest.mark.asyncio
async def test_codex_connector_lists_newer_models() -> None:
    models = await connect("codex").get_available_models()

    assert "gpt-5.5" in models
    assert "gpt-5.3-codex" in models
    assert "codex-5.3" in models


def test_codex_model_normalization_accepts_shorthand() -> None:
    assert _normalize_model("codex-5.3") == "gpt-5.3-codex"
    assert _normalize_model("gpt-5.5") == "gpt-5.5"
    assert _normalize_model("gpt-5.3-codex") == "gpt-5.3-codex"


def test_codex_instructions_are_required_by_backend() -> None:
    assert _instructions_from_messages([SystemMessage("Plan tests"), HumanMessage("Snapshot")]) == "Plan tests"
    assert _instructions_from_messages([HumanMessage("Snapshot")])


def test_codex_message_input_uses_response_message_type() -> None:
    item = _message_to_response_input(HumanMessage("Snapshot"))

    assert item["type"] == "message"
    assert item["role"] == "user"


def test_parse_codex_sse_final_response() -> None:
    raw = "\n".join(
        [
            'data: {"type":"response.output_text.delta","delta":"ignored"}',
            'data: {"type":"response.done","response":{"output_text":"done"}}',
            "data: [DONE]",
        ]
    )

    assert _parse_sse_response(raw) == {"output_text": "done"}


def test_parse_codex_sse_preserves_streamed_text_when_final_output_is_empty() -> None:
    raw = "\n".join(
        [
            'data: {"type":"response.output_text.delta","delta":"{\\"ok\\":"}',
            'data: {"type":"response.output_text.delta","delta":"true}"}',
            'data: {"type":"response.completed","response":{"output":[]}}',
        ]
    )

    assert _parse_sse_response(raw) == {"output": [], "output_text": '{"ok":true}'}


@pytest.mark.asyncio
async def test_codex_structured_output_parses_pydantic_model(monkeypatch: Any) -> None:
    model = CodexChatModel()

    def fake_request(messages: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
        assert any("Return only valid JSON" in message.content for message in messages)
        return {"output_text": json.dumps({"title": "Plan", "count": 2})}

    monkeypatch.setattr(model, "_request", fake_request)

    result = await model.with_structured_output(StructuredAnswer).ainvoke([HumanMessage("Plan tests")])

    assert result == StructuredAnswer(title="Plan", count=2)
