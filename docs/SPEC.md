# Specification

`sleepybricks` is a Typer CLI for running databricks operations across multiple
workspaces from a single command. It wraps the official `databricks-sdk` and
authenticates by reading profiles from `~/.databrickscfg`.

## Authentication

- Profiles are read from `~/.databrickscfg` (overridable via the standard
  `DATABRICKS_CONFIG_FILE` env var, which the SDK also honors).
- Every command takes a `profile_list`: a comma-separated list of profile names
  such as `dev,stg,us`.
- If the config file is missing, or any requested profile is absent, the CLI
  exits with a clear, actionable message (it never silently fails to auth).

## Commands

| Command                    | Form                                                                                  | Notes                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `dash-links`               | `dash-links <dashboard_name> <profiles>`                                              | Case-sensitive match. First match per workspace; warns on duplicates.              |
| `sql`                      | `sql -f <file.sql> <profiles>` or `sql -s "<sql>" <profiles>`                         | `-f` requires a `.sql` extension. Needs a serverless SQL warehouse (see config).   |
| `write-secret`             | `write-secret <scope> <key> <value> <profiles>` or `write-secret <scope>.<key> <value> <profiles>` | Scope must exist; otherwise the relevant `create-scope` command is suggested.      |
| `create-scope`             | `create-scope <scope_name> <profiles>`                                                | Idempotent: existing scopes are skipped and reported.                              |
| `pull-repo`                | `pull-repo <repo_name> <profiles>`                                                    | Matches the repo by name within its path; pulls latest on its branch.              |
| `run-job`                  | `run-job <job_name> <profiles>`                                                       | Case-sensitive exact match. Job names are not unique; if more than one matches, nothing runs and the count is reported. |
| `create-workspace-folder`  | `create-workspace-folder <folder_name> <profiles>`                                    | Path is `/`-prefixed if omitted. Existing folders are skipped and reported.        |

## Output

All results are rendered with [tabulate](https://pypi.org/project/tabulate/),
using the `bricks_table_style` from the shared sleepy config. Per-workspace rows
are decorated with the configured emoji and display name for each profile.

## Configuration

Settings live in the shared sleepy-utils config at `~/sleepyconfig/params.yml`.
Each sleepy util owns only its own `<tool>_<name>` keys and never references
another tool's keys. When the file is absent, sleepybricks writes only its own
section. When a required value is missing, it prints its config snippet and
asks the user to verify their sleepyconfig. The sleepybricks keys are:

- `bricks_table_style` — tabulate table style for all output.
- `bricks_serverless_warehouse_name` — serverless SQL warehouse name; the
  `<env>` token is substituted with the active profile name at lookup time.
- `bricks_env_emojis` — per-profile emoji for output labels.
- `bricks_display_names` — per-profile friendly names for output labels.

## Error handling

- Credential/profile problems abort the whole command with a single message.
- Per-workspace failures (auth, missing warehouse, API errors) are captured into
  the output table/section for that workspace so one bad workspace does not abort
  the others.
