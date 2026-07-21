from __future__ import annotations
from datetime import datetime, timedelta, timezone
from graph.provider import GraphDataProvider
from models.findings import StaleGuestsFinding, FindingStatus, UserSummary
from models.graph import User

STALE_GUEST_THRESHOLD_DAYS = 90


def _summary(u: User) -> UserSummary:
    return UserSummary(
        display_name=u.displayName or u.userPrincipalName or u.id,
        user_principal_name=u.userPrincipalName or u.id,
    )


class StaleGuestsFinder:
    """Guest accounts with no sign-in for 90+ days (or never signed in)."""

    def __init__(self, provider: GraphDataProvider) -> None:
        self._provider = provider

    def run(self) -> StaleGuestsFinding:
        try:
            guests = self._provider.get_guest_users()
            if not guests:
                return StaleGuestsFinding(status=FindingStatus.SUCCESS, total_count=0)

            # No sign-in activity anywhere → tenant lacks the premium data to judge staleness.
            if all(g.signInActivity is None for g in guests):
                return StaleGuestsFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason="Sign-in activity unavailable for this tenant.",
                )

            cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_GUEST_THRESHOLD_DAYS)
            stale = [g for g in guests if self._is_stale(g, cutoff)]
            return StaleGuestsFinding(
                status=FindingStatus.SUCCESS,
                total_count=len(stale),
                examples=[_summary(g) for g in stale[:3]],
            )
        except Exception as exc:
            return StaleGuestsFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Stale guest analysis failed: {exc}",
            )

    @staticmethod
    def _is_stale(guest: User, cutoff: datetime) -> bool:
        if guest.signInActivity is None:
            return True
        last = guest.signInActivity.lastSignInDateTime
        return last is None or last < cutoff
