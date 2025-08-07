"""Tests for CLI commands."""

from typer.testing import CliRunner

from tresto.cli import app

runner = CliRunner()


def test_version_command() -> None:
    """Test version command works."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Tresto v" in result.stdout


def test_help_command() -> None:
    """Test help command works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AI-powered E2E testing CLI" in result.stdout


def test_init_help() -> None:
    """Test init command help."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize Tresto in your project" in result.stdout


def test_record_help() -> None:
    """Test record command help."""
    result = runner.invoke(app, ["record", "--help"])
    assert result.exit_code == 0
    assert "Record and generate AI-powered tests" in result.stdout
