"""Tests for the shared sleepy params loading (sleepybricks copy)."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from sleepybricks.core.sleepy_params import (
    PARAMS_PATH_ENV_VAR,
    loadSleepyParams,
    requireParam,
)


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
    assert params["bricks_serverless_warehouse_name"] == "<env>_serverless_warehouse"
    assert params["bricks_env_emojis"]["stg"] == "🔧"
    assert any("defaults" in message for message in messages)

    # Only this tool's own section is written — no cross-tool keys.
    written = params_path.read_text(encoding="utf-8")
    assert "datapeek_" not in written
    assert "convert_" not in written


def testRequireParamReturnsPresentValue() -> None:
    """A present key is returned unchanged."""

    assert requireParam({"bricks_table_style": "github"}, "bricks_table_style") == "github"


def testRequireParamGuidesUserWhenMissing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing key prints the tool's snippet, says to verify, and exits."""

    monkeypatch.setenv(PARAMS_PATH_ENV_VAR, str(tmp_path / "params.yml"))

    with pytest.raises(typer.Exit):
        requireParam({"bricks_table_style": "simple"}, "bricks_display_names")

    err = capsys.readouterr().err
    assert "verify your sleepyconfig" in err
    assert "# sleepybricks" in err
    assert "bricks_display_names" in err
