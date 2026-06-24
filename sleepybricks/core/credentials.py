"""Databricks credential discovery from ``~/.databrickscfg``.

sleepybricks authenticates by reading profiles from the standard databricks CLI
config file. This module locates that file, validates requested profiles, and
raises :class:`CredentialError` with an actionable message when something is
missing. The CLI layer turns those errors into graceful console output.
"""

from __future__ import annotations

import configparser
import os
from pathlib import Path

# Honors the same override the databricks SDK/CLI uses, so all auth stays in sync.
DATABRICKS_CONFIG_FILE_ENV = "DATABRICKS_CONFIG_FILE"


class CredentialError(Exception):
    """Raised when databricks credentials cannot be resolved."""


def getDatabricksConfigPath() -> Path:
    """Return the path to the databricks config file.

    Returns:
        The resolved config path, honoring the ``DATABRICKS_CONFIG_FILE``
        environment override when set.
    """

    override = os.getenv(DATABRICKS_CONFIG_FILE_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".databrickscfg"


def loadAvailableProfiles() -> list[str]:
    """Return the profile names defined in the databricks config file.

    Returns:
        A list of profile (section) names.

    Raises:
        CredentialError: If the config file does not exist.
    """

    config_path = getDatabricksConfigPath()
    if not config_path.exists():
        raise CredentialError(
            f"Databricks config not found at {config_path}.\n"
            "sleepybricks authenticates by reading profiles from this file.\n"
            "Create it by running `databricks configure --token` (repeat per workspace), "
            "then retry."
        )

    parser = configparser.ConfigParser()
    parser.read(config_path)
    return list(parser.sections())


def parseProfileList(profile_list: str) -> list[str]:
    """Parse a comma-separated profile list into a clean list of names.

    Args:
        profile_list: A comma-separated string such as ``"dev,stg,us"``.

    Returns:
        The parsed, de-whitespaced profile names in order.

    Raises:
        CredentialError: If no profiles are present after parsing.
    """

    profiles = [profile.strip() for profile in profile_list.split(",") if profile.strip()]
    if not profiles:
        raise CredentialError(
            "No profiles provided. Pass a comma-separated list like 'dev,stg,us'."
        )
    return profiles


def resolveProfiles(profile_list: str) -> list[str]:
    """Validate that every requested profile exists in the config file.

    Args:
        profile_list: A comma-separated string of profile names.

    Returns:
        The validated profile names in the order requested.

    Raises:
        CredentialError: If the config is missing or any profile is unknown.
    """

    requested = parseProfileList(profile_list)
    available = loadAvailableProfiles()
    missing = [profile for profile in requested if profile not in available]
    if missing:
        raise CredentialError(
            f"Profile(s) {', '.join(missing)} not found in {getDatabricksConfigPath()}.\n"
            f"Available profiles: {', '.join(available) if available else '(none)'}"
        )
    return requested
