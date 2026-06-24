"""``create-workspace-folder`` command: make a workspace folder everywhere."""

from __future__ import annotations

import typer
from databricks.sdk.errors import NotFound

from sleepybricks.cli.runtime import bootstrap
from sleepybricks.core.workspace import getClient
from sleepybricks.utils.formatting import renderTable


def _normalizePath(folder_name: str) -> str:
    """Normalize a folder name into an absolute workspace path.

    Args:
        folder_name: The folder name or path provided by the user.

    Returns:
        An absolute workspace path beginning with ``/``.
    """

    folder_name = folder_name.strip()
    return folder_name if folder_name.startswith("/") else f"/{folder_name}"


def register(app: typer.Typer) -> None:
    """Register the ``create-workspace-folder`` command.

    Args:
        app: Root Typer application instance.

    Returns:
        None.
    """

    @app.command("create-workspace-folder")
    def createWorkspaceFolder(
        folder_name: str = typer.Argument(..., help="Folder path under the workspace root."),
        profile_list: str = typer.Argument(
            ..., help="Comma-separated profiles, e.g. 'dev,stg,us'."
        ),
    ) -> None:
        """Create a workspace folder across one or more workspaces.

        Existing folders are skipped and reported as already present.

        Args:
            folder_name: The folder path to create (``/`` prefixed if omitted).
            profile_list: Comma-separated list of profiles.

        Returns:
            None.
        """

        config, profiles = bootstrap(profile_list)
        path = _normalizePath(folder_name)

        rows: list[list[str]] = []
        for profile in profiles:
            label = config.labelFor(profile)
            try:
                client = getClient(profile)
                try:
                    client.workspace.get_status(path)
                    rows.append([label, path, "↩️ already existed"])
                    continue
                except NotFound:
                    pass
                client.workspace.mkdirs(path)
                rows.append([label, path, "✅ created"])
            except Exception as error:  # noqa: BLE001 - surface any SDK/auth error per profile
                rows.append([label, path, f"⚠️ error: {error}"])

        typer.echo()
        typer.echo(
            renderTable(
                rows, headers=["Workspace", "Path", "Status"], table_style=config.table_style
            )
        )
