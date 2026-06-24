"""Shared pytest fixtures for sleepybricks tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from sleepybricks.core.credentials import DATABRICKS_CONFIG_FILE_ENV
from sleepybricks.core.sleepy_params import DEFAULT_PARAMS_SNIPPET, PARAMS_PATH_ENV_VAR


@pytest.fixture(autouse=True)
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Isolate the shared sleepy config and databricks config from the real home.

    The sleepy params file is pre-seeded so commands don't emit the first-run
    message, and the databricks config path points at a (by default absent)
    temp file so tests can never reach a real workspace.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        A namespace exposing the temp ``params`` and ``cfg`` paths.
    """

    params_path = tmp_path / "sleepyconfig" / "params.yml"
    params_path.parent.mkdir(parents=True, exist_ok=True)
    params_path.write_text(DEFAULT_PARAMS_SNIPPET, encoding="utf-8")
    monkeypatch.setenv(PARAMS_PATH_ENV_VAR, str(params_path))

    cfg_path = tmp_path / ".databrickscfg"
    monkeypatch.setenv(DATABRICKS_CONFIG_FILE_ENV, str(cfg_path))

    return SimpleNamespace(params=params_path, cfg=cfg_path)


def writeDatabricksConfig(cfg_path: Path, profiles: list[str]) -> None:
    """Write a minimal ``.databrickscfg`` with the given profile sections.

    Args:
        cfg_path: Destination config path.
        profiles: Profile names to define.

    Returns:
        None.
    """

    blocks = [
        f"[{profile}]\nhost = https://{profile}.example.cloud.databricks.com\ntoken = dapi-{profile}\n"
        for profile in profiles
    ]
    cfg_path.write_text("\n".join(blocks), encoding="utf-8")
