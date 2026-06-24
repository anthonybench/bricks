"""Shared runtime helpers for sleepybricks CLI commands.

This module lives outside ``cli/commands`` so it is not picked up by the command
auto-discovery in :mod:`sleepybricks.cli.commands`.
"""

from __future__ import annotations

import typer

from sleepybricks.core.config import AppConfig, getConfig
from sleepybricks.core.credentials import CredentialError, resolveProfiles


def bootstrap(profile_list: str) -> tuple[AppConfig, list[str]]:
    """Load config and resolve profiles, exiting gracefully on credential errors.

    Args:
        profile_list: A comma-separated string of profile names.

    Returns:
        A tuple of the application config and the validated profile names.

    Raises:
        typer.Exit: With code 1 when credentials cannot be resolved.
    """

    config = getConfig()
    try:
        profiles = resolveProfiles(profile_list)
    except CredentialError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from error
    return config, profiles
