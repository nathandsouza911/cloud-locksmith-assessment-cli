from __future__ import annotations
from graph.errors import GraphAPIError
from graph.provider import GraphDataProvider
from models.findings import UserConsentFinding, FindingStatus

# Built-in permission-grant policies that, when assigned to the default user role,
# allow ordinary (non-admin) users to consent to third-party applications.
_SELF_CONSENT_MARKER = "ManagePermissionGrantsForSelf"


class UserConsentFinder:
    """Whether ordinary users may grant consent to third-party applications."""

    def __init__(self, provider: GraphDataProvider) -> None:
        self._provider = provider

    def run(self) -> UserConsentFinding:
        try:
            policy = self._provider.get_authorization_policy()
            assigned = policy.defaultUserRolePermissions.permissionGrantPoliciesAssigned
            can_consent = any(_SELF_CONSENT_MARKER in p for p in assigned)
            if can_consent:
                detail = (
                    "Ordinary users can consent to third-party apps. Restricting this to "
                    "admin approval reduces illicit-consent (OAuth phishing) risk."
                )
            else:
                detail = "User app consent is restricted to administrators (recommended)."
            return UserConsentFinding(
                status=FindingStatus.SUCCESS,
                users_can_consent=can_consent,
                detail=detail,
            )
        except GraphAPIError as exc:
            if exc.status_code == 403:
                return UserConsentFinding(
                    status=FindingStatus.SKIPPED,
                    skipped_reason="User consent settings require Policy.Read.All admin consent.",
                )
            return UserConsentFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Authorization policy unavailable: [{exc.status_code}] {exc.error_code}",
            )
        except Exception as exc:
            return UserConsentFinding(
                status=FindingStatus.ERROR,
                skipped_reason=f"Authorization policy unavailable: {exc}",
            )
