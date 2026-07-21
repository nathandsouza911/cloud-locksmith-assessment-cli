from __future__ import annotations
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class FindingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class UserSummary(BaseModel):
    display_name: str
    user_principal_name: str


class LicenseWasteFinding(BaseModel):
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    active_units: int = 0
    consumed_units: int = 0
    # Units paid for but not assigned to any account. "Potentially reclaimable",
    # NOT proven waste — a buffer of spare seats can be intentional.
    unassigned_units: int = 0
    # Priced only for SKUs present in the pricing map; unknown SKUs contribute 0.
    estimated_reclaimable_monthly_usd: float = 0.0
    estimated_reclaimable_annual_usd: float = 0.0
    priced_unassigned_units: int = 0
    unpriced_unassigned_units: int = 0
    unknown_skus: list[str] = Field(default_factory=list)
    partial_pricing_warning: str | None = None
    pricing_source: str = "Microsoft public list prices (approximate)"


class DormantUsersFinding(BaseModel):
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    total_count: int = 0
    examples: list[UserSummary] = Field(default_factory=list)


class DisabledLicensedFinding(BaseModel):
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    total_count: int = 0
    examples: list[UserSummary] = Field(default_factory=list)


class GlobalAdminsFinding(BaseModel):
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    count: int = 0
    risk_level: Literal["Good", "Moderate", "High"] = "Good"


class MFACoverageFinding(BaseModel):
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    privileged_user_count: int = 0
    mfa_registered_count: int = 0
    coverage_pct: float = 0.0


# ── New controls ──────────────────────────────────────────────────────────────


class TenantMFAFinding(BaseModel):
    """Tenant-wide MFA registration coverage (all enabled users)."""
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    total_users: int = 0
    mfa_registered_count: int = 0
    coverage_pct: float = 0.0


class RoleMemberSummary(BaseModel):
    role_name: str
    member_count: int


class PrivilegedRolesFinding(BaseModel):
    """Members of high-privilege directory roles beyond Global Administrator."""
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    # Distinct users holding at least one high-privilege role.
    distinct_privileged_users: int = 0
    roles: list[RoleMemberSummary] = Field(default_factory=list)


class GuestUsersFinding(BaseModel):
    """External (guest) collaboration inventory."""
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    total_count: int = 0
    examples: list[UserSummary] = Field(default_factory=list)


class StaleGuestsFinding(BaseModel):
    """Guest accounts with no sign-in for 90+ days (or never)."""
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    total_count: int = 0
    examples: list[UserSummary] = Field(default_factory=list)


class SecurityDefaultsFinding(BaseModel):
    """Whether Entra Security Defaults are enabled."""
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    enabled: bool | None = None


class ConditionalAccessFinding(BaseModel):
    """Conditional Access policy inventory (presence only, no rule internals)."""
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    policy_count: int = 0
    enabled_count: int = 0
    report_only_count: int = 0
    examples: list[str] = Field(default_factory=list)


class UserConsentFinding(BaseModel):
    """Whether ordinary users may consent to third-party applications."""
    status: FindingStatus = FindingStatus.SUCCESS
    skipped_reason: str | None = None
    # True = users can grant app consent themselves (higher risk).
    users_can_consent: bool | None = None
    detail: str | None = None
