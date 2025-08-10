from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from tresto.ai.agent.state import TestAgentState


def _create_llm(state: TestAgentState):
    cfg = state["config"]
    provider = getattr(cfg.ai, "connector", None) or "anthropic"
    model = getattr(cfg.ai, "model", None) or "claude-3-5-sonnet-20241022"
    temperature = getattr(cfg.ai, "temperature", None) or 0.2
    if provider.lower() in {"openai", "gpt"}:
        return ChatOpenAI(model=model, temperature=temperature)
    return ChatAnthropic(model_name=model, temperature=temperature)


async def generate_or_update_code(state: TestAgentState) -> dict[str, Any]:
    llm = _create_llm(state)

    instruction = (
        "Create a new pytest + Playwright (async) test based on the provided details."
        if "current_test_code" not in state
        else "Improve the given pytest + Playwright (async) test. Keep it runnable."
    )

    recording_text = ""
    recording_path = state.get("recording_path")
    if recording_path and Path(recording_path).exists():
        try:
            recording_text = Path(recording_path).read_text(encoding="utf-8")
        except OSError:
            recording_text = ""

    prior_code = state.get("current_test_code", "")
    run_info = state.get("run_result")
    run_feedback = (
        f"Last run: success={run_info.success}, duration={run_info.duration_s:.3f}s\nTraceback:\n{run_info.traceback or ''}"
        if run_info
        else ""
    )

    sys_prompt = (
        "You are a senior QA engineer. Produce complete, executable Python code for pytest using Playwright async API."
        " Use robust selectors and proper waits, and meaningful expect() assertions."
    )

    user_prompt = (
        f"Instruction: {instruction}\n\n"
        f"Test name: {state['test_name']}\n"
        f"Target file path: {state['test_file_path']}\n\n"
        "Recording (if any):\n" + (recording_text[:4000] if recording_text else "<none>") + "\n\n"
        "Current test code (if any):\n" + (prior_code[:6000] if prior_code else "<none>") + "\n\n"
        f"Execution feedback (if any):\n{run_feedback}\n\n"
        "Return ONLY Python code, no explanations."
    )

    messages: list[str] = state.get("messages", [])
    combined_prompt = f"{sys_prompt}\n\n{user_prompt}"
    messages.append(f"USER:\n{combined_prompt}")
    # Brief high-level plan (thinking) for visibility
    think_prompt = (
        "You are planning how to write or update a pytest Playwright test.\n"
        "Provide a concise, high-level plan (3-6 short bullets) describing what you'll change or verify next,\n"
        "based on the current state, recording, and any prior run feedback.\n"
        "Do NOT include any code."
    )
    think_context = (
        f"Test: {state['test_name']}\n"  # type: ignore[index]
        f"Has prior code: {bool(prior_code)}\n"
        f"Run feedback: {run_feedback or 'n/a'}\n"
    )
    think_msg = await llm.ainvoke(think_prompt + "\n\n" + think_context)
    think_text = getattr(think_msg, "content", str(think_msg))

    ai_msg = await llm.ainvoke(combined_prompt)
    ai_text = getattr(ai_msg, "content", str(ai_msg))

    def _strip_markdown_code_fences(text: str) -> str:
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

    sanitized_code = _strip_markdown_code_fences(ai_text)

    messages.append(f"AI:\n{ai_text}")
    return {
        "messages": messages,
        "current_test_code": sanitized_code,
        "debug_generate": {
            "prompt": combined_prompt,
            "response_preview": ai_text[:1200],
        },
        "debug_think": think_text[:1200],
    }
