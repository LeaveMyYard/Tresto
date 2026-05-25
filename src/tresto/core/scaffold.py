from __future__ import annotations

import textwrap
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field, field_validator

from tresto import __version__
from tresto.core.file_header import FileHeader
from tresto.core.pathfinder import TrestoPathFinder

if TYPE_CHECKING:
    from tresto.core.config.main import TrestoConfig


class PlannedTest(BaseModel):
    test_name: str = Field(description="Tresto test name using dots or slashes, for example auth.login.success")
    file_path: str | None = Field(default=None, description="Optional relative test file path")
    title: str
    description: str
    priority: str = "medium"
    todo_steps: list[str] = Field(default_factory=list)

    @field_validator("test_name")
    def validate_test_name(cls, value: str) -> str:
        parts = TrestoPathFinder.split_test_path(value)
        if len(parts) == 0 or any(not part.isidentifier() for part in parts):
            raise ValueError("Test name should contain only valid Python identifiers")
        return value


class DatabaseCleanupRecommendation(BaseModel):
    beneficial: bool
    rationale: str
    detected_technology: str | None = None
    proposed_approach: str | None = None
    hook_code: str | None = Field(
        default=None,
        description="Optional pytest fixture/hook code that resets the test database safely.",
    )


class ScaffoldPlan(BaseModel):
    project_overview: str
    detected_stack: list[str] = Field(default_factory=list)
    conventions: list[str] = Field(default_factory=list)
    planned_tests: list[PlannedTest]
    database_cleanup: DatabaseCleanupRecommendation
    open_questions: list[str] = Field(default_factory=list)


class ScaffoldResult(BaseModel):
    readme_path: Path
    test_files: list[Path]
    db_cleanup_enabled: bool


class ExistingScaffoldError(RuntimeError):
    pass


class CodebaseSnapshot(BaseModel):
    project_root: Path
    tree: str
    files: list[tuple[str, str]]

    def to_prompt(self) -> str:
        file_sections = "\n\n".join(
            f"## {path}\n```text\n{content}\n```" for path, content in self.files
        )
        return f"# Project tree\n{self.tree}\n\n# Selected files\n{file_sections}"


class CodebaseSnapshotBuilder:
    EXCLUDED_DIRS: ClassVar[set[str]] = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "tmp",
        ".database",
        ".recordings",
    }
    EXCLUDED_FILES: ClassVar[set[str]] = {"uv.lock", "package-lock.json"}
    IMPORTANT_NAMES: ClassVar[set[str]] = {
        "pyproject.toml",
        "package.json",
        "vite.config.js",
        "next.config.js",
        "README.md",
        "tresto.yaml",
        "docker-compose.yml",
        "docker-compose.yaml",
    }
    IMPORTANT_SUFFIXES: ClassVar[tuple[str, ...]] = (
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".vue",
        ".svelte",
        ".html",
        ".css",
        ".toml",
        ".yaml",
        ".yml",
        ".json",
    )

    def __init__(self, project_root: Path, test_directory: Path) -> None:
        self.project_root = project_root.resolve()
        self.test_directory = (project_root / test_directory).resolve()

    def build(self, max_files: int = 35, max_file_chars: int = 6000, max_tree_entries: int = 250) -> CodebaseSnapshot:
        tree_entries: list[str] = []
        candidate_files: list[Path] = []

        for path in sorted(self.project_root.rglob("*")):
            if self._is_excluded(path):
                continue

            rel = path.relative_to(self.project_root)
            if len(tree_entries) < max_tree_entries:
                suffix = "/" if path.is_dir() else ""
                tree_entries.append(f"{rel}{suffix}")

            if path.is_file() and self._is_candidate_file(path):
                candidate_files.append(path)

        selected_files = self._prioritize_files(candidate_files)[:max_files]
        file_contents: list[tuple[str, str]] = []
        for path in selected_files:
            rel_path = path.relative_to(self.project_root).as_posix()
            content = self._read_text(path, max_file_chars)
            if content is not None:
                file_contents.append((rel_path, content))

        return CodebaseSnapshot(
            project_root=self.project_root,
            tree="\n".join(tree_entries),
            files=file_contents,
        )

    def _is_excluded(self, path: Path) -> bool:
        parts = set(path.relative_to(self.project_root).parts)
        if parts & self.EXCLUDED_DIRS:
            return True
        if path.name in self.EXCLUDED_FILES:
            return True
        try:
            path.relative_to(self.test_directory)
        except ValueError:
            return False
        return True

    def _is_candidate_file(self, path: Path) -> bool:
        if path.name in self.IMPORTANT_NAMES:
            return True
        if path.suffix.lower() not in self.IMPORTANT_SUFFIXES:
            return False
        return path.stat().st_size <= 200 * 1024

    def _prioritize_files(self, files: list[Path]) -> list[Path]:
        def score(path: Path) -> tuple[int, str]:
            rel = path.relative_to(self.project_root).as_posix().lower()
            value = 100
            if path.name in self.IMPORTANT_NAMES:
                value -= 40
            if any(token in rel for token in ["app", "page", "route", "component", "view", "screen"]):
                value -= 25
            if any(token in rel for token in ["auth", "login", "user", "checkout", "order", "admin"]):
                value -= 20
            if any(token in rel for token in ["test", "spec", "fixture"]):
                value -= 15
            if any(token in rel for token in ["db", "database", "prisma", "sqlalchemy", "migration"]):
                value -= 15
            return (value, rel)

        return sorted(files, key=score)

    @staticmethod
    def _read_text(path: Path, max_chars: int) -> str | None:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return None
        if len(content) > max_chars:
            return content[:max_chars] + f"\n\n... truncated at {max_chars} characters ..."
        return content


class ScaffoldWriter:
    SCAFFOLD_MARKER = "Generated by Tresto scaffold"
    DB_HOOK_START = "# BEGIN TRESTO SCAFFOLD DB CLEANUP"
    DB_HOOK_END = "# END TRESTO SCAFFOLD DB CLEANUP"

    def __init__(self, config: TrestoConfig, plan: ScaffoldPlan, force: bool = False) -> None:
        self.config = config
        self.plan = plan
        self.force = force
        self.test_root = config.project.test_directory
        self.workspace_root = self.test_root.parent

    def write(self, enable_db_cleanup: bool) -> ScaffoldResult:
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.test_root.mkdir(parents=True, exist_ok=True)
        self._check_existing(enable_db_cleanup)

        readme_path = self.workspace_root / "README.md"
        readme_path.write_text(self._render_readme(enable_db_cleanup), encoding="utf-8")

        written_tests = []
        for planned_test in self.plan.planned_tests:
            pathfinder = TrestoPathFinder(config=self.config, test_name=planned_test.test_name)
            path = pathfinder.test_file_path
            path.parent.mkdir(parents=True, exist_ok=True)
            self._ensure_init_files(pathfinder.test_module_relative_path.parent)
            header = FileHeader(
                test_name=planned_test.test_name,
                test_description=planned_test.description,
                content=self._render_placeholder_test(planned_test),
            )
            header.write_to_file(path)
            written_tests.append(path)

        if enable_db_cleanup:
            self._write_db_cleanup_hook()

        return ScaffoldResult(readme_path=readme_path, test_files=written_tests, db_cleanup_enabled=enable_db_cleanup)

    def _check_existing(self, enable_db_cleanup: bool) -> None:
        generated_conflicts: list[Path] = []
        user_conflicts: list[Path] = []
        readme_path = self.workspace_root / "README.md"
        if readme_path.exists():
            (generated_conflicts if self._is_scaffold_file(readme_path) else user_conflicts).append(readme_path)

        for planned_test in self.plan.planned_tests:
            path = TrestoPathFinder(config=self.config, test_name=planned_test.test_name).test_file_path
            if path.exists():
                (generated_conflicts if self._is_scaffold_file(path) else user_conflicts).append(path)

        conftest = self.test_root / "conftest.py"
        if enable_db_cleanup and conftest.exists():
            content = conftest.read_text(encoding="utf-8")
            if self.DB_HOOK_START in content and self.DB_HOOK_END in content:
                return

        if user_conflicts:
            conflict_list = "\n".join(f"- {path}" for path in user_conflicts)
            raise ExistingScaffoldError(
                "Scaffold output conflicts with hand-written files. Move them before running scaffold.\n"
                + conflict_list
            )

        if generated_conflicts and not self.force:
            conflict_list = "\n".join(f"- {path}" for path in generated_conflicts)
            raise ExistingScaffoldError(
                "Scaffold output already exists. Use --force to replace scaffold-generated files.\n" + conflict_list
            )

    def _is_scaffold_file(self, path: Path) -> bool:
        return path.exists() and self.SCAFFOLD_MARKER in path.read_text(encoding="utf-8", errors="ignore")

    def _render_readme(self, enable_db_cleanup: bool) -> str:
        planned_rows = "\n".join(
            f"| `{test.test_name}` | `{TrestoPathFinder(config=self.config, test_name=test.test_name).test_file_path}` "
            f"| {test.priority} | {test.title} |"
            for test in self.plan.planned_tests
        )
        sections = [
            f"# Tresto Test Scaffold\n\n<!-- {self.SCAFFOLD_MARKER} v{__version__} -->",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "## Project Overview\n" + self.plan.project_overview,
            "## Detected Stack\n" + self._render_list(self.plan.detected_stack),
            "## Conventions\n" + self._render_list(self.plan.conventions),
            "## Planned Test Files\n\n| Test | File | Priority | Purpose |\n| --- | --- | --- | --- |\n" + planned_rows,
            "## Test Details\n" + "\n\n".join(self._render_test_detail(test) for test in self.plan.planned_tests),
            "## Database Cleanup\n"
            + f"- Enabled: {'yes' if enable_db_cleanup else 'no'}\n"
            + f"- Beneficial: {'yes' if self.plan.database_cleanup.beneficial else 'no'}\n"
            + f"- Detected technology: {self.plan.database_cleanup.detected_technology or 'unknown'}\n"
            + f"- Rationale: {self.plan.database_cleanup.rationale}\n"
            + f"- Proposed approach: {self.plan.database_cleanup.proposed_approach or 'none'}",
            "## Open Questions\n" + self._render_list(self.plan.open_questions),
        ]
        return "\n\n".join(sections).strip() + "\n"

    @staticmethod
    def _render_list(items: list[str]) -> str:
        if not items:
            return "- None identified"
        return "\n".join(f"- {item}" for item in items)

    @staticmethod
    def _render_test_detail(test: PlannedTest) -> str:
        todos = "\n".join(f"- {step}" for step in test.todo_steps) or "- Define scenario steps"
        return f"### {test.test_name}\n\n{test.description}\n\nTODO:\n{todos}"

    def _render_placeholder_test(self, test: PlannedTest) -> str:
        steps = "\n".join(f"    # TODO: {step}" for step in test.todo_steps) or "    # TODO: Define scenario steps"
        function_name = "test_" + TrestoPathFinder.split_test_path(test.test_name)[-1]
        return textwrap.dedent(
            f'''\
            # {self.SCAFFOLD_MARKER} v{__version__}

            import pytest
            from playwright.async_api import Page


            @pytest.mark.skip(reason="Planned by tresto scaffold; implement with `tresto test iterate`.")
            async def {function_name}(page: Page) -> None:
                """{test.title}

                {test.description}
                """
            {steps}
            '''
        )

    def _ensure_init_files(self, relative_parent: Path) -> None:
        current_path = relative_parent
        while current_path != Path("."):
            init_file = self.test_root / current_path / "__init__.py"
            init_file.touch(exist_ok=True)
            current_path = current_path.parent

    def _write_db_cleanup_hook(self) -> None:
        conftest = self.test_root / "conftest.py"
        conftest.parent.mkdir(parents=True, exist_ok=True)
        existing = conftest.read_text(encoding="utf-8") if conftest.exists() else ""
        block = self._render_db_cleanup_block()

        if self.DB_HOOK_START in existing and self.DB_HOOK_END in existing:
            before, rest = existing.split(self.DB_HOOK_START, 1)
            _, after = rest.split(self.DB_HOOK_END, 1)
            conftest.write_text(before.rstrip() + "\n\n" + block + "\n" + after.lstrip(), encoding="utf-8")
            return

        conftest.write_text(existing.rstrip() + "\n\n" + block + "\n", encoding="utf-8")

    def _render_db_cleanup_block(self) -> str:
        hook_code = self.plan.database_cleanup.hook_code or self._default_db_cleanup_hook()
        hook_code = textwrap.indent(textwrap.dedent(hook_code).strip(), "")
        return f"{self.DB_HOOK_START}\n# {self.SCAFFOLD_MARKER}: app database cleanup\n{hook_code}\n{self.DB_HOOK_END}"

    def _default_db_cleanup_hook(self) -> str:
        return '''
        import os
        import pytest


        @pytest.fixture(autouse=True)
        async def tresto_scaffold_clean_database() -> None:
            """Reset application test data before each test.

            TODO: Implement the reset for this application's database.
            Tresto only enables this in explicit test environments.
            """
            if os.getenv("TRESTO_ENABLE_DB_CLEANUP") != "1":
                return
            raise NotImplementedError("Implement database cleanup for this project before enabling this fixture.")
        '''


async def generate_scaffold_plan(config: TrestoConfig, snapshot: CodebaseSnapshot) -> ScaffoldPlan:
    options = config.ai.options or {}
    llm = init_chat_model(
        f"{config.ai.connector}:{config.ai.model}",
        max_tokens=config.ai.max_tokens,
        temperature=config.ai.temperature,
        max_retries=3,
        **options,
    )
    structured_llm = llm.with_structured_output(ScaffoldPlan)
    result = await structured_llm.ainvoke(
        [
            SystemMessage(
                content=(
                    "You are Tresto scaffold. Plan a thorough pytest + Playwright E2E test suite. "
                    "Do not write executable test logic. Produce a structured plan and placeholder test inventory. "
                    "Recommend application database cleanup only if tests would benefit from isolated data."
                )
            ),
            HumanMessage(content=snapshot.to_prompt()),
        ]
    )
    if not isinstance(result, ScaffoldPlan):
        raise TypeError("Model did not return a ScaffoldPlan")
    return result
