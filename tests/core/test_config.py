"""Tests for sleepybricks application configuration."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from sleepybricks.core.config import getConfig
from sleepybricks.core.sleepy_params import PARAMS_PATH_ENV_VAR


def testGetConfigReadsDefaults(env: SimpleNamespace) -> None:
    """The default template yields the documented sleepybricks defaults."""

    config = getConfig()

    assert config.table_style == "simple"
    assert config.serverless_warehouse_name == "<env>_serverless_warehouse"
    assert config.env_emojis["dev"] == "👩‍💻"
    assert config.display_names["us"] == "United States"


def testWarehouseNameSubstitutesEnvToken(env: SimpleNamespace) -> None:
    """The ``<env>`` token is replaced with the active profile name."""

    config = getConfig()

    assert config.warehouseNameFor("dev") == "dev_serverless_warehouse"


def testWarehouseNameStaticWhenNoToken(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A static warehouse name (no token) is returned verbatim for any profile."""

    params_path = tmp_path / "params.yml"
    params_path.write_text(
        "bricks_table_style: simple\n"
        "bricks_serverless_warehouse_name: global_warehouse\n"
        "bricks_env_emojis: {}\n"
        "bricks_display_names: {}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(PARAMS_PATH_ENV_VAR, str(params_path))

    config = getConfig()

    assert config.warehouseNameFor("stg") == "global_warehouse"


def testLabelForCombinesEmojiAndDisplayName(env: SimpleNamespace) -> None:
    """Labels combine emoji and display name, falling back to the raw profile."""

    config = getConfig()

    assert config.labelFor("dev") == "👩‍💻 Development (dev)"
    assert config.labelFor("unknown") == "unknown"
