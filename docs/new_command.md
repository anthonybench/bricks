# Adding a Command

Commands are auto-discovered: drop a module in `sleepybricks/cli/commands/` that
exposes a `register(app)` function and it is wired up automatically by
`cli/commands/__init__.py`. No central registry to edit.

## 1. Create the command module

`sleepybricks/cli/commands/<name>.py` (snake_case file, kebab-case command name):

```python
"""``my-command`` command: one-line summary."""

from __future__ import annotations

import typer

from sleepybricks.cli.runtime import bootstrap
from sleepybricks.core.workspace import getClient
from sleepybricks.utils.formatting import renderTable


def register(app: typer.Typer) -> None:
    """Register the ``my-command`` command."""

    @app.command("my-command")
    def myCommand(
        target: str = typer.Argument(..., help="What to act on."),
        profile_list: str = typer.Argument(
            ..., help="Comma-separated profiles, e.g. 'dev,stg,us'."
        ),
    ) -> None:
        """Do the thing across one or more workspaces."""

        config, profiles = bootstrap(profile_list)

        rows: list[list[str]] = []
        for profile in profiles:
            label = config.labelFor(profile)
            try:
                client = getClient(profile)
                # ... call the SDK via `client` ...
                rows.append([label, "✅ done"])
            except Exception as error:  # noqa: BLE001 - surface per-profile failures
                rows.append([label, f"⚠️ error: {error}"])

        typer.echo()
        typer.echo(
            renderTable(rows, headers=["Workspace", "Status"], table_style=config.table_style)
        )
```

## Conventions

- **`bootstrap(profile_list)`** → `(config, profiles)`. It loads config and
  validates the profiles against `~/.databrickscfg`, exiting cleanly with a
  helpful message on bad credentials or config. Always start here.
- **One client per profile** via `getClient(profile)`. Loop over `profiles`.
- **Never abort the whole run for one workspace** — wrap each profile's work in
  `try/except` and record the failure as a row, so the other workspaces still run.
- **Always render with `renderTable(...)`** using `config.table_style`; label
  each workspace row with `config.labelFor(profile)` (emoji + display name).
- **Non-unique resources**: dashboards/jobs/repos can share a name. Decide
  per command whether to use the first match (warn) or refuse to act (see
  `dash_links.py` vs `run_job.py`).
- **Compute (SQL/warehouses)**: resolve the warehouse with
  `config.warehouseNameFor(profile)` + `findWarehouseId(...)`, run via
  `runStatement(...)` (see `core/workspace.py` and `sql.py`).

Good examples to copy: `run_job.py` (refuse on duplicates), `dash_links.py`
(first match + warning), `secrets.py` (multiple commands in one module).

## 2. (Only if you need new config)

Config keys are owned per-tool and must use the `bricks_` prefix. To add one:

1. Add the key + default to `DEFAULT_PARAMS` **and** `DEFAULT_PARAMS_SNIPPET` in
   `core/sleepy_params.py` (keep them in sync).
2. Add a field to `AppConfig` and read it in `getConfig()` with
   `requireParam(params, "bricks_<name>")` in `core/config.py`.

Missing values are surfaced automatically: `requireParam` prints the tool's
snippet and asks the user to verify their `~/sleepyconfig/params.yml`.

## 3. Add a test

`tests/cli/test_<name>.py`, driving the command through `CliRunner` with the
`FakeClient` stand-in instead of a real workspace:

```python
import sleepybricks.cli.commands.my_command as cmd
from sleepybricks.main import app
from tests.conftest import writeDatabricksConfig
from tests.fakes import FakeClient

runner = CliRunner()


def testMyCommand(env, monkeypatch):
    writeDatabricksConfig(env.cfg, ["dev"])           # define profiles
    fake = FakeClient(...)                             # configure fake state
    monkeypatch.setattr(cmd, "getClient", lambda profile: fake)

    result = runner.invoke(app, ["my-command", "target", "dev"])

    assert result.exit_code == 0
```

- The autouse `env` fixture (in `tests/conftest.py`) isolates the sleepy config
  and points `~/.databrickscfg` at a temp file, so tests never touch a real
  workspace.
- If your command uses a databricks service the fake doesn't model yet, add it
  to `FakeClient` in `tests/fakes.py`.

## 4. Update docs

Add the command to the table in `README.md` and `docs/SPEC.md`, a usage example
in `docs/test_drive.md`, and the file tree in `docs/OUTLINE.md`.
