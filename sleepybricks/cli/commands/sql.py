"""``sql`` command: run a SQL statement across workspaces."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from databricks.sdk.service.sql import StatementResponse, StatementState

from sleepybricks.cli.runtime import bootstrap
from sleepybricks.core.config import AppConfig
from sleepybricks.core.workspace import findWarehouseId, getClient, runStatement
from sleepybricks.utils.formatting import renderTable


def _resolveStatement(sql_file: Optional[Path], sql_string: Optional[str]) -> str:
    """Resolve the SQL text from the mutually-exclusive ``-f``/``-s`` options.

    Args:
        sql_file: Path to a ``.sql`` file, when provided.
        sql_string: Literal SQL text, when provided.

    Returns:
        The SQL statement to execute.

    Raises:
        typer.BadParameter: If neither or both options are provided, or the file
            is invalid.
    """

    if bool(sql_file) == bool(sql_string):
        raise typer.BadParameter("Provide exactly one of -f/--file or -s/--string.")

    if sql_string is not None:
        return sql_string

    assert sql_file is not None
    if sql_file.suffix.lower() != ".sql":
        raise typer.BadParameter(f"SQL file must have a .sql extension: {sql_file}")
    if not sql_file.is_file():
        raise typer.BadParameter(f"SQL file does not exist: {sql_file}")
    return sql_file.read_text(encoding="utf-8")


def _renderResult(response: StatementResponse, config: AppConfig) -> str:
    """Render a statement response as text for a single workspace.

    Args:
        response: The terminal statement response.
        config: Application configuration (for table style).

    Returns:
        Rendered output describing the result or failure.
    """

    state = response.status.state if response.status is not None else None

    if state == StatementState.SUCCEEDED:
        manifest = response.manifest
        result = response.result
        columns = (
            [column.name for column in manifest.schema.columns]
            if manifest is not None and manifest.schema is not None and manifest.schema.columns
            else []
        )
        data = result.data_array if result is not None and result.data_array else []
        if not data:
            return "✅ succeeded (no rows returned)"
        return renderTable(data, headers=columns, table_style=config.table_style)

    if response.status is not None and response.status.error is not None:
        return f"⚠️ {state}: {response.status.error.message}"
    return f"⚠️ {state}"


def register(app: typer.Typer) -> None:
    """Register the ``sql`` command.

    Args:
        app: Root Typer application instance.

    Returns:
        None.
    """

    @app.command("sql")
    def sql(
        profile_list: str = typer.Argument(
            ..., help="Comma-separated profiles, e.g. 'dev,stg,us'."
        ),
        sql_file: Optional[Path] = typer.Option(
            None, "-f", "--file", help="Path to a .sql file to execute."
        ),
        sql_string: Optional[str] = typer.Option(
            None, "-s", "--string", help="Literal SQL string to execute."
        ),
    ) -> None:
        """Execute a SQL statement across one or more workspaces.

        Requires a serverless SQL warehouse (resolved from the configured
        ``serverless_warehouse_name``) in each target workspace.

        Args:
            profile_list: Comma-separated list of profiles to run against.
            sql_file: Path to a ``.sql`` file (mutually exclusive with ``-s``).
            sql_string: Literal SQL text (mutually exclusive with ``-f``).

        Returns:
            None.
        """

        config, profiles = bootstrap(profile_list)
        statement = _resolveStatement(sql_file, sql_string)

        for profile in profiles:
            label = config.labelFor(profile)
            typer.echo(f"\n─── {label} ───")
            warehouse_name = config.warehouseNameFor(profile)
            try:
                client = getClient(profile)
                warehouse_id = findWarehouseId(client, warehouse_name)
                if warehouse_id is None:
                    typer.secho(
                        f"⚠️ serverless warehouse '{warehouse_name}' not found in this workspace.",
                        fg=typer.colors.YELLOW,
                    )
                    continue
                response = runStatement(client, statement, warehouse_id)
            except Exception as error:  # noqa: BLE001 - surface any SDK/auth error per profile
                typer.secho(f"⚠️ error: {error}", fg=typer.colors.YELLOW)
                continue

            typer.echo(_renderResult(response, config))
