from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import tresto.commands.test.implement as implement_mod
from tresto.core.config.main import AIConfig, BrowserConfig, ProjectConfig, RecordingConfig, TrestoConfig
from tresto.core.file_header import FileHeader
from tresto.core.scaffold import ScaffoldWriter


def _write_config(tmp_path: Path) -> TrestoConfig:
    config = TrestoConfig(
        project=ProjectConfig(name="demo", url="http://localhost:3000", test_directory=Path("./tresto/tests")),
        ai=AIConfig(connector="test", model="test-model"),
        browser=BrowserConfig.default(),
        recording=RecordingConfig.default(),
    )
    config.save()
    return config


def _write_test(path: Path, test_name: str, description: str, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    FileHeader(test_name=test_name, test_description=description, content=content).write_to_file(path)


def test_discover_scaffolded_tests_only_returns_placeholder_tests(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    config = _write_config(tmp_path)
    _write_test(
        tmp_path / "tresto" / "tests" / "auth" / "test_login.py",
        "auth.login",
        "Login succeeds.",
        f"# {ScaffoldWriter.SCAFFOLD_MARKER}\n\nimport pytest\n\n@pytest.mark.skip(reason='planned')\ndef test_login():\n    pass\n",
    )
    _write_test(
        tmp_path / "tresto" / "tests" / "auth" / "test_done.py",
        "auth.done",
        "Already implemented.",
        "def test_done():\n    pass\n",
    )

    tests = implement_mod.discover_scaffolded_tests(config)

    assert [test.test_name for test in tests] == ["auth.login"]


def test_implement_scaffold_command_prompts_and_runs_selected_tests(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)
    _write_test(
        tmp_path / "tresto" / "tests" / "auth" / "test_login.py",
        "auth.login",
        "Login succeeds.",
        f"# {ScaffoldWriter.SCAFFOLD_MARKER}\n\nimport pytest\n\n@pytest.mark.skip(reason='planned')\ndef test_login():\n    pass\n",
    )
    _write_test(
        tmp_path / "tresto" / "tests" / "checkout" / "test_pay.py",
        "checkout.pay",
        "Checkout succeeds.",
        f"# {ScaffoldWriter.SCAFFOLD_MARKER}\n\nimport pytest\n\n@pytest.mark.skip(reason='planned')\ndef test_pay():\n    pass\n",
    )

    run_calls: list[str] = []

    class DummyRunner:
        def __init__(self, *_args: Any, test_name: str, **_kwargs: Any) -> None:
            self.test_name = test_name

        async def run(self) -> None:
            run_calls.append(self.test_name)

    with (
        patch("rich.prompt.Prompt.ask", side_effect=["record", "skip"]),
        patch("tresto.commands.test.implement.TrestoRunner", DummyRunner),
    ):
        implement_mod.implement_scaffold_command()

    assert run_calls == ["auth.login"]
