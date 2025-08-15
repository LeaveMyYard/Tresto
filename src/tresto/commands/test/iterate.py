"""Create test command implementation."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rich.console import Console
from rich.status import Status
from rich.prompt import Prompt
from rich.panel import Panel
from rich.live import Live
from rich.syntax import Syntax

from tresto.ai.agent.state import TestAgentState, ThinkingStep, WaitingStep, WritingCodeStep
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
    console.print(f"Using {cfg.ai.model} from {cfg.ai.connector}")

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
    instructions = "I want to write a test that logins and goes to the dashboard page. I want to check that the dashboard page is loaded and contains the correct elements. For example I want to click the top tabs and see all pages loaded successfully."

    console.print("🤖 Launching AI Agent to generate and run your test")

    agent = LangGraphTestAgent(
        cfg,
        test_name=test_name,
        test_file_path=target_file_path,
        test_instructions=instructions,
    )

    agent_run_task = asyncio.create_task(agent.run())

    while not agent_run_task.done():
        output = await agent.state.consume_output()
        async for update in output.consume():
            console.print(f"[{output.__class__.__name__}] {update}")

    await agent_run_task

    console.print("Finished")