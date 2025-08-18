"""Data models for playwright iteration functionality."""

from __future__ import annotations

from pydantic import BaseModel


class PlaywrightExecutionResult(BaseModel):
    """Result of executing playwright automation code."""
    success: bool
    error_message: str | None = None
    page_html: str | None = None


class InspectionResult(BaseModel):
    """Result of executing BeautifulSoup inspection code."""
    success: bool
    output: str
    error: str | None = None


class IterationData(BaseModel):
    """Data for a single iteration of the playwright cycle."""
    playwright_code: str
    playwright_success: bool
    playwright_error: str | None = None
    inspection_code: str
    inspection_success: bool
    inspection_output: str
    inspection_error: str | None = None 