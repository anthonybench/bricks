"""Shared output formatting helpers for sleepybricks."""

from __future__ import annotations

from typing import Sequence

from tabulate import tabulate


def renderTable(
    rows: Sequence[Sequence[object]],
    headers: Sequence[str],
    table_style: str,
) -> str:
    """Render rows as a tabulate table.

    Args:
        rows: Row sequences to render.
        headers: Column headers.
        table_style: Tabulate table format name (from the shared config).

    Returns:
        The rendered table string.
    """

    return tabulate(rows, headers=list(headers), tablefmt=table_style)
