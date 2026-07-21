from __future__ import annotations

import os
import subprocess
import sys
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP

from tresto import __version__
from tresto.core.config.main import ConfigLoadingError, TrestoConfig
from tresto.core.file_header import FileHeader, TrestoFileHeaderCorrupted
from tresto.core.pathfinder import TrestoPathFinder
from tresto.core.recorder import BrowserRecorder
from tresto.core.scaffold import ScaffoldWriter

if TYPE_CHECKING:
    from collections.abc import Iterator

mcp = FastMCP(
    "Tresto",
    instructions=(
        "Operate Tresto E2E tests for a local project. The usual workflow is: list scaffolded tests, "
        "record a manual browser flow with tresto_record_flow, read the resulting context, write the "
        "test implementation, and run the test."
    ),
)


@mcp.tool()
def tresto_status(project_dir: str = ".") -> dict[str, Any]:
    """Return Tresto configuration and basic project status."""

    with _project_cwd(project_dir) as root:
        config = _load_config()
        if config is None:
            return {
                "tresto_version": __version__,
                "project_dir": str(root),
                "initialized": False,
                "config_file": str(root / "tresto.yaml"),
                "config_exists": False,
                "message": "No tresto.yaml found. Run `tresto init` in this project first.",
                "test_directory_exists": False,
                "test_count": 0,
            }
        return {
            "tresto_version": __version__,
            "project_dir": str(root),
            "initialized": True,
            "config_file": str(root / "tresto.yaml"),
            "config_exists": True,
            "project": config.project.model_dump(mode="json"),
            "ai": config.ai.model_dump(mode="json"),
            "test_directory": str(config.project.test_directory),
            "test_directory_exists": config.project.test_directory.exists(),
            "test_count": len(list(config.project.test_directory.rglob("test_*.py")))
            if config.project.test_directory.exists()
            else 0,
        }


@mcp.tool()
def tresto_list_tests(project_dir: str = ".", scaffold_only: bool = False) -> dict[str, Any]:
    """List Tresto tests discovered from file headers."""

    with _project_cwd(project_dir):
        config = _require_config()
        tests = _discover_tests(config, scaffold_only=scaffold_only)
        return {"tests": tests, "count": len(tests)}


@mcp.tool()
async def tresto_record_flow(project_dir: str, test_name: str, url: str | None = None) -> dict[str, Any]:
    """Launch Playwright codegen so the user can manually record a browser flow for a test."""

    with _project_cwd(project_dir):
        config = _require_config()
        pathfinder = TrestoPathFinder(config=config, test_name=test_name)
        recorder = BrowserRecorder(config=config)
        with _suppress_stdout():
            code = await recorder.start_recording(
                url=url or config.project.url,
                output_file=pathfinder.recording_file_path,
            )
        return {
            "test_name": test_name,
            "recording_file": str(pathfinder.recording_file_path),
            "recording_code": code,
        }


@mcp.tool()
def tresto_read_test_context(project_dir: str, test_name: str) -> dict[str, Any]:
    """Read a Tresto test file, its header metadata, and any manual recording code."""

    with _project_cwd(project_dir):
        config = _require_config()
        pathfinder = TrestoPathFinder(config=config, test_name=test_name)
        header = _read_header(pathfinder.test_file_path)
        recording_code = (
            pathfinder.recording_file_path.read_text(encoding="utf-8")
            if pathfinder.recording_file_path.exists()
            else None
        )
        return {
            "test_name": test_name,
            "test_file": str(pathfinder.test_file_path),
            "recording_file": str(pathfinder.recording_file_path),
            "exists": pathfinder.test_file_path.exists(),
            "header": header.model_dump(mode="json") if header is not None else None,
            "test_code": header.content if header is not None else None,
            "recording_code": recording_code,
            "is_scaffold_placeholder": _is_scaffold_placeholder(pathfinder.test_file_path),
        }


@mcp.tool()
def tresto_write_test_code(
    project_dir: str,
    test_name: str,
    code: str,
    description: str | None = None,
) -> dict[str, Any]:
    """Write generated Playwright test code while preserving the Tresto file header."""

    with _project_cwd(project_dir):
        config = _require_config()
        pathfinder = TrestoPathFinder(config=config, test_name=test_name)
        pathfinder.test_file_path.parent.mkdir(parents=True, exist_ok=True)
        _ensure_init_files(pathfinder)

        existing_header = _read_header(pathfinder.test_file_path)
        if existing_header is None and not description:
            raise ValueError("description is required when creating a new Tresto test file")

        clean_code = _strip_markdown_code_fences(code)
        compile(clean_code, str(pathfinder.test_file_path), "exec")
        if existing_header is not None:
            test_description = description if description is not None else existing_header.test_description
            created_date = existing_header.created_date
        else:
            assert description is not None
            test_description = description
            created_date = FileHeader(
                content="",
                test_name=test_name,
                test_description=test_description,
            ).created_date

        header = FileHeader(
            test_name=test_name,
            test_description=test_description,
            created_date=created_date,
            content=clean_code,
        )
        header.write_to_file(pathfinder.test_file_path)
        return {"test_name": test_name, "test_file": str(pathfinder.test_file_path), "written": True}


@mcp.tool()
def tresto_run_tests(
    project_dir: str = ".",
    test_name: str | None = None,
    pytest_args: list[str] | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Run pytest for all Tresto tests or one named Tresto test."""

    with _project_cwd(project_dir):
        config = _require_config()
        target = config.project.test_directory
        if test_name:
            target = TrestoPathFinder(config=config, test_name=test_name).test_file_path
        args = [sys.executable, "-m", "pytest", str(target), *(pytest_args or [])]
        result = subprocess.run(
            args,
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return {
            "command": args,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }


@mcp.tool()
def tresto_run_cli(project_dir: str, args: list[str], timeout_seconds: int = 120) -> dict[str, Any]:
    """Run a Tresto CLI command for operations not covered by the typed tools."""

    if any(arg in {"mcp", "mcp-server"} for arg in args):
        raise ValueError("Refusing to recursively run the MCP server.")
    command = [sys.executable, "-m", "tresto", *args]
    result = subprocess.run(
        command,
        cwd=Path(project_dir).expanduser().resolve(),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0,
    }


def main() -> None:
    """Run the Tresto MCP server over stdio."""

    mcp.run()


@contextmanager
def _project_cwd(project_dir: str) -> Iterator[Path]:
    previous = Path.cwd()
    root = Path(project_dir).expanduser().resolve()
    os.chdir(root)
    try:
        yield root
    finally:
        os.chdir(previous)


@contextmanager
def _suppress_stdout() -> Iterator[None]:
    previous = sys.stdout
    sys.stdout = StringIO()
    try:
        yield
    finally:
        sys.stdout = previous


def _load_config() -> TrestoConfig | None:
    with _suppress_stdout():
        try:
            return TrestoConfig.load_config()
        except ConfigLoadingError:
            return None


def _require_config() -> TrestoConfig:
    config = _load_config()
    if config is None:
        raise ValueError("No tresto.yaml found. Run `tresto init` in this project first.")
    return config


def _discover_tests(config: TrestoConfig, scaffold_only: bool) -> list[dict[str, Any]]:
    test_root = config.project.test_directory
    if not test_root.exists():
        return []
    tests: list[dict[str, Any]] = []
    for path in sorted(test_root.rglob("test_*.py")):
        header = _read_header(path)
        if header is None:
            continue
        is_scaffold = _is_scaffold_placeholder(path)
        if scaffold_only and not is_scaffold:
            continue
        recording_file = TrestoPathFinder(config=config, test_name=header.test_name).recording_file_path
        tests.append(
            {
                "test_name": header.test_name,
                "description": header.test_description,
                "path": str(path),
                "recording_file": str(recording_file),
                "has_recording": recording_file.exists(),
                "is_scaffold_placeholder": is_scaffold,
            }
        )
    return tests


def _read_header(path: Path) -> FileHeader | None:
    if not path.exists():
        return None
    try:
        return FileHeader.read_from_file(path)
    except TrestoFileHeaderCorrupted:
        return None


def _is_scaffold_placeholder(path: Path) -> bool:
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8", errors="ignore")
    return ScaffoldWriter.SCAFFOLD_MARKER in content and "@pytest.mark.skip" in content


def _ensure_init_files(pathfinder: TrestoPathFinder) -> None:
    current_path = pathfinder.test_module_relative_path.parent
    while current_path != Path("."):
        init_file = pathfinder.tresto_root / current_path / "__init__.py"
        init_file.touch(exist_ok=True)
        current_path = current_path.parent


def _strip_markdown_code_fences(code: str) -> str:
    stripped = code.strip()
    if not stripped.startswith("```"):
        return code
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip() + "\n"


if __name__ == "__main__":
    main()
