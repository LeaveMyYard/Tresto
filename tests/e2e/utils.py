"""Utilities for E2E tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_tresto_command(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Run a tresto CLI command in a subprocess.

    Args:
        cmd: Command and arguments to run (e.g., ["tresto", "init"])
        cwd: Working directory to run the command in
        env: Optional environment variables
        input_text: Optional text to provide as stdin input

    Returns:
        CompletedProcess with stdout, stderr, and returncode
    """
    project_root = Path(__file__).resolve().parents[2]

    full_env = {
        "PYTHONPATH": str(project_root / "src"),
        "PATH": str(project_root / "src") + ":" + (env or {}).get("PATH", ""),
        **(env or {}),
    }

    python_exe = sys.executable

    if cmd[0] == "tresto":
        cmd = [python_exe, "-m", "tresto"] + cmd[1:]

    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        input=input_text,
        env=full_env,
        timeout=30,
    )

