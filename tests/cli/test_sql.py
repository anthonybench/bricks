"""Tests for the ``sql`` command."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import typer
from typer.testing import CliRunner

from sleepybricks.cli.commands.sql import _resolveStatement
from sleepybricks.main import app
from tests.conftest import writeDatabricksConfig

runner = CliRunner()


def testResolveStatementReadsSqlFile(tmp_path: Path) -> None:
    """A ``.sql`` file is read and its contents returned."""

    sql_path = tmp_path / "query.sql"
    sql_path.write_text("select 1", encoding="utf-8")

    assert _resolveStatement(sql_path, None) == "select 1"


def testResolveStatementUsesLiteralString(tmp_path: Path) -> None:
    """A literal SQL string is returned unchanged."""

    assert _resolveStatement(None, "select 2") == "select 2"


def testResolveStatementRejectsBothOrNeither(tmp_path: Path) -> None:
    """Providing both or neither of -f/-s is an error."""

    with pytest.raises(typer.BadParameter):
        _resolveStatement(None, None)
    with pytest.raises(typer.BadParameter):
        _resolveStatement(tmp_path / "a.sql", "select 1")


def testResolveStatementRequiresSqlExtension(tmp_path: Path) -> None:
    """A non-.sql file path is rejected."""

    bad = tmp_path / "query.txt"
    bad.write_text("select 1", encoding="utf-8")

    with pytest.raises(typer.BadParameter):
        _resolveStatement(bad, None)


def testSqlGracefulWhenConfigMissing(env: SimpleNamespace) -> None:
    """With no databricks config, the command exits 1 with a clear message."""

    result = runner.invoke(app, ["sql", "-s", "select 1", "dev,stg"])

    assert result.exit_code == 1
    assert "Databricks config not found" in result.output


def testSqlGracefulWhenProfileUnknown(env: SimpleNamespace) -> None:
    """An unknown profile is reported with the available ones."""

    writeDatabricksConfig(env.cfg, ["dev"])

    result = runner.invoke(app, ["sql", "-s", "select 1", "dev,prod"])

    assert result.exit_code == 1
    assert "prod" in result.output
