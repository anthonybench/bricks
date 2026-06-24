"""Tests for the ``write-secret`` and ``create-scope`` commands."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import typer
from typer.testing import CliRunner

import sleepybricks.cli.commands.secrets as secrets_cmd
from sleepybricks.cli.commands.secrets import _parseWriteSecretArgs
from sleepybricks.main import app
from tests.conftest import writeDatabricksConfig
from tests.fakes import FakeClient

runner = CliRunner()


def testParseWriteSecretFourArgForm() -> None:
    """The explicit four-argument form is parsed directly."""

    assert _parseWriteSecretArgs(["scope", "key", "value", "dev,stg"]) == (
        "scope",
        "key",
        "value",
        "dev,stg",
    )


def testParseWriteSecretDottedForm() -> None:
    """The dotted three-argument form splits scope and key."""

    assert _parseWriteSecretArgs(["scope.key", "value", "dev"]) == (
        "scope",
        "key",
        "value",
        "dev",
    )


def testParseWriteSecretRejectsBadArity() -> None:
    """An unsupported number of arguments is rejected."""

    with pytest.raises(typer.BadParameter):
        _parseWriteSecretArgs(["only", "two"])


def testParseWriteSecretDottedRequiresDot() -> None:
    """The three-arg form requires a dot in the first argument."""

    with pytest.raises(typer.BadParameter):
        _parseWriteSecretArgs(["nodot", "value", "dev"])


def testWriteSecretSucceedsWhenScopeExists(
    env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A secret is written when the scope already exists."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(scopes=["my_scope"])
    monkeypatch.setattr(secrets_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["write-secret", "my_scope.api_key", "s3cret", "dev"])

    assert result.exit_code == 0
    assert fake.secrets.put_calls == [("my_scope", "api_key", "s3cret")]
    assert "written" in result.output


def testWriteSecretSuggestsCreateScopeWhenMissing(
    env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the scope is missing, the create-scope command is suggested."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(scopes=[])
    monkeypatch.setattr(secrets_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["write-secret", "ghost", "key", "value", "dev"])

    assert result.exit_code == 0
    assert fake.secrets.put_calls == []
    assert "create-scope ghost dev" in result.output


def testCreateScopeSkipsExisting(env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    """An existing scope is skipped and reported as already present."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(scopes=["already"])
    monkeypatch.setattr(secrets_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["create-scope", "already", "dev"])

    assert result.exit_code == 0
    assert fake.secrets.created == []
    assert "already existed" in result.output


def testCreateScopeCreatesWhenMissing(
    env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing scope is created."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(scopes=[])
    monkeypatch.setattr(secrets_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["create-scope", "fresh", "dev"])

    assert result.exit_code == 0
    assert fake.secrets.created == ["fresh"]
    assert "created" in result.output
