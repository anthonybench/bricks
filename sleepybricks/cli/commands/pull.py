"""``pull-repo`` command: pull the latest commit for a repo across workspaces."""

from __future__ import annotations

import typer
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import RepoInfo

from sleepybricks.cli.runtime import bootstrap
from sleepybricks.core.workspace import getClient
from sleepybricks.utils.formatting import renderTable


def _findRepo(client: WorkspaceClient, repo_name: str) -> tuple[RepoInfo | None, int]:
    """Find a repo by name within a workspace.

    Args:
        client: The workspace client to query.
        repo_name: The repo name to match against repo paths.

    Returns:
        A tuple of the first matching repo (or ``None``) and the total match count.
    """

    matches = [repo for repo in client.repos.list() if repo_name in (repo.path or "")]
    return (matches[0] if matches else None, len(matches))


def register(app: typer.Typer) -> None:
    """Register the ``pull-repo`` command.

    Args:
        app: Root Typer application instance.

    Returns:
        None.
    """

    @app.command("pull-repo")
    def pullRepo(
        repo_name: str = typer.Argument(..., help="Repo name to pull (matched within repo path)."),
        profile_list: str = typer.Argument(
            ..., help="Comma-separated profiles, e.g. 'dev,stg,us'."
        ),
    ) -> None:
        """Pull the latest commit for a repo across one or more workspaces.

        Args:
            repo_name: The repo name to update.
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
                repo, count = _findRepo(client, repo_name)
                if repo is None:
                    rows.append([label, repo_name, "-", "⚠️ not found (is it a git folder?)"])
                    continue
                if count > 1:
                    typer.secho(
                        f"⚠️ {label}: {count} repos match '{repo_name}'; using {repo.path}.",
                        fg=typer.colors.YELLOW,
                    )

                if repo.branch:
                    client.repos.update(repo.id, branch=repo.branch)
                else:
                    client.repos.update(repo.id)

                updated = client.repos.get(repo.id)
                head = (updated.head_commit_id or "")[:8] or "-"
                rows.append([label, repo.path, updated.branch or "-", f"✅ pulled @ {head}"])
            except Exception as error:  # noqa: BLE001 - surface any SDK/auth error per profile
                rows.append([label, repo_name, "-", f"⚠️ error: {error}"])

        typer.echo()
        typer.echo(
            renderTable(
                rows,
                headers=["Workspace", "Repo", "Branch", "Status"],
                table_style=config.table_style,
            )
        )
