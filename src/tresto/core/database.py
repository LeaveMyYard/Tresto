"""Database system for storing persistent test information."""

from __future__ import annotations

import hashlib
import textwrap
from pathlib import Path

from langchain_core.messages import HumanMessage
from pydantic import BaseModel


class TestDatabase(BaseModel):
    """Manages persistent storage for test-related information."""

    test_directory: Path
    test_name: str

    @property
    def database_dir(self) -> Path:
        """Get the database directory path."""
        return self.test_directory / ".database"

    @property
    def test_hash(self) -> str:
        """Generate a unique hash for this test."""
        # Use test name to create consistent hash
        return hashlib.md5(self.test_name.encode()).hexdigest()[:12]

    @property
    def test_data_dir(self) -> Path:
        """Get the directory for this specific test's data."""
        return self.database_dir / self.test_hash

    def ensure_database_exists(self) -> None:
        """Create database directory structure if it doesn't exist."""
        self.test_data_dir.mkdir(parents=True, exist_ok=True)

        # Create a metadata file for easy identification
        metadata_file = self.test_data_dir / "metadata.txt"
        if not metadata_file.exists():
            metadata_content = textwrap.dedent(
                f"""\
                Test Database Entry
                Test Name: {self.test_name}
                Test Hash: {self.test_hash}
                Created: Generated automatically by Tresto"""
            )
            metadata_file.write_text(metadata_content)

    def store_project_inspection_report(self, report: str) -> None:
        """Store project inspection report."""
        self.ensure_database_exists()
        report_file = self.test_data_dir / "project_inspection.txt"
        report_file.write_text(report)

    def get_project_inspection_report(self) -> str | None:
        """Retrieve project inspection report."""
        report_file = self.test_data_dir / "project_inspection.txt"
        if report_file.exists():
            return report_file.read_text()
        return None

    def store_playwright_investigation(self, investigation: str) -> None:
        """Store playwright investigation results."""
        self.ensure_database_exists()
        investigation_file = self.test_data_dir / "playwright_investigation.txt"
        investigation_file.write_text(investigation)

    def get_playwright_investigation(self) -> str | None:
        """Retrieve playwright investigation results."""
        investigation_file = self.test_data_dir / "playwright_investigation.txt"
        if investigation_file.exists():
            return investigation_file.read_text()
        return None

    def store_test_insights(self, insights: str) -> None:
        """Store general test insights and learnings."""
        self.ensure_database_exists()
        insights_file = self.test_data_dir / "test_insights.txt"
        insights_file.write_text(insights)

    def get_test_insights(self) -> str | None:
        """Retrieve test insights and learnings."""
        insights_file = self.test_data_dir / "test_insights.txt"
        if insights_file.exists():
            return insights_file.read_text()
        return None

    def list_stored_data(self) -> list[str]:
        """List all stored data files for this test."""
        if not self.test_data_dir.exists():
            return []

        data_files = [
            file.name for file in self.test_data_dir.iterdir() if file.is_file() and file.name != "metadata.txt"
        ]
        return sorted(data_files)

    def clear_test_data(self) -> None:
        """Clear all stored data for this test."""
        if self.test_data_dir.exists():
            import shutil

            shutil.rmtree(self.test_data_dir)

    @classmethod
    def list_all_tests(cls, test_directory: str) -> list[dict[str, str]]:
        """List all tests with stored data."""
        test_dir = Path(test_directory)
        database_dir = test_dir / ".database"

        if not database_dir.exists():
            return []

        tests = []
        for test_dir_path in database_dir.iterdir():
            if not test_dir_path.is_dir():
                continue

            metadata_file = test_dir_path / "metadata.txt"
            if not metadata_file.exists():
                continue

            try:
                content = metadata_file.read_text()
                # Parse test name from metadata
                for line in content.split("\n"):
                    if not line.startswith("Test Name:"):
                        continue

                    test_name = line.split(":", 1)[1].strip()
                    tests.append(
                        {
                            "test_name": test_name,
                            "test_hash": test_dir_path.name,
                            "data_dir": str(test_dir_path),
                        }
                    )
                    break
            except Exception:  # noqa: BLE001
                continue

        return sorted(tests, key=lambda x: x["test_name"])

    def to_prompt(self) -> list[HumanMessage]:
        """Convert the database to a prompt."""

        playwright_investigation = self.get_playwright_investigation()
        project_inspection = self.get_project_inspection_report()
        test_insights = self.get_test_insights()

        messages = [
            (
                HumanMessage(
                    content="Playwright investigation from previous runs: \n" + (playwright_investigation or "")
                )
                if playwright_investigation
                else None
            ),
            (
                HumanMessage(content="Project inspection from previous runs: \n" + (project_inspection or ""))
                if project_inspection
                else None
            ),
            (
                HumanMessage(content="Test insights from previous runs: \n" + (test_insights or ""))
                if test_insights
                else None
            ),
        ]

        return [message for message in messages if message is not None]
