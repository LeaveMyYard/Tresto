"""Configuration management for Tresto."""

from __future__ import annotations

from pathlib import Path
from typing import Self

import typer
import yaml
from pydantic import BaseModel
from rich.console import Console

console = Console()


class ViewportConfig(BaseModel):
    """Viewport configuration settings."""

    width: int = 1280
    height: int = 720


class BrowserConfig(BaseModel):
    """Browser configuration settings."""

    headless: bool | None = None
    timeout: int | None = None
    viewport: ViewportConfig

    @classmethod
    def default(cls) -> Self:
        """Get default browser configuration."""
        return cls(
            headless=True,
            timeout=30000,  # Default timeout in milliseconds
            viewport=ViewportConfig(),
        )


class AIConfig(BaseModel):
    """AI configuration settings."""

    connector: str
    model: str
    max_iterations: int | None = None
    temperature: float | None = None


class RecordingConfig(BaseModel):
    """Recording configuration settings."""

    auto_wait: bool | None = None
    capture_screenshots: bool | None = None
    generate_selectors: str | None = None

    @classmethod
    def default(cls) -> Self:
        """Get default recording configuration."""
        return cls(
            auto_wait=True,
            capture_screenshots=True,
            generate_selectors="auto",
        )


class ProjectConfig(BaseModel):
    """Project configuration settings."""

    name: str
    base_url: str
    test_directory: str


class TrestoConfig(BaseModel):
    """Main Tresto configuration."""

    project: ProjectConfig
    ai: AIConfig
    browser: BrowserConfig | None = None
    recording: RecordingConfig | None = None
    verbose: bool = True  # Show detailed code generation by default

    @classmethod
    def get_config_path(cls) -> Path:
        """Get the path to the configuration file."""
        return Path.cwd() / "tresto.yaml"

    @classmethod
    def load_config(cls) -> Self:
        """Load configuration from tresto.yaml file."""
        config_path = cls.get_config_path()

        if not config_path.exists():
            console.print("[red]Error:[/red] No tresto.yaml found.")
            console.print("Run [bold]tresto init[/bold] to create a configuration file.")
            raise typer.Exit(0)

        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            return cls(**config_data)
        except (OSError, ValueError, TypeError) as e:
            console.print(f"[red]{e.__class__.__name__} loading configuration:[/red] {e}")
            raise typer.Exit(-1) from e

    def save(self) -> Path:
        """Save configuration to tresto.yaml file."""
        config_path = self.get_config_path()

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.model_dump(), f, sort_keys=False)
        except (OSError, ValueError) as e:
            console.print(f"[red]Error saving configuration:[/red] {e}")
            raise typer.Exit(-1) from e
        else:
            console.print(f"[green]Configuration saved to {config_path}[/green]")

        return config_path
