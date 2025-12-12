"""Fixtures for E2E tests."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pytest

__all__ = ["e2e_test_dir"]


def get_test_run_hash() -> str:
    """Generate a unique hash for this test run."""
    import time

    return hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]


@pytest.fixture
def e2e_test_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for E2E tests with the test_project copied."""
    project_root = Path(__file__).resolve().parents[2]
    test_project_src = project_root / "test_project"

    test_run_hash = get_test_run_hash()
    tmp_dir = project_root / "tmp" / test_run_hash
    tmp_dir.mkdir(parents=True, exist_ok=True)

    test_project_dest = tmp_dir / "test_project"

    shutil.copytree(
        test_project_src,
        test_project_dest,
        ignore=shutil.ignore_patterns("node_modules", "__pycache__", "*.pyc"),
        dirs_exist_ok=True,
    )

    node_modules_src = test_project_src / "node_modules"
    if node_modules_src.exists():
        node_modules_dest = test_project_dest / "node_modules"
        node_modules_dest.symlink_to(node_modules_src, target_is_directory=True)

    yield test_project_dest

    shutil.rmtree(tmp_dir, ignore_errors=True)
