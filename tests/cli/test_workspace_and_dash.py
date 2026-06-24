"""Tests for the ``create-workspace-folder`` and ``dash-links`` commands."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

import sleepybricks.cli.commands.dash_links as dash_cmd
import sleepybricks.cli.commands.workspace_folder as folder_cmd
from sleepybricks.main import app
from tests.conftest import writeDatabricksConfig
from tests.fakes import FakeClient, dashboard

runner = CliRunner()


def testCreateWorkspaceFolderCreatesWhenMissing(
    env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing folder is created and the path is normalized with a leading slash."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(folders=[])
    monkeypatch.setattr(folder_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["create-workspace-folder", "my_folder", "dev"])

    assert result.exit_code == 0
    assert fake.workspace.made == ["/my_folder"]
    assert "created" in result.output


def testCreateWorkspaceFolderSkipsExisting(
    env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An existing folder is skipped and reported."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(folders=["/existing"])
    monkeypatch.setattr(folder_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["create-workspace-folder", "/existing", "dev"])

    assert result.exit_code == 0
    assert fake.workspace.made == []
    assert "already existed" in result.output


def testDashLinksBuildsPublishedLink(env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    """A matching dashboard yields its published link."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(
        host="https://dev.example.cloud.databricks.com",
        dashboards=[dashboard("Sales", "abc123")],
    )
    monkeypatch.setattr(dash_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["dash-links", "Sales", "dev"])

    assert result.exit_code == 0
    assert "/dashboardsv3/abc123/published" in result.output


def testDashLinksWarnsOnDuplicates(env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    """Duplicate dashboard names trigger a warning but still resolve the first."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(
        dashboards=[dashboard("Sales", "first"), dashboard("Sales", "second")],
    )
    monkeypatch.setattr(dash_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["dash-links", "Sales", "dev"])

    assert result.exit_code == 0
    assert "found 2 dashboards" in result.output
    assert "/dashboardsv3/first/published" in result.output


def testDashLinksNotFound(env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing dashboard is reported as not found."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(dashboards=[dashboard("Other", "x")])
    monkeypatch.setattr(dash_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["dash-links", "Missing", "dev"])

    assert result.exit_code == 0
    assert "(not found)" in result.output
