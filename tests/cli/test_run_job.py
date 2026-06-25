"""Tests for the ``run-job`` command."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

import sleepybricks.cli.commands.run_job as run_job_cmd
from sleepybricks.main import app
from tests.conftest import writeDatabricksConfig
from tests.fakes import FakeClient, job

runner = CliRunner()


def testRunJobStartsUniqueJob(env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    """A single exact match is triggered and its run link is reported."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(
        host="https://dev.example.cloud.databricks.com", jobs=[job("Nightly ETL", 42)]
    )
    monkeypatch.setattr(run_job_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["run-job", "Nightly ETL", "dev"])

    assert result.exit_code == 0
    assert fake.jobs.run_calls == [42]
    assert "/jobs/42/runs/" in result.output


def testRunJobDoesNotRunWhenDuplicateNames(
    env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Multiple exact matches are not run and the count is reported."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(jobs=[job("Nightly ETL", 1), job("Nightly ETL", 2), job("Nightly ETL", 3)])
    monkeypatch.setattr(run_job_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["run-job", "Nightly ETL", "dev"])

    assert result.exit_code == 0
    assert fake.jobs.run_calls == []
    assert "3 jobs share" in result.output


def testRunJobIsCaseSensitive(env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    """A name differing only by case is not treated as a match."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(jobs=[job("Nightly ETL", 1)])
    monkeypatch.setattr(run_job_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["run-job", "nightly etl", "dev"])

    assert result.exit_code == 0
    assert fake.jobs.run_calls == []
    assert "(not found)" in result.output


def testRunJobNotFound(env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing job is reported as not found and nothing is run."""

    writeDatabricksConfig(env.cfg, ["dev"])
    fake = FakeClient(jobs=[job("Other", 1)])
    monkeypatch.setattr(run_job_cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["run-job", "Missing", "dev"])

    assert result.exit_code == 0
    assert fake.jobs.run_calls == []
    assert "(not found)" in result.output
