"""Lightweight fakes for the databricks ``WorkspaceClient`` used in tests."""

from __future__ import annotations

from types import SimpleNamespace

from databricks.sdk.errors import NotFound


class _FakeSecrets:
    def __init__(self, scopes: list[str]) -> None:
        self._scopes = list(scopes)
        self.put_calls: list[tuple[str, str, str | None]] = []
        self.created: list[str] = []

    def list_scopes(self):
        return [SimpleNamespace(name=name) for name in self._scopes]

    def create_scope(self, scope: str) -> None:
        self.created.append(scope)
        self._scopes.append(scope)

    def put_secret(self, scope: str, key: str, *, string_value: str | None = None) -> None:
        self.put_calls.append((scope, key, string_value))


class _FakeWorkspace:
    def __init__(self, existing: list[str]) -> None:
        self._existing = set(existing)
        self.made: list[str] = []

    def get_status(self, path: str):
        if path not in self._existing:
            raise NotFound(f"{path} not found")
        return SimpleNamespace(path=path)

    def mkdirs(self, path: str) -> None:
        self.made.append(path)
        self._existing.add(path)


class _FakeLakeview:
    def __init__(self, dashboards: list[SimpleNamespace]) -> None:
        self._dashboards = dashboards

    def list(self):
        return iter(self._dashboards)


class FakeClient:
    """A configurable stand-in for ``WorkspaceClient``."""

    def __init__(
        self,
        *,
        host: str = "https://example.cloud.databricks.com",
        scopes: list[str] | None = None,
        folders: list[str] | None = None,
        dashboards: list[SimpleNamespace] | None = None,
    ) -> None:
        self.config = SimpleNamespace(host=host)
        self.secrets = _FakeSecrets(scopes or [])
        self.workspace = _FakeWorkspace(folders or [])
        self.lakeview = _FakeLakeview(dashboards or [])


def dashboard(display_name: str, dashboard_id: str) -> SimpleNamespace:
    """Build a fake lakeview dashboard object.

    Args:
        display_name: The dashboard display name.
        dashboard_id: The dashboard id.

    Returns:
        A namespace mimicking an SDK ``Dashboard``.
    """

    return SimpleNamespace(display_name=display_name, dashboard_id=dashboard_id)
