from __future__ import annotations
from graph.provider import GraphDataProvider
from models.graph import User

_ALL_FIELDS = [
    "id", "displayName", "userPrincipalName",
    "accountEnabled", "assignedLicenses", "signInActivity",
]
_DISABLED_FIELDS = ["id", "displayName", "userPrincipalName", "assignedLicenses"]


def fetch_all_licensed_users(provider: GraphDataProvider) -> list[User]:
    try:
        users = provider.get_users(select=_ALL_FIELDS)
    except Exception:
        # signInActivity requires AuditLog.Read.All; fall back so dormant check returns SKIPPED
        users = provider.get_users(select=_DISABLED_FIELDS)
    return [u for u in users if u.assignedLicenses]


def fetch_disabled_users(provider: GraphDataProvider) -> list[User]:
    return provider.get_users(
        select=_DISABLED_FIELDS,
        filter_expr="accountEnabled eq false",
    )
