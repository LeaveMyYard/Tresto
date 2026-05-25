from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

from click.exceptions import Exit

import tresto.commands.scaffold as scaffold_mod
from tresto.core.config.main import AIConfig, BrowserConfig, ProjectConfig, RecordingConfig, TrestoConfig
from tresto.core.scaffold import DatabaseCleanupRecommendation, PlannedTest, ScaffoldPlan


def _write_config(tmp_path: Path) -> None:
    config = TrestoConfig(
        project=ProjectConfig(name="demo", url="http://localhost:3000", test_directory=Path("./tresto/tests")),
        ai=AIConfig(connector="test", model="test-model"),
        browser=BrowserConfig.default(),
        recording=RecordingConfig.default(),
    )
    config.save()


def _plan(beneficial: bool = True) -> ScaffoldPlan:
    return ScaffoldPlan(
        project_overview="A checkout app.",
        detected_stack=["React"],
        conventions=["Feature folders under src"],
        planned_tests=[
            PlannedTest(
                test_name="checkout.complete",
                title="Checkout completes",
                description="Plan the happy-path checkout test.",
                priority="high",
                todo_steps=["Add item to cart", "Complete payment", "Assert confirmation"],
            )
        ],
        database_cleanup=DatabaseCleanupRecommendation(
            beneficial=beneficial,
            rationale="Checkout tests create orders.",
            detected_technology="SQLite",
            proposed_approach="Delete test orders before each test.",
        ),
        open_questions=[],
    )


def test_tresto_scaffold_writes_plan_files_and_respects_no_db_cleanup(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Checkout.jsx").write_text("export function Checkout() { return null }", encoding="utf-8")
    _write_config(tmp_path)

    async def _fake_plan(*_args: Any, **_kwargs: Any) -> ScaffoldPlan:
        return _plan(beneficial=True)

    with patch("tresto.commands.scaffold.generate_scaffold_plan", side_effect=_fake_plan):
        scaffold_mod.scaffold_command(no_db_cleanup=True)

    readme = tmp_path / "tresto" / "README.md"
    test_file = tmp_path / "tresto" / "tests" / "checkout" / "test_complete.py"
    conftest = tmp_path / "tresto" / "tests" / "conftest.py"

    assert readme.exists()
    assert "Checkout completes" in readme.read_text(encoding="utf-8")
    assert test_file.exists()
    assert "Plan the happy-path checkout test" in test_file.read_text(encoding="utf-8")
    assert not conftest.exists()


def test_tresto_scaffold_writes_db_cleanup_when_user_approves(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    _write_config(tmp_path)

    async def _fake_plan(*_args: Any, **_kwargs: Any) -> ScaffoldPlan:
        return _plan(beneficial=True)

    with patch("tresto.commands.scaffold.generate_scaffold_plan", side_effect=_fake_plan):
        scaffold_mod.scaffold_command(yes_db_cleanup=True)

    conftest = tmp_path / "tresto" / "tests" / "conftest.py"
    assert "tresto_scaffold_clean_database" in conftest.read_text(encoding="utf-8")


def test_tresto_scaffold_requires_config(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)

    try:
        scaffold_mod.scaffold_command(no_db_cleanup=True)
    except Exit as e:
        assert e.exit_code == 1
    else:
        raise AssertionError("Expected scaffold to fail without tresto.yaml")
