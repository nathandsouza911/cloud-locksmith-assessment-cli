from __future__ import annotations
from graph.provider import GraphDataProvider
from models.findings import GuestUsersFinding, FindingStatus, UserSummary
from models.graph import User


def _summary(u: User) -> UserSummary:
    return UserSummary(
        display_name=u.displayName or u.userPrincipalName or u.id,
        user_principal_name=u.userPrincipalName or u.id,
    )


class GuestUsersFinder:
    """Inventory of external (guest) accounts in the tenant."""

    def __init__(self, provider: GraphDataProvider) -> None:
        self._provider = provider

    def run(self) -> GuestUsersFinding:
        try:
            guests = self._provider.get_guest_users()
            examples = [_summary(u) for u in guests[:3]]
            return GuestUsersFinding(
                status=FindingStatus.SUCCESS,
                total_count=len(guests),
                examples=examples,
            )
        except Exception as exc:
            return GuestUsersFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Guest user data unavailable: {exc}",
            )
