"""Configuration management for Tresto."""

from __future__ import annotations

import os
import toml
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, Field
from rich.console import Console

console = Console()


class BrowserConfig(BaseModel):
    """Browser configuration settings."""
    headless: bool = False
    timeout: int = 30000
    viewport: Dict[str, int] = Field(default_factory=lambda: {"width": 1280, "height": 720})


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
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    recording: RecordingConfig = Field(default_factory=RecordingConfig)


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return Path.cwd() / ".trestorc"


def load_config() -> TrestoConfig:
    """Load configuration from .trestorc file."""
    config_path = get_config_path()
    
    if not config_path.exists():
        console.print(
            "[yellow]Warning:[/yellow] No .trestorc found. Using default configuration."
        )
        console.print("Run [bold]tresto init[/bold] to create a configuration file.")
        return TrestoConfig()
    
    try:
        with open(config_path, "r") as f:
            config_data = toml.load(f)
        return TrestoConfig(**config_data)
    except Exception as e:
        console.print(f"[red]Error loading configuration:[/red] {e}")
        console.print("Using default configuration.")
        return TrestoConfig()


def save_config(config: TrestoConfig) -> None:
    """Save configuration to .trestorc file."""
    config_path = get_config_path()
    
    try:
        with open(config_path, "w") as f:
            toml.dump(config.model_dump(), f)
        console.print(f"[green]Configuration saved to {config_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error saving configuration:[/red] {e}")


def get_anthropic_api_key() -> Optional[str]:
    """Get Anthropic API key from environment variables."""
    return os.getenv("ANTHROPIC_API_KEY")


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from environment variables."""
    return os.getenv("OPENAI_API_KEY")


def get_api_key_for_provider(provider: str) -> Optional[str]:
    """Get API key for the specified provider."""
    provider_lower = provider.lower()
    
    if provider_lower in ["anthropic", "claude"]:
        return get_anthropic_api_key()
    elif provider_lower in ["openai", "gpt"]:
        return get_openai_api_key()
    else:
        # For unknown providers, try a generic pattern
        env_var = f"{provider.upper()}_API_KEY"
        return os.getenv(env_var)


def get_required_env_var_name(provider: str) -> str:
    """Get the environment variable name required for the provider."""
    provider_lower = provider.lower()
    
    if provider_lower in ["anthropic", "claude"]:
        return "ANTHROPIC_API_KEY"
    elif provider_lower in ["openai", "gpt"]:
        return "OPENAI_API_KEY"
    else:
        return f"{provider.upper()}_API_KEY"
