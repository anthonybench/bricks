# sleepybricks

`sleepybricks` is a succinct [Typer](https://typer.tiangolo.com/)-based CLI that wraps the [databricks SDK](https://databricks-sdk-py.readthedocs.io/) to run operations **across multiple workspaces** at once.

It authenticates by reading profiles from `~/.databrickscfg` (the same file the databricks CLI uses) and gives a graceful error when that file or a requested profile is missing.

## Authentication

Every command takes a comma-separated `profile_list` (e.g. `dev,stg,us`) naming profiles defined in `~/.databrickscfg`. Create that file with the databricks CLI if you don't have one:

```sh
databricks configure --token   # repeat once per workspace/profile
```

## Install

Install the CLI globally with [uv](https://docs.astral.sh/uv/):

```sh
uv tool install sleepybricks
```

## Commands

| Command                                                       | Description                                                                |
| ------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `dash-links <dashboard_name> <profiles>`                      | Print the published link for a dashboard in each workspace.                |
| `sql -s "<sql>" <profiles>` / `sql -f <file.sql> <profiles>`  | Execute raw sql or a file on the serverless warehouse set in sleepyconfig. |
| `write-secret <scope> <key> <value> <profiles>`               | Write a secret into an existing scope in each workspace.                   |
| `write-secret <scope>.<key> <value> <profiles>`               | Same, using the dotted shorthand.                                          |
| `create-scope <scope_name> <profiles>`                        | Create a secret scope in each workspace (skips existing).                  |
| `pull-repo <repo_name> <profiles>`                            | Pull the latest commit for a git repo in each workspace.                   |
| `create-workspace-folder <folder_name> <profiles>`            | Create a workspace folder in each workspace (skips existing).              |

```sh
sleepybricks dash-links "Scheduled Triage Device Metrics" "dev,eu"
sleepybricks sql -s "select * from my_tbl" "dev,stg,us"
sleepybricks sql -f "./query.sql" "dev,stg"
sleepybricks write-secret my_scope.api_key "s3cret" "dev,stg"
sleepybricks pull-repo databricks_templates "dev,stg,us"
sleepybricks create-workspace-folder databricks_templates "dev,stg,us"
sleepybricks --help
```

Dashboard names are matched case-sensitively and are not unique in databricks; the first match per workspace is used and a warning is shown when duplicates exist. The `sql` command needs a serverless SQL warehouse in each workspace — see Configuration below.

## Configuration

`sleepybricks` is a _sleepy util_ and reads its settings from the shared `~/sleepyconfig/params.yml`. Each sleepy util owns only its own `<tool>_<name>` keys; sleepybricks uses the `bricks_` prefix. If the file is absent, sleepybricks writes **only its own section** below and prints a note. If a value it needs is missing, it prints this snippet and asks you to verify your config. Keys:

- `bricks_table_style` — [tabulate](https://pypi.org/project/tabulate/) table style used for all output (e.g. `simple`, `rounded_grid`, `github`).
- `bricks_serverless_warehouse_name` — name of the serverless SQL warehouse used for compute. The `<env>` token is replaced with the active profile name, so the default `<env>_serverless_warehouse` resolves to `dev_serverless_warehouse` for the `dev` profile. Use a static value (no token) if your warehouse name is the same everywhere.
- `bricks_env_emojis` — per-profile emoji used to decorate output labels.
- `bricks_display_names` — per-profile friendly name used in output labels.

```yaml
# sleepybricks
bricks_table_style: simple
bricks_serverless_warehouse_name: <env>_serverless_warehouse
bricks_env_emojis:
  dev: "👩‍💻"
  stg: "🔧"
  us: "🇺🇸"
bricks_display_names:
  dev: "Development"
  stg: "Staging"
  us: "United States"
```

## Development

Create the environment and install in editable mode with [uv](https://docs.astral.sh/uv/):

```sh
uv venv
uv pip install -e ".[dev]"
```

Then run `uv run pytest`, or `./tools/test.sh`. Tests use fakes for the databricks client and never touch a real workspace. Tear down with `rm -rf .venv`.

## Documentation

- [Specification](docs/SPEC.md) — what the tool does
