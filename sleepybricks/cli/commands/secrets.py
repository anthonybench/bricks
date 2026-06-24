"""``write-secret`` and ``create-scope`` commands for managing secrets."""

from __future__ import annotations

import typer
from databricks.sdk import WorkspaceClient

from sleepybricks.cli.runtime import bootstrap
from sleepybricks.core.workspace import getClient
from sleepybricks.utils.formatting import renderTable


def _scopeExists(client: WorkspaceClient, scope_name: str) -> bool:
    """Return whether a secret scope exists in the workspace.

    Args:
        client: The workspace client to query.
        scope_name: The scope name to check.

    Returns:
        ``True`` when the scope is present.
    """

    return any(scope.name == scope_name for scope in client.secrets.list_scopes())


def _parseWriteSecretArgs(parts: list[str]) -> tuple[str, str, str, str]:
    """Parse the flexible ``write-secret`` positional arguments.

    Supports both the four-arg form (``scope key value profiles``) and the
    dotted three-arg form (``scope.key value profiles``).

    Args:
        parts: Raw positional arguments.

    Returns:
        A tuple of (scope, key, value, profile_list).

    Raises:
        typer.BadParameter: If the arguments don't match a supported form.
    """

    if len(parts) == 4:
        scope, key, value, profile_list = parts
        return scope, key, value, profile_list

    if len(parts) == 3:
        scoped_key, value, profile_list = parts
        if "." not in scoped_key:
            raise typer.BadParameter(
                "Three-argument form expects '<scope>.<key>', e.g. 'my_scope.my_key'."
            )
        scope, key = scoped_key.split(".", 1)
        if not scope or not key:
            raise typer.BadParameter("Both scope and key are required in '<scope>.<key>'.")
        return scope, key, value, profile_list

    raise typer.BadParameter(
        "Usage: write-secret <scope> <key> <value> <profiles>  |  "
        "write-secret <scope>.<key> <value> <profiles>"
    )


def register(app: typer.Typer) -> None:
    """Register the secret-management commands.

    Args:
        app: Root Typer application instance.

    Returns:
        None.
    """

    @app.command("write-secret")
    def writeSecret(
        parts: list[str] = typer.Argument(
            ...,
            help="<scope> <key> <value> <profiles>  OR  <scope>.<key> <value> <profiles>",
        ),
    ) -> None:
        """Write a secret into a scope across one or more workspaces.

        The scope must already exist; if it does not, the relevant
        ``create-scope`` command is suggested.

        Args:
            parts: Positional arguments in one of the two supported forms.

        Returns:
            None.
        """

        scope_name, secret_key, secret_value, profile_list = _parseWriteSecretArgs(parts)
        config, profiles = bootstrap(profile_list)

        rows: list[list[str]] = []
        for profile in profiles:
            label = config.labelFor(profile)
            try:
                client = getClient(profile)
                if not _scopeExists(client, scope_name):
                    rows.append(
                        [
                            label,
                            scope_name,
                            secret_key,
                            f"⚠️ scope missing — run: sleepybricks create-scope {scope_name} {profile}",
                        ]
                    )
                    continue
                client.secrets.put_secret(scope_name, secret_key, string_value=secret_value)
                rows.append([label, scope_name, secret_key, "✅ written"])
            except Exception as error:  # noqa: BLE001 - surface any SDK/auth error per profile
                rows.append([label, scope_name, secret_key, f"⚠️ error: {error}"])

        typer.echo()
        typer.echo(
            renderTable(
                rows,
                headers=["Workspace", "Scope", "Key", "Status"],
                table_style=config.table_style,
            )
        )

    @app.command("create-scope")
    def createScope(
        scope_name: str = typer.Argument(..., help="Name of the secret scope to create."),
        profile_list: str = typer.Argument(
            ..., help="Comma-separated profiles, e.g. 'dev,stg,us'."
        ),
    ) -> None:
        """Create a secret scope across one or more workspaces.

        Existing scopes are skipped and reported as already present.

        Args:
            scope_name: The scope name to create.
            profile_list: Comma-separated list of profiles.

        Returns:
            None.
        """

        config, profiles = bootstrap(profile_list)

        rows: list[list[str]] = []
        for profile in profiles:
            label = config.labelFor(profile)
            try:
                client = getClient(profile)
                if _scopeExists(client, scope_name):
                    rows.append([label, scope_name, "↩️ already existed"])
                    continue
                client.secrets.create_scope(scope_name)
                rows.append([label, scope_name, "✅ created"])
            except Exception as error:  # noqa: BLE001 - surface any SDK/auth error per profile
                rows.append([label, scope_name, f"⚠️ error: {error}"])

        typer.echo()
        typer.echo(
            renderTable(
                rows, headers=["Workspace", "Scope", "Status"], table_style=config.table_style
            )
        )
