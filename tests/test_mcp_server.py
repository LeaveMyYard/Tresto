from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

from tresto.core.config.main import AIConfig, BrowserConfig, ProjectConfig, RecordingConfig, TrestoConfig
from tresto.core.file_header import FileHeader
from tresto.core.scaffold import ScaffoldWriter
from tresto.mcp_server import (
    tresto_list_tests,
    tresto_read_test_context,
    tresto_run_tests,
    tresto_status,
    tresto_write_test_code,
)


def _write_config(tmp_path: Path) -> None:
    config = TrestoConfig(
        project=ProjectConfig(name="demo", url="http://localhost:3000", test_directory=Path("./tresto/tests")),
        ai=AIConfig(connector="test", model="test-model"),
        browser=BrowserConfig.default(),
        recording=RecordingConfig.default(),
    )
    config.save()


def _write_scaffold_test(tmp_path: Path) -> None:
    test_file = tmp_path / "tresto" / "tests" / "auth" / "test_login.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    FileHeader(
        test_name="auth.login",
        test_description="Login succeeds.",
        content=(
            f"# {ScaffoldWriter.SCAFFOLD_MARKER}\n\n"
            "import pytest\n\n"
            "@pytest.mark.skip(reason='planned')\n"
            "def test_login():\n"
            "    pass\n"
        ),
    ).write_to_file(test_file)


def test_mcp_status_and_list_tests(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    _write_scaffold_test(tmp_path)

    status = tresto_status(str(tmp_path))
    tests = tresto_list_tests(str(tmp_path), scaffold_only=True)

    assert status["project"]["name"] == "demo"
    assert status["test_count"] == 1
    assert tests["count"] == 1
    assert tests["tests"][0]["test_name"] == "auth.login"
    assert tests["tests"][0]["is_scaffold_placeholder"] is True


def test_mcp_read_and_write_test_code(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    _write_scaffold_test(tmp_path)

    before = tresto_read_test_context(str(tmp_path), "auth.login")
    result = tresto_write_test_code(
        str(tmp_path),
        "auth.login",
        "from playwright.async_api import Page\n\nasync def test_login(page: Page) -> None:\n    assert True\n",
    )
    after = tresto_read_test_context(str(tmp_path), "auth.login")

    assert before["is_scaffold_placeholder"] is True
    assert result["written"] is True
    assert "async def test_login" in after["test_code"]
    assert after["is_scaffold_placeholder"] is False


def test_mcp_run_selected_test(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    tresto_write_test_code(
        str(tmp_path),
        "auth.login",
        "def test_login() -> None:\n    assert True\n",
        description="Login succeeds.",
    )

    result = tresto_run_tests(str(tmp_path), test_name="auth.login", timeout_seconds=30)

    assert result["success"] is True
    assert result["returncode"] == 0


@pytest.mark.asyncio
async def test_mcp_stdio_survives_missing_config(tmp_path: Path) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "tresto.mcp_server"],
        cwd=tmp_path,
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            status = await session.call_tool("tresto_status", {"project_dir": str(tmp_path)})
            tests = await session.call_tool("tresto_list_tests", {"project_dir": str(tmp_path)})

    assert status.isError is False
    assert isinstance(status.content[0], TextContent)
    assert isinstance(tests.content[0], TextContent)
    status_text = status.content[0].text
    tests_text = tests.content[0].text

    assert '"initialized": false' in status_text
    assert tests.isError is True
    assert "No tresto.yaml found" in tests_text
