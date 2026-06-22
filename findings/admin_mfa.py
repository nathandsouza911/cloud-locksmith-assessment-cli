from __future__ import annotations
from graph.provider import GraphDataProvider
from graph.mfa import fetch_credential_registrations
from models.findings import MFACoverageFinding, FindingStatus
from models.graph import User


class AdminMFAFinder:
    def __init__(self, provider: GraphDataProvider, admin_users: list[User]) -> None:
        self._provider = provider
        self._admin_users = admin_users

    def run(self) -> MFACoverageFinding:
        if not self._admin_users:
            return MFACoverageFinding(
                status=FindingStatus.SKIPPED,
                skipped_reason="No privileged users found to evaluate.",
            )
        try:
            registrations = fetch_credential_registrations(self._provider)
            if not registrations:
                return MFACoverageFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason="Credential registration data unavailable.",
                )
            admin_ids = {u.id for u in self._admin_users}
            admin_regs = [r for r in registrations if r.userId in admin_ids]
            mfa_count = sum(1 for r in admin_regs if r.isMfaRegistered)
            total = len(self._admin_users)
            pct = round(mfa_count / total * 100, 1) if total > 0 else 0.0
            return MFACoverageFinding(
                status=FindingStatus.SUCCESS,
                privileged_user_count=total,
                mfa_registered_count=mfa_count,
                coverage_pct=pct,
            )
        except Exception as exc:
            return MFACoverageFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"MFA analysis failed: {exc}",
            )
