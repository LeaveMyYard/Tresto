"""Create test command implementation."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.live import Live
from rich.syntax import Syntax

from tresto.core.config.main import TrestoConfig
from tresto.core.recorder import BrowserRecorder
from tresto.ai.agent import LangGraphTestAgent

console = Console()


def _normalize_test_path(raw: str) -> Path:
    # allow dots or slashes as separators; collapse repeated separators
    parts = [p for chunk in raw.split("/") for p in chunk.split(".") if p]
    return Path(*parts)


def iterate_test_command(path: str) -> None:
    asyncio.run(_iterate_test_command(path))


async def _iterate_test_command(path: str) -> None:
    """Interactively create a new test skeleton with metadata files."""

    console.print("\n[bold blue]🧪 Create a new Tresto test[/bold blue]")

    # Ensure project config exists
    cfg = TrestoConfig.load_config()
    base_dir = Path(cfg.project.test_directory)

    rel_test_path = _normalize_test_path(path)
    abs_test_path = base_dir / rel_test_path

    test_name = abs_test_path.stem
    test_module_path = (abs_test_path / "..").resolve()
    target_file_path = (test_module_path / f"test_{test_name}.py").resolve()

    if not target_file_path.exists():
        console.print(f"\n[red]❌ Test does not exist[/red] at [bold]{target_file_path}[/bold]")
        return

    # 3. Ask for high-level instructions
    instructions = "Go to the main page of the app, go to the top panel navigation and to the current auction list. Open one current auction and check that the page contains dropdowns with it's groups and subgroups. Clicking one should open lot list."
    recording_path = test_module_path / "playwright_codegen.py"

    console.print(Panel.fit("🤖 Launching AI Agent to generate and run your test", title="Tresto AI"))

    agent = LangGraphTestAgent(cfg)
    state = await agent.run(
        test_name=test_name,
        test_instructions=instructions,
        test_file_path=target_file_path.as_posix(),
        recording_path=str(recording_path),
        max_iterations=cfg.ai.max_iterations or 5,
    )

    # Summarize results
    result = state.get("run_result")
    if result and getattr(result, "success", False):
        console.print(Panel.fit(
            f"✅ Test passed in {getattr(result, 'duration_s', 0.0):.2f}s\nSaved to: [bold]{target_file_path}[/bold]",
            title="AI Result",
            border_style="green",
        ))
    else:
        tb = getattr(result, "traceback", "") if result else "No result"
        console.print(Panel(
            f"❌ Test failed. See traceback below:\n\n{tb}\n\nSaved to: [bold]{target_file_path}[/bold]",
            title="AI Result",
            border_style="red",
        ))
