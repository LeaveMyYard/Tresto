"""Tresto: AI-powered E2E testing CLI."""

from rich.console import Console

from tresto.config import config, secrets

console = Console()


__version__ = "0.2.1"
__author__ = "LeaveMyYard"
__email__ = "zhukovpavel2001@gmail.com"


__all__ = ["config", "secrets", "__version__", "__author__", "__email__"]
