from __future__ import annotations
from datetime import datetime, timedelta, timezone
from graph.provider import GraphDataProvider
from graph.users import fetch_all_licensed_users
from models.findings import DormantUsersFinding, FindingStatus, UserSummary
from models.graph import User

DORMANT_THRESHOLD_DAYS = 90


class DormantUserFinder:
    def __init__(self, provider: GraphDataProvider) -> None:
        self._provider = provider

    def run(self) -> DormantUsersFinding:
        try:
            users = fetch_all_licensed_users(self._provider)
            if not users:
                return DormantUsersFinding(status=FindingStatus.SUCCESS, total_count=0)

            # If no user has signInActivity, the tenant lacks AAD Premium — skip
            if all(u.signInActivity is None for u in users):
                return DormantUsersFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason="Sign-in activity unavailable for this tenant.",
                )

            cutoff = datetime.now(timezone.utc) - timedelta(days=DORMANT_THRESHOLD_DAYS)
            dormant = [u for u in users if self._is_dormant(u, cutoff)]
            examples = [
                UserSummary(display_name=u.displayName, user_principal_name=u.userPrincipalName)
                for u in dormant[:3]
            ]
            return DormantUsersFinding(
                status=FindingStatus.SUCCESS,
                total_count=len(dormant),
                examples=examples,
            )
        except Exception as exc:
            return DormantUsersFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Dormant user analysis failed: {exc}",
            )

    @staticmethod
    def _is_dormant(user: User, cutoff: datetime) -> bool:
        if user.signInActivity is None:
            return True
        last = user.signInActivity.lastSignInDateTime
        return last is None or last < cutoff
