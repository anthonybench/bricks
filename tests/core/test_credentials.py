"""Tests for databricks credential discovery."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from sleepybricks.core.credentials import (
    CredentialError,
    loadAvailableProfiles,
    parseProfileList,
    resolveProfiles,
)
from tests.conftest import writeDatabricksConfig


def testParseProfileListSplitsAndTrims() -> None:
    """Comma-separated profiles are split and whitespace-trimmed."""

    assert parseProfileList(" dev, stg ,us ") == ["dev", "stg", "us"]


def testParseProfileListRejectsEmpty() -> None:
    """An empty profile list raises a credential error."""

    with pytest.raises(CredentialError):
        parseProfileList("  ,  ")


def testLoadAvailableProfilesErrorsWhenConfigMissing(env: SimpleNamespace) -> None:
    """A missing config file produces an actionable error."""

    with pytest.raises(CredentialError) as excinfo:
        loadAvailableProfiles()

    assert "Databricks config not found" in str(excinfo.value)


def testResolveProfilesReturnsRequestedWhenPresent(env: SimpleNamespace) -> None:
    """All requested profiles are returned when present in the config."""

    writeDatabricksConfig(env.cfg, ["dev", "stg", "us"])

    assert resolveProfiles("dev,us") == ["dev", "us"]


def testResolveProfilesReportsMissingProfiles(env: SimpleNamespace) -> None:
    """Unknown profiles raise an error listing the available ones."""

    writeDatabricksConfig(env.cfg, ["dev"])

    with pytest.raises(CredentialError) as excinfo:
        resolveProfiles("dev,prod")

    message = str(excinfo.value)
    assert "prod" in message
    assert "dev" in message
