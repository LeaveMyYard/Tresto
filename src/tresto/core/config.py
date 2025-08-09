"""Configuration management for Tresto."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Self

import toml
import typer
from pydantic import BaseModel, Field
from rich.console import Console

console = Console()


class BrowserConfig(BaseModel):
    """Browser configuration settings."""

    headless: bool = False
    timeout: int = 30000
    viewport: dict[str, int] = Field(default_factory=lambda: {"width": 1280, "height": 720})


class AIConfig(BaseModel):
    """AI configuration settings."""

    provider: str = "anthropic"  # anthropic, openai, etc.
    model: str = "claude-3-5-sonnet-20241022"
    max_iterations: int = 5
    temperature: float = 0.1


class RecordingConfig(BaseModel):
    """Recording configuration settings."""

    auto_wait: bool = True
    capture_screenshots: bool = True
    generate_selectors: str = "smart"


class ProjectConfig(BaseModel):
    """Project configuration settings."""

    name: str = "my-project"
    base_url: str = "http://localhost:3000"
    test_directory: str = "./tests"


class TrestoConfig(BaseModel):
    """Main Tresto configuration."""

    project: ProjectConfig
    browser: BrowserConfig
    ai: AIConfig
    recording: RecordingConfig

    @classmethod
    def get_config_path(cls) -> Path:
        """Get the path to the configuration file."""
        return Path.cwd() / ".trestorc"

    @classmethod
    def load_config(cls) -> Self:
        """Load configuration from .trestorc file."""
        config_path = cls.get_config_path()

        if not config_path.exists():
            console.print("[yellow]Warning:[/yellow] No .trestorc found. Using default configuration.")
            console.print("Run [bold]tresto init[/bold] to create a configuration file.")
            raise typer.Exit(0)

        try:
            with open(config_path) as f:
                config_data = toml.load(f)
            return cls(**config_data)
        except (OSError, ValueError, TypeError) as e:
            console.print(f"[red]{e.__class__.__name__} loading configuration:[/red] {e}")
            raise typer.Exit(-1) from e

    def save(self) -> None:
        """Save configuration to .trestorc file."""
        config_path = self.get_config_path()

        try:
            with open(config_path, "w") as f:
                toml.dump(self.model_dump(), f)
        except (OSError, ValueError) as e:
            console.print(f"[red]Error saving configuration:[/red] {e}")
            raise typer.Exit(-1) from e
        else:
            console.print(f"[green]Configuration saved to {config_path}[/green]")
