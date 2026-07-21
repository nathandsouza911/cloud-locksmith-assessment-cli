from __future__ import annotations
from graph.errors import GraphAPIError
from graph.provider import GraphDataProvider
from graph.mfa import fetch_credential_registrations
from findings.admin_mfa import _classify_mfa_403
from models.findings import TenantMFAFinding, FindingStatus


class TenantMFAFinder:
    """Tenant-wide MFA registration coverage across all reported user accounts."""

    def __init__(self, provider: GraphDataProvider) -> None:
        self._provider = provider

    def run(self) -> TenantMFAFinding:
        try:
            registrations = fetch_credential_registrations(self._provider)
            if not registrations:
                return TenantMFAFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason="Credential registration data unavailable.",
                )
            total = len(registrations)
            registered = sum(1 for r in registrations if r.isMfaRegistered)
            pct = round(registered / total * 100, 1) if total else 0.0
            return TenantMFAFinding(
                status=FindingStatus.SUCCESS,
                total_users=total,
                mfa_registered_count=registered,
                coverage_pct=pct,
            )
        except GraphAPIError as exc:
            if exc.status_code == 403:
                return TenantMFAFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason=_classify_mfa_403(exc.error_code, exc.graph_message),
                )
            return TenantMFAFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Tenant MFA analysis failed: [{exc.status_code}] {exc.error_code}",
            )
        except Exception as exc:
            return TenantMFAFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Tenant MFA analysis failed: {exc}",
            )
