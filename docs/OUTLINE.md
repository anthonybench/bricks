# Project Outline

How the repository is laid out and what each area is responsible for.

```txt
bricks/                              # repository root (PyPI package: sleepybricks)
├── sleepybricks/                    # Application package
│   ├── __init__.py
│   ├── main.py                      # Entrypoint: assembles the root Typer app
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── runtime.py               # Shared command bootstrap (config + profile resolution)
│   │   └── commands/
│   │       ├── __init__.py          # Auto-registers all command modules
│   │       ├── dash_links.py        # `dash-links <name> <profiles>`
│   │       ├── sql.py               # `sql -f|-s ... <profiles>`
│   │       ├── secrets.py           # `write-secret ...` and `create-scope ...`
│   │       ├── pull.py              # `pull-repo <name> <profiles>`
│   │       └── workspace_folder.py  # `create-workspace-folder <name> <profiles>`
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                # App config (table style, warehouse name, labels)
│   │   ├── sleepy_params.py         # Shared sleepy-utils config (~/sleepyconfig/params.yml)
│   │   ├── credentials.py           # ~/.databrickscfg discovery and profile validation
│   │   ├── workspace.py             # WorkspaceClient factory, warehouse lookup, SQL runner
│   │   └── logging.py               # Shared logging setup
│   └── utils/
│       ├── __init__.py
│       └── formatting.py            # Shared tabulate table helper
├── tests/
│   ├── conftest.py                  # Isolates sleepy + databricks config from the real home
│   ├── fakes.py                     # Configurable WorkspaceClient stand-in
│   ├── cli/
│   │   ├── test_sql.py
│   │   ├── test_secrets.py
│   │   └── test_workspace_and_dash.py
│   └── core/
│       ├── test_config.py
│       ├── test_credentials.py
│       └── test_sleepy_params.py
├── tools/                           # Scripts for humans to run
│   ├── format.sh                    # Format shell and Python
│   └── test.sh                      # Run the test suite
├── docs/                            # Single-purpose documentation files
│   ├── SPEC.md                      # Application specification
│   ├── OUTLINE.md                   # This file
│   ├── test_drive.md                # Setup, testing, and CLI usage guide
│   └── publish.md                   # Release to PyPI
├── LICENSE
├── README.md                        # Project overview, commands, configuration
└── pyproject.toml                   # Package metadata and dependencies
```

## Responsibilities

- **`cli/commands/`** — one module per command (or closely related pair). Each exposes a `register(app)` function; `commands/__init__.py` discovers and registers them so new commands can be dropped in freely.
- **`cli/runtime.py`** — `bootstrap()` loads the shared config and resolves the requested profiles, converting credential problems into a clean non-zero exit. Lives outside `commands/` so it is not picked up by command auto-discovery.
- **`core/credentials.py`** — locates `~/.databrickscfg` (honoring `DATABRICKS_CONFIG_FILE`), lists available profiles, and validates the requested ones, raising `CredentialError` with actionable messages.
- **`core/workspace.py`** — builds a `WorkspaceClient` per profile, resolves the serverless warehouse id by name, and runs SQL statements to completion.
- **`core/config.py`** — the single place that maps the shared sleepy params onto a typed `AppConfig` (table style, warehouse name template, per-profile emoji/display labels).
- **`core/sleepy_params.py`** — the shared "sleepy utils" config contract; an identical copy lives in each sleepy tool.
- **`utils/`** — cross-cutting helpers with no command-specific logic (table formatting).

## Adding a command

1. Create `sleepybricks/cli/commands/<name>.py` exposing `register(app)`.
2. Inside, define the Typer command and call `bootstrap(profile_list)` to get the config and validated profiles.
3. Iterate profiles, build a client with `getClient(profile)`, capture per-profile failures into the result, and render with `renderTable(...)`.
4. Add a test under `tests/cli/` using the `FakeClient` from `tests/fakes.py`.
