"""``dash-links`` command: find dashboard links across workspaces."""

from __future__ import annotations

import typer

from sleepybricks.cli.runtime import bootstrap
from sleepybricks.core.workspace import getClient
from sleepybricks.utils.formatting import renderTable


def _buildLink(host: str, dashboard_id: str) -> str:
    """Build the published link for a lakeview dashboard.

    Args:
        host: The workspace host URL.
        dashboard_id: The dashboard id.

    Returns:
        The published dashboard URL.
    """

    return f"{host.rstrip('/')}/dashboardsv3/{dashboard_id}/published"


def register(app: typer.Typer) -> None:
    """Register the ``dash-links`` command.

    Args:
        app: Root Typer application instance.

    Returns:
        None.
    """

    @app.command("dash-links")
    def dashLinks(
        dashboard_name: str = typer.Argument(..., help="Case-sensitive dashboard name to match."),
        profile_list: str = typer.Argument(
            ..., help="Comma-separated profiles, e.g. 'dev,stg,us'."
        ),
    ) -> None:
        """Fetch published links for a dashboard across one or more workspaces.

        Dashboard names are not unique in databricks; the first match in each
        workspace is used and a warning is shown when duplicates exist.

        Args:
            dashboard_name: Case-sensitive dashboard display name.
            profile_list: Comma-separated list of profiles to search.

        Returns:
            None.
        """

        config, profiles = bootstrap(profile_list)

        rows: list[list[str]] = []
        for profile in profiles:
            label = config.labelFor(profile)
            try:
                client = getClient(profile)
                matches = [
                    dashboard
                    for dashboard in client.lakeview.list()
                    if dashboard.display_name == dashboard_name
                ]
            except Exception as error:  # noqa: BLE001 - surface any SDK/auth error per profile
                rows.append([label, f"⚠️ error: {error}"])
                continue

            if not matches:
                rows.append([label, "(not found)"])
                continue

            if len(matches) > 1:
                typer.secho(
                    f"⚠️ {label}: found {len(matches)} dashboards named "
                    f"'{dashboard_name}'; using the first.",
                    fg=typer.colors.YELLOW,
                )

            first = matches[0]
            rows.append([label, _buildLink(client.config.host, first.dashboard_id)])

        typer.echo(f"\n✨ {dashboard_name} ✨\n")
        typer.echo(renderTable(rows, headers=["Workspace", "Link"], table_style=config.table_style))
