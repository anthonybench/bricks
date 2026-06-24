"""Tests for the shared sleepy params loading (sleepybricks copy)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sleepybricks.core.sleepy_params import PARAMS_PATH_ENV_VAR, loadSleepyParams


def testLoadSleepyParamsWritesDefaultsWhenMissing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing params file is created with defaults and announced."""

    params_path = tmp_path / "fresh" / "params.yml"
    monkeypatch.setenv(PARAMS_PATH_ENV_VAR, str(params_path))

    messages: list[str] = []
    params = loadSleepyParams(echo=messages.append)

    assert params_path.exists()
    assert params["bricks_table_style"] == "simple"
    assert params["serverless_warehouse_name"] == "<env>_serverless_warehouse"
    assert params["env_emojis"]["stg"] == "🔧"
    assert any("wrote defaults" in message for message in messages)
