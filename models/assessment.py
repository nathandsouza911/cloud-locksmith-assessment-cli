from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from models.findings import (
    LicenseWasteFinding, DormantUsersFinding, DisabledLicensedFinding,
    GlobalAdminsFinding, MFACoverageFinding, TenantMFAFinding,
    PrivilegedRolesFinding, GuestUsersFinding, StaleGuestsFinding,
    SecurityDefaultsFinding, ConditionalAccessFinding, UserConsentFinding,
    FindingStatus,
)
from models.posture import PostureScore

# Bumped independently of the package version. Identifies the set of controls
# evaluated and the report/JSON schema shape. See docs/SCHEMA.md.
SCHEMA_VERSION = "2.0.0"


class AssessmentResult(BaseModel):
    """Single container for every finding plus the derived posture score.

    Passed to each report writer so adding a control does not require changing
    every report function signature.
    """
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str = SCHEMA_VERSION

    license_waste: LicenseWasteFinding
    global_admins: GlobalAdminsFinding
    privileged_mfa: MFACoverageFinding
    tenant_mfa: TenantMFAFinding
    privileged_roles: PrivilegedRolesFinding
    dormant_users: DormantUsersFinding
    disabled_licensed_users: DisabledLicensedFinding
    guest_users: GuestUsersFinding
    stale_guests: StaleGuestsFinding
    security_defaults: SecurityDefaultsFinding
    conditional_access: ConditionalAccessFinding
    user_consent: UserConsentFinding
    posture: PostureScore

    def has_errors(self) -> bool:
        """True if any control failed to run (ERROR) — a runtime/config problem,
        distinct from a control that simply found an issue."""
        return any(
            getattr(self, name).status == FindingStatus.ERROR
            for name in _FINDING_FIELDS
        )

    def has_failures(self) -> bool:
        """True if the posture score contains at least one FAIL control —
        i.e. the assessment surfaced a significant security gap."""
        return any(c.status == "FAIL" for c in self.posture.controls)


_FINDING_FIELDS = [
    "license_waste", "global_admins", "privileged_mfa", "tenant_mfa",
    "privileged_roles", "dormant_users", "disabled_licensed_users",
    "guest_users", "stale_guests", "security_defaults",
    "conditional_access", "user_consent",
]
