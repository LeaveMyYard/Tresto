"""Models for HTML inspection tools."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InspectionResult:
    """Result of an HTML inspection command."""
    success: bool
    output: str
    error: str = ""
