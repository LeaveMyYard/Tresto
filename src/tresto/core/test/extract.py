from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, cast

from playwright.async_api import Page

from .errors import TestExtractionFormatError, TestExtractionNoTestFunctionsError, TestExtractionSignatureError

if TYPE_CHECKING:
    from pathlib import Path

type TestFunction = Callable[[Page], Awaitable[None]]


def extract_test_function(path: Path) -> TestFunction:
    if not path.exists() or not path.is_file():
        raise TestExtractionFormatError(f"Test file not found: {path}")
    if path.suffix != ".py":
        raise TestExtractionFormatError("Test file must be a Python file with .py extension")

    try:
        source = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        raise TestExtractionFormatError(f"Failed to read test file: {exc}") from exc

    namespace: dict[str, object] = {"__name": "__tresto_test__"}
    try:
        exec(compile(source, str(path), "exec"), namespace, namespace)  # noqa: S102
    except Exception as exc:  # noqa: BLE001
        raise TestExtractionFormatError(f"Failed to import/execute test module: {exc}") from exc

    candidates = [obj for name, obj in namespace.items() if name.startswith("test_") and callable(obj)]

    if not candidates:
        raise TestExtractionNoTestFunctionsError("No test functions found")
    if len(candidates) > 1:
        raise TestExtractionFormatError(f"Expected exactly one test function, found {len(candidates)}")

    test_func = candidates[0]
    if not inspect.iscoroutinefunction(test_func):
        raise TestExtractionSignatureError("Test function must be declared with 'async def'")

    sig = inspect.signature(test_func)
    params = list(sig.parameters.values())
    if len(params) != 1:
        raise TestExtractionSignatureError("Test function must accept exactly one parameter: 'page'")

    param = params[0]

    if param.kind not in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
        raise TestExtractionSignatureError("Test parameter must be positional: 'page'")

    if param.default is not inspect.Signature.empty:
        raise TestExtractionSignatureError("Test parameter must not have a default value")

    if param.name != "page":
        raise TestExtractionSignatureError("Test parameter must be named 'page'")

    return cast("TestFunction", test_func)
