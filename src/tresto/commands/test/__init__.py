"""Test-related CLI commands for Tresto."""

import typer

from . import create as create_module

app = typer.Typer(help="Work with tests")

app.command("create", help="Create a new test scaffold")(create_module.create_test_command)
