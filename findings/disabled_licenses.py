from __future__ import annotations
from graph.provider import GraphDataProvider
from graph.users import fetch_disabled_users
from models.findings import DisabledLicensedFinding, FindingStatus, UserSummary


class DisabledLicensedFinder:
    def __init__(self, provider: GraphDataProvider) -> None:
        self._provider = provider

    def run(self) -> DisabledLicensedFinding:
        try:
            users = fetch_disabled_users(self._provider)
            licensed = [u for u in users if u.assignedLicenses]
            examples = [
                UserSummary(
                    display_name=u.displayName or u.userPrincipalName or u.id,
                    user_principal_name=u.userPrincipalName or u.id,
                )
                for u in licensed[:3]
            ]
            return DisabledLicensedFinding(
                status=FindingStatus.SUCCESS,
                total_count=len(licensed),
                examples=examples,
            )
        except Exception as exc:
            return DisabledLicensedFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"User data unavailable: {exc}",
            )
