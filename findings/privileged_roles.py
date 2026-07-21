from __future__ import annotations
from graph.provider import GraphDataProvider
from graph.roles import fetch_privileged_role_members
from models.findings import PrivilegedRolesFinding, RoleMemberSummary, FindingStatus


class PrivilegedRolesFinder:
    """Enumerate members of high-impact directory roles (privileged sprawl)."""

    def __init__(self, provider: GraphDataProvider) -> None:
        self._provider = provider

    def run(self) -> PrivilegedRolesFinding:
        try:
            members_by_role = fetch_privileged_role_members(self._provider)
            if not members_by_role:
                return PrivilegedRolesFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason="No activated privileged directory roles found.",
                )
            roles = [
                RoleMemberSummary(role_name=name, member_count=len(members))
                for name, members in sorted(members_by_role.items())
                if members
            ]
            distinct_ids = {
                m.id for members in members_by_role.values() for m in members
            }
            return PrivilegedRolesFinding(
                status=FindingStatus.SUCCESS,
                distinct_privileged_users=len(distinct_ids),
                roles=roles,
            )
        except Exception as exc:
            return PrivilegedRolesFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Privileged role data unavailable: {exc}",
            )
