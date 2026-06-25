"""``run-job`` command: trigger a job by exact name across workspaces."""

from __future__ import annotations

import typer
from databricks.sdk import WorkspaceClient

from sleepybricks.cli.runtime import bootstrap
from sleepybricks.core.workspace import getClient
from sleepybricks.utils.formatting import renderTable


def _findJobsByName(client: WorkspaceClient, job_name: str) -> list:
    """Return all jobs whose name matches exactly (case-sensitive).

    The server-side ``name`` filter narrows the listing; the client-side check
    enforces an exact, case-sensitive match.

    Args:
        client: The workspace client to query.
        job_name: The exact job name to match.

    Returns:
        A list of matching jobs.
    """

    return [
        job
        for job in client.jobs.list(name=job_name)
        if job.settings is not None and job.settings.name == job_name
    ]


def _runLink(host: str, job_id: int, run_id: int) -> str:
    """Build the link to a job run.

    Args:
        host: The workspace host URL.
        job_id: The job id.
        run_id: The triggered run id.

    Returns:
        The job-run URL.
    """

    return f"{host.rstrip('/')}/jobs/{job_id}/runs/{run_id}"


def register(app: typer.Typer) -> None:
    """Register the ``run-job`` command.

    Args:
        app: Root Typer application instance.

    Returns:
        None.
    """

    @app.command("run-job")
    def runJob(
        job_name: str = typer.Argument(..., help="Case-sensitive job name to match and run."),
        profile_list: str = typer.Argument(
            ..., help="Comma-separated profiles, e.g. 'dev,stg,us'."
        ),
    ) -> None:
        """Trigger a job by exact name across one or more workspaces.

        Job names are not unique in databricks. If more than one job shares the
        exact name in a workspace, the job is NOT run and the count is reported.

        Args:
            job_name: Case-sensitive job name.
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
                matches = _findJobsByName(client, job_name)

                if not matches:
                    rows.append([label, "-", "(not found)"])
                    continue

                if len(matches) > 1:
                    typer.secho(
                        f"⚠️ {label}: {len(matches)} jobs share the exact name "
                        f"'{job_name}' — not run.",
                        fg=typer.colors.YELLOW,
                    )
                    rows.append([label, "-", f"⚠️ {len(matches)} jobs share this name — not run"])
                    continue

                job = matches[0]
                waiter = client.jobs.run_now(job.job_id)
                rows.append(
                    [
                        label,
                        str(job.job_id),
                        f"✅ started: {_runLink(client.config.host, job.job_id, waiter.run_id)}",
                    ]
                )
            except Exception as error:  # noqa: BLE001 - surface any SDK/auth error per profile
                rows.append([label, "-", f"⚠️ error: {error}"])

        typer.echo()
        typer.echo(
            renderTable(
                rows, headers=["Workspace", "Job ID", "Status"], table_style=config.table_style
            )
        )
