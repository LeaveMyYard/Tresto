"""Data models for project inspection functionality."""

from __future__ import annotations

from pydantic import BaseModel


class FileExplorationResult(BaseModel):
    """Result of executing file exploration command."""

    success: bool
    output: str
    error: str | None = None


class FileExplorationData(BaseModel):
    """Data for file exploration cycle."""

    exploration_command: str
    exploration_success: bool
    exploration_output: str
    exploration_error: str | None = None
