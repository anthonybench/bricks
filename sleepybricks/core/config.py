"""Application configuration for sleepybricks."""

from __future__ import annotations

from dataclasses import dataclass, field

from sleepybricks.core.sleepy_params import DEFAULT_PARAMS, loadSleepyParams


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration for the sleepybricks CLI.

    Attributes:
        table_style: Tabulate table format used for all rendered output.
        serverless_warehouse_name: Name of the serverless SQL warehouse to use
            for compute. May contain the ``<env>`` token, which is replaced with
            the active profile name at lookup time (e.g. ``<env>_serverless_warehouse``
            becomes ``dev_serverless_warehouse`` for the ``dev`` profile).
        env_emojis: Mapping of profile name to a decorative emoji.
        display_names: Mapping of profile name to a friendly display label.
    """

    table_style: str = "simple"
    serverless_warehouse_name: str = "<env>_serverless_warehouse"
    env_emojis: dict[str, str] = field(default_factory=dict)
    display_names: dict[str, str] = field(default_factory=dict)

    def warehouseNameFor(self, profile: str) -> str:
        """Resolve the serverless warehouse name for a profile.

        Args:
            profile: The active databricks profile name.

        Returns:
            The warehouse name with the ``<env>`` token substituted.
        """

        return self.serverless_warehouse_name.replace("<env>", profile)

    def labelFor(self, profile: str) -> str:
        """Build a decorated label for a profile for use in output.

        Combines the configured emoji and display name, falling back to the raw
        profile name when no mappings are present.

        Args:
            profile: The active databricks profile name.

        Returns:
            A human-friendly label such as ``👩‍💻 Development (dev)``.
        """

        emoji = self.env_emojis.get(profile)
        display = self.display_names.get(profile)
        parts: list[str] = []
        if emoji:
            parts.append(emoji)
        if display:
            parts.append(f"{display} ({profile})")
        else:
            parts.append(profile)
        return " ".join(parts)


def getConfig() -> AppConfig:
    """Return application configuration sourced from the shared sleepy config.

    Reads ``~/sleepyconfig/params.yml`` (creating it with defaults on first
    run) and applies the sleepybricks-owned parameters.

    Returns:
        The immutable application configuration instance.
    """

    params = loadSleepyParams()

    env_emojis = params.get("env_emojis") or {}
    display_names = params.get("display_names") or {}

    return AppConfig(
        table_style=str(params.get("bricks_table_style", DEFAULT_PARAMS["bricks_table_style"])),
        serverless_warehouse_name=str(
            params.get("serverless_warehouse_name", DEFAULT_PARAMS["serverless_warehouse_name"])
        ),
        env_emojis={str(k): str(v) for k, v in dict(env_emojis).items()},
        display_names={str(k): str(v) for k, v in dict(display_names).items()},
    )
