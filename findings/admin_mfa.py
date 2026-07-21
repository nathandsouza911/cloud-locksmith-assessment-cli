from __future__ import annotations
from graph.errors import GraphAPIError
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
            admin_regs = [r for r in registrations if r.id in admin_ids]
            mfa_count = sum(1 for r in admin_regs if r.isMfaRegistered)
            total = len(self._admin_users)
            pct = round(mfa_count / total * 100, 1) if total > 0 else 0.0
            return MFACoverageFinding(
                status=FindingStatus.SUCCESS,
                privileged_user_count=total,
                mfa_registered_count=mfa_count,
                coverage_pct=pct,
            )
        except GraphAPIError as exc:
            if exc.status_code == 403:
                return MFACoverageFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason=_classify_mfa_403(exc.error_code, exc.graph_message),
                )
            return MFACoverageFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"MFA analysis failed: [{exc.status_code}] {exc.error_code}",
            )
        except Exception as exc:
            return MFACoverageFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"MFA analysis failed: {exc}",
            )


def _classify_mfa_403(error_code: str, graph_message: str) -> str:
    # Named error codes take priority — these are stable Graph API identifiers.
    if error_code == "Authentication_RequestFromNonPremiumTenantOrB2CTenant":
        return "MFA registration reporting requires Microsoft Entra ID P1 or P2 licensing."
    if error_code == "Authorization_RequestDenied":
        return "MFA registration reporting requires Reports.Read.All admin consent."

    # Fallback: keyword match on the message body (less stable, but covers undocumented variants).
    msg = graph_message.lower()
    if "consent" in msg:
        return "MFA registration reporting requires Reports.Read.All admin consent."
    if any(k in msg for k in ("license", "premium", "aad_premium", "entra")):
        return "MFA registration reporting requires Microsoft Entra ID P1 or P2 licensing."
    if any(k in msg for k in ("role", "privilege", "insufficient")):
        return (
            "Signed-in user must be a Global Administrator, Reports Reader, "
            "Security Reader, or Security Administrator."
        )
    return (
        "MFA registration data unavailable. Possible causes: "
        "(1) Admin consent not granted for Reports.Read.All, "
        "(2) Signed-in user lacks Reports Reader or Security Reader role, "
        "(3) Tenant does not have Microsoft Entra ID P1/P2 licensing."
    )
