"""Generate deterministic, fully synthetic sample reports for the repository.

The data below is invented ("Contoso") — it contains NO real tenant information,
user data, or secrets. Running this script regenerates the committed samples in
docs/samples/ so users can inspect the output BEFORE granting any Graph consent.

Usage (from repo root):
    uv run python scripts/generate_samples.py
"""
from __future__ import annotations
import json
import pathlib

from models.findings import (
    FindingStatus, LicenseWasteFinding, DormantUsersFinding, DisabledLicensedFinding,
    GlobalAdminsFinding, MFACoverageFinding, TenantMFAFinding, PrivilegedRolesFinding,
    RoleMemberSummary, GuestUsersFinding, StaleGuestsFinding, SecurityDefaultsFinding,
    ConditionalAccessFinding, UserConsentFinding, UserSummary,
)
from models.assessment import AssessmentResult
from findings.posture_score import evaluate_posture
from reports.markdown_report import write_markdown
from reports.pdf_report import write_pdf

_S = FindingStatus.SUCCESS
_SAMPLES = pathlib.Path("docs/samples")

# Fixed timestamp so regenerated samples are byte-stable in git (except the PDF,
# which embeds its own creation date).
_GENERATED_AT = "2026-01-15T09:00:00+00:00"


def _synthetic_result() -> AssessmentResult:
    license_waste = LicenseWasteFinding(
        status=_S, active_units=175, consumed_units=161, unassigned_units=14,
        estimated_reclaimable_annual_usd=5352.0, estimated_reclaimable_monthly_usd=446.0,
        priced_unassigned_units=12, unpriced_unassigned_units=2,
        unknown_skus=["CONTOSO_ADDON"],
        partial_pricing_warning=(
            "2 reclaimable seat(s) across 1 SKU(s) have no pricing data; the dollar "
            "estimate covers only priced SKUs."),
    )
    global_admins = GlobalAdminsFinding(status=_S, count=4, risk_level="Moderate")
    privileged_mfa = MFACoverageFinding(status=_S, privileged_user_count=6,
                                        mfa_registered_count=6, coverage_pct=100.0)
    tenant_mfa = TenantMFAFinding(status=_S, total_users=150, mfa_registered_count=123,
                                  coverage_pct=82.0)
    privileged_roles = PrivilegedRolesFinding(
        status=_S, distinct_privileged_users=7,
        roles=[
            RoleMemberSummary(role_name="Global Administrator", member_count=4),
            RoleMemberSummary(role_name="Security Administrator", member_count=2),
            RoleMemberSummary(role_name="Exchange Administrator", member_count=2),
        ],
    )
    dormant = DormantUsersFinding(
        status=_S, total_count=6,
        examples=[UserSummary(display_name="Sample Dormant One", user_principal_name="dormant1@contoso.example"),
                  UserSummary(display_name="Sample Dormant Two", user_principal_name="dormant2@contoso.example")],
    )
    disabled = DisabledLicensedFinding(
        status=_S, total_count=2,
        examples=[UserSummary(display_name="Former Employee", user_principal_name="former@contoso.example")],
    )
    guests = GuestUsersFinding(
        status=_S, total_count=14,
        examples=[UserSummary(display_name="Partner Contact", user_principal_name="partner_contoso.example#EXT#@contoso.example")],
    )
    stale_guests = StaleGuestsFinding(
        status=_S, total_count=5,
        examples=[UserSummary(display_name="Old Vendor", user_principal_name="vendor_old#EXT#@contoso.example")],
    )
    security_defaults = SecurityDefaultsFinding(status=_S, enabled=False)
    conditional_access = ConditionalAccessFinding(
        status=_S, policy_count=5, enabled_count=3, report_only_count=1,
        examples=["Require MFA for admins", "Block legacy authentication", "Require compliant device"],
    )
    user_consent = UserConsentFinding(
        status=_S, users_can_consent=True,
        detail=("Ordinary users can consent to third-party apps. Restricting this to "
                "admin approval reduces illicit-consent (OAuth phishing) risk."),
    )
    posture = evaluate_posture(
        privileged_mfa, global_admins, dormant, tenant_mfa,
        security_defaults, conditional_access, user_consent, stale_guests,
    )
    return AssessmentResult(
        generated_at=_GENERATED_AT,
        license_waste=license_waste,
        global_admins=global_admins,
        privileged_mfa=privileged_mfa,
        tenant_mfa=tenant_mfa,
        privileged_roles=privileged_roles,
        dormant_users=dormant,
        disabled_licensed_users=disabled,
        guest_users=guests,
        stale_guests=stale_guests,
        security_defaults=security_defaults,
        conditional_access=conditional_access,
        user_consent=user_consent,
        posture=posture,
    )


def _no_premium_result() -> AssessmentResult:
    """A small tenant WITHOUT Entra ID P1/P2: the license-dependent controls are
    SKIPPED, demonstrating how the tool degrades and how the grade is capped."""
    _P12 = "Requires Microsoft Entra ID P1 or P2 licensing."
    license_waste = LicenseWasteFinding(
        status=_S, active_units=30, consumed_units=28, unassigned_units=2,
        estimated_reclaimable_annual_usd=300.0, estimated_reclaimable_monthly_usd=25.0,
        priced_unassigned_units=2,
    )
    global_admins = GlobalAdminsFinding(status=_S, count=2, risk_level="Good")
    privileged_mfa = MFACoverageFinding(status=FindingStatus.SKIPPED, skipped_reason=_P12)
    tenant_mfa = TenantMFAFinding(status=FindingStatus.SKIPPED, skipped_reason=_P12)
    privileged_roles = PrivilegedRolesFinding(
        status=_S, distinct_privileged_users=2,
        roles=[RoleMemberSummary(role_name="Global Administrator", member_count=2)])
    dormant = DormantUsersFinding(status=FindingStatus.SKIPPED,
                                  skipped_reason="Sign-in activity unavailable for this tenant.")
    disabled = DisabledLicensedFinding(status=_S, total_count=1)
    guests = GuestUsersFinding(status=_S, total_count=2)
    stale_guests = StaleGuestsFinding(status=FindingStatus.SKIPPED,
                                      skipped_reason="Sign-in activity unavailable for this tenant.")
    security_defaults = SecurityDefaultsFinding(status=_S, enabled=True)
    conditional_access = ConditionalAccessFinding(
        status=FindingStatus.SKIPPED,
        skipped_reason=("Conditional Access inventory requires Policy.Read.All admin consent "
                        "and Microsoft Entra ID P1 or P2 licensing."))
    user_consent = UserConsentFinding(status=_S, users_can_consent=False,
                                      detail="User app consent is restricted to administrators (recommended).")
    posture = evaluate_posture(
        privileged_mfa, global_admins, dormant, tenant_mfa,
        security_defaults, conditional_access, user_consent, stale_guests,
    )
    return AssessmentResult(
        generated_at=_GENERATED_AT,
        license_waste=license_waste, global_admins=global_admins, privileged_mfa=privileged_mfa,
        tenant_mfa=tenant_mfa, privileged_roles=privileged_roles, dormant_users=dormant,
        disabled_licensed_users=disabled, guest_users=guests, stale_guests=stale_guests,
        security_defaults=security_defaults, conditional_access=conditional_access,
        user_consent=user_consent, posture=posture,
    )


def _write_scenario(result: AssessmentResult, prefix: str) -> None:
    (_SAMPLES / f"{prefix}_results.json").write_text(
        json.dumps(json.loads(result.model_dump_json()), indent=2, default=str), encoding="utf-8")
    write_markdown(result, _SAMPLES / f"{prefix}_report.md")
    write_pdf(result, _SAMPLES / f"{prefix}_report.pdf")


def main() -> None:
    _SAMPLES.mkdir(parents=True, exist_ok=True)

    premium = _synthetic_result()
    _write_scenario(premium, "sample_assessment")
    no_premium = _no_premium_result()
    _write_scenario(no_premium, "sample_no_premium")

    print(f"Wrote synthetic samples to {_SAMPLES}/")
    print(f"  premium tenant     -> grade {premium.posture.grade} "
          f"({premium.posture.score_pct:.0f}%, {len(premium.posture.controls) - len(premium.posture.skipped_controls)} evaluated)")
    print(f"  no-premium tenant  -> grade {no_premium.posture.grade} "
          f"({no_premium.posture.score_pct:.0f}%, {len(no_premium.posture.controls) - len(no_premium.posture.skipped_controls)} evaluated)")


if __name__ == "__main__":
    main()
