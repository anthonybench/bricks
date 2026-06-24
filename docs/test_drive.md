# Test Drive Guide

## Setup

Create a virtual environment and install the package with dev dependencies using [uv](https://docs.astral.sh/uv/):

```bash
uv venv
uv pip install -e ".[dev]"
```

The `-e` flag installs in editable mode — changes to source files take effect immediately without reinstalling.

## Running Tests

```bash
uv run pytest tests/
```

To see verbose output:

```bash
uv run pytest tests/ -v
```

The suite uses a configurable fake databricks client (`tests/fakes.py`) and isolates both the shared sleepy config and `~/.databrickscfg` to temp paths (`tests/conftest.py`), so tests never touch your real config or a live workspace.

## Authentication

`sleepybricks` reads workspace credentials from `~/.databrickscfg` — the same file the databricks CLI uses. Create it (once per workspace) before running real commands:

```bash
databricks configure --token
```

Every command takes a comma-separated `profile_list` naming the profiles to act on, e.g. `dev,stg,us`. If the config file or a requested profile is missing, the command exits with an actionable message and does nothing.

## Using the CLI

After setup, the `sleepybricks` command is available in your shell (or run it with `uv run sleepybricks ...`).

### `dash-links` — find dashboard links across workspaces

```bash
sleepybricks dash-links "Scheduled Triage Device Metrics" "dev,eu"
```

Dashboard names are matched case-sensitively. Names are not unique in databricks; the first match per workspace is used and a warning is shown when duplicates exist.

### `sql` — run a query across workspaces

```bash
sleepybricks sql -s "select * from my_tbl" "dev,stg,us"
sleepybricks sql -f ./queries/audit.sql "dev,stg"
```

Exactly one of `-s/--string` or `-f/--file` is required; `-f` requires a `.sql` extension. SQL needs a serverless SQL warehouse in each workspace, resolved from the configured `bricks_serverless_warehouse_name` (see Configuration).

### `write-secret` — write a secret into a scope

```bash
sleepybricks write-secret my_scope api_key "s3cret" "dev,stg"
sleepybricks write-secret my_scope.api_key "s3cret" "dev,stg"   # dotted shorthand
```

The scope must already exist; if it does not, the relevant `create-scope` command is suggested.

### `create-scope` — create a secret scope

```bash
sleepybricks create-scope my_scope "dev,stg,us"
```

Idempotent: existing scopes are skipped and reported as already present.

### `pull-repo` — pull the latest commit for a repo

```bash
sleepybricks pull-repo databricks_templates "dev,stg,us"
```

Matches the repo by name within its workspace path and pulls the latest commit on its current branch.

### `create-workspace-folder` — make a workspace folder

```bash
sleepybricks create-workspace-folder /Shared/my_folder "dev,stg"
```

The path is `/`-prefixed if omitted. Existing folders are skipped and reported.

### Help

```bash
sleepybricks --help
sleepybricks sql --help
```

## Configuration

`sleepybricks` reads its settings from the shared `~/sleepyconfig/params.yml`, writing only its own `bricks_*` section if the file is absent. See the [README](../README.md#configuration) for the full list of keys (`bricks_table_style`, `bricks_serverless_warehouse_name`, `bricks_env_emojis`, `bricks_display_names`).

## Teardown

```bash
rm -rf .venv
```
