"""Databricks workspace client helpers shared across commands."""

from __future__ import annotations

import time

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementResponse, StatementState

# Terminal statement states; anything else means the query is still in flight.
_TERMINAL_STATES = {
    StatementState.SUCCEEDED,
    StatementState.FAILED,
    StatementState.CANCELED,
    StatementState.CLOSED,
}


def getClient(profile: str) -> WorkspaceClient:
    """Build a workspace client for a databricks profile.

    The client reads host/token from the standard databricks config file
    (``~/.databrickscfg`` or ``DATABRICKS_CONFIG_FILE``).

    Args:
        profile: The databricks profile name.

    Returns:
        A configured :class:`WorkspaceClient`.
    """

    return WorkspaceClient(profile=profile)


def findWarehouseId(client: WorkspaceClient, warehouse_name: str) -> str | None:
    """Return the id of the warehouse matching a name, if present.

    Args:
        client: The workspace client to query.
        warehouse_name: The exact (case-sensitive) warehouse name to find.

    Returns:
        The warehouse id, or ``None`` when no warehouse matches.
    """

    for endpoint in client.warehouses.list():
        if endpoint.name == warehouse_name:
            return endpoint.id
    return None


def runStatement(
    client: WorkspaceClient,
    statement: str,
    warehouse_id: str,
    poll_interval_seconds: float = 2.0,
) -> StatementResponse:
    """Execute a SQL statement and block until it reaches a terminal state.

    Args:
        client: The workspace client to run against.
        statement: The SQL text to execute.
        warehouse_id: The serverless SQL warehouse id to run on.
        poll_interval_seconds: Delay between status polls while the statement runs.

    Returns:
        The terminal :class:`StatementResponse`.
    """

    response = client.statement_execution.execute_statement(
        statement=statement,
        warehouse_id=warehouse_id,
        wait_timeout="50s",
    )

    while response.status is not None and response.status.state not in _TERMINAL_STATES:
        time.sleep(poll_interval_seconds)
        response = client.statement_execution.get_statement(response.statement_id)

    return response
