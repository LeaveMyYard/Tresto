"""Test-related CLI commands for Tresto."""

import typer

from . import create as create_module
from .iterate import iterate_test_command
from .run import run_tests_command

app = typer.Typer(
    help="Work with tests",
    invoke_without_command=True,
    no_args_is_help=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)


@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context) -> None:
    # If invoked as `tresto test` with no subcommand, run tests
    if ctx.invoked_subcommand is None:
        run_tests_command(ctx)


app.command("create", help="Create a new test scaffold")(create_module.create_test_command)

def _run_entry(ctx: typer.Context) -> None:
    run_tests_command(ctx)

app.command(
    "run",
    help="Run all tests with pytest",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)(_run_entry)

app.command("iterate", help="Iterate on a test")(iterate_test_command)
