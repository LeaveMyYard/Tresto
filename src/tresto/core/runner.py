from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, ValidationError
from rich.console import Console
from rich.prompt import Prompt
from typer import Exit

from tresto.ai.agent import LangGraphTestAgent
from tresto.core.config.main import TrestoConfig
from tresto.core.file_header import FileHeader, TrestoFileHeaderCorrupted
from tresto.core.pathfinder import TrestoPathFinder


class TrestoRunner(BaseModel):
    console: Console = Field(default_factory=Console)
    config: TrestoConfig = Field(default_factory=TrestoConfig.load_config)
    mode: Literal["create", "iterate"]
    test_name: str | None = Field(default=None)

    _pathfinder: TrestoPathFinder | None = PrivateAttr(default=None)
    _test_description: str | None = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def run(self) -> None:
        self._hello()
        self.test_name = self._get_test_name()

        try:
            self._pathfinder = TrestoPathFinder(config=self.config, test_name=self.test_name)
        except ValidationError as e:
            self.console.print(f"\n[red]❌ {e}[/red]")
            raise Exit(1) from e

        if self.mode == "iterate" and not self._pathfinder.test_file_path.exists():
            self.console.print(f"\n[red]❌ Test file does not exist: {self._pathfinder.test_file_path}[/red]")
            raise Exit(1)

        if self.mode == "create" and self._pathfinder.test_file_path.exists():
            self.console.print(f"[red]❌ Test file already exists: {self._pathfinder.test_file_path}[/red]")
            self.console.print(
                "[red]Please use [bold]'tresto test iterate'[/bold] to iterate on "
                "existing test or delete the file and try again.[/red]"
            )
            raise Exit(1)

        self._test_description = self._get_test_description()
        if not self._test_description:
            self.console.print("\n[red]❌ Test description is required[/red]")
            raise Exit(1)

        self._ensure_file_exists()

        await self._run_agent()

    def _hello(self) -> None:
        if self.mode == "create":
            self.console.print("\n[bold blue]🧪 Create a new Tresto test[/bold blue]")
        elif self.mode == "iterate":
            self.console.print("\n[bold blue]🔍 Iterate on existing Tresto test[/bold blue]")

    def _get_test_name(self) -> str:
        if self.test_name is not None:
            # We already have a test name, skip the input
            return self.test_name

        return Prompt.ask("Enter the test name (use dots or slashes for subfolders)")

    def _get_test_description(self) -> str:
        description = self._try_load_test_description_from_file_header()
        if description is not None:
            return description

        return Prompt.ask("Describe what this test should do")

    def _try_load_test_description_from_file_header(self) -> str | None:
        assert self._pathfinder is not None

        if not self._pathfinder.test_file_path.exists():
            return None

        try:
            file_header = FileHeader.read_from_file(self._pathfinder.test_file_path)
        except TrestoFileHeaderCorrupted as e:
            self.console.print(f"\n[yellow]Warning: Test file was found but header is corrupted: {e}[/yellow]")
            return None

        return file_header.test_description

    def _ensure_file_exists(self) -> None:
        assert self._pathfinder is not None

        previous_content = ""

        if self._pathfinder.test_file_path.exists():
            with open(self._pathfinder.test_file_path) as f:
                previous_content = f.read()
        else:
            self._pathfinder.test_file_path.parent.mkdir(parents=True, exist_ok=True)

            # To make the new structure correct for pytest, we need to add __init__.py to all subfolders
            for path in self._pathfinder.test_module_relative_path.parent.rglob("__init__.py"):
                (self._pathfinder.tresto_root / path).touch()

            self._pathfinder.test_file_path.touch()

        header = FileHeader(test_name=self.test_name, test_description=self._test_description, content=previous_content)
        header.write_to_file(self._pathfinder.test_file_path)

    async def _run_agent(self) -> None:
        self.console.print("🤖 Launching AI Agent to generate and run your test")

        agent = LangGraphTestAgent(
            self.config,
            test_name=self.test_name,
            test_file_path=self._pathfinder.test_file_path,
            test_instructions=self._test_description,
            recording_file_path=self._pathfinder.recording_file_path,
        )
        await agent.init()
        await agent.run()
