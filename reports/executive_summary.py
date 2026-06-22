from __future__ import annotations
from models.findings import (
    LicenseWasteFinding, DormantUsersFinding, DisabledLicensedFinding,
    GlobalAdminsFinding, MFACoverageFinding, FindingStatus,
)
from models.readiness import InsuranceReadiness

assessment_version = "1.0.0"

_FOOTER = "Generated locally. No data sent to Cloud Locksmith. Assessment only. Not a remediation tool."
_ESTIMATE_DISCLAIMER = (
    "This simplified estimate is based on a limited set of Microsoft 365 controls "
    "and is not an underwriting decision."
)


def print_summary(
    license_waste: LicenseWasteFinding,
    dormant: DormantUsersFinding,
    disabled: DisabledLicensedFinding,
    admins: GlobalAdminsFinding,
    mfa: MFACoverageFinding,
    readiness: InsuranceReadiness,
) -> None:
    w = 62
    print("\n" + "=" * w)
    print("  Cloud Locksmith — Microsoft 365 Assessment")
    print(f"  Assessment Version: {assessment_version}")
    print("=" * w)

    print("\n  LICENSE WASTE")
    if license_waste.status == FindingStatus.SUCCESS:
        print(f"    Unassigned licenses : {license_waste.unassigned_units}")
        print(f"    Est. annual waste   : ${license_waste.estimated_annual_waste_usd:,.2f}")
    else:
        print(f"    Status  : {license_waste.status.value}")
        if license_waste.skipped_reason:
            print(f"    Reason  : {license_waste.skipped_reason}")

    print("\n  SECURITY FINDINGS")
    _row("Global Admins", admins.status,
         f"{admins.count} admins ({admins.risk_level} risk)" if admins.status == FindingStatus.SUCCESS else admins.skipped_reason)
    _row("MFA Coverage (Privileged)", mfa.status,
         f"{mfa.coverage_pct:.0f}% ({mfa.mfa_registered_count}/{mfa.privileged_user_count})" if mfa.status == FindingStatus.SUCCESS else mfa.skipped_reason)
    _row("Dormant Licensed Users", dormant.status,
         f"{dormant.total_count} users" if dormant.status == FindingStatus.SUCCESS else dormant.skipped_reason)
    _row("Disabled Licensed Users", disabled.status,
         f"{disabled.total_count} users" if disabled.status == FindingStatus.SUCCESS else disabled.skipped_reason)

    evaluated = len(readiness.controls) - len(readiness.skipped_controls)
    print(f"\n  INSURANCE READINESS ESTIMATE: {readiness.tier.upper()}")
    print(f"    Score: {readiness.total_score}/{readiness.max_possible_score} ({readiness.score_pct:.0f}%) — {evaluated} of {len(readiness.controls)} controls evaluated")
    if readiness.skipped_controls:
        print(f"    Skipped: {', '.join(readiness.skipped_controls)}")
    print()
    for ctrl in readiness.controls:
        sym = "✓" if ctrl.status == "PASS" else ("⚠" if ctrl.status == "WARNING" else ("–" if ctrl.status == "SKIPPED" else "✗"))
        print(f"    {sym} {ctrl.name:<32} {ctrl.status:<8} {ctrl.detail}")
    print(f"\n    {_ESTIMATE_DISCLAIMER}")

    print(f"\n  {'-' * (w - 2)}")
    print(f"  {_FOOTER}")
    print("=" * w + "\n")


def _row(name: str, status: FindingStatus, detail: str | None) -> None:
    sym = "✓" if status == FindingStatus.SUCCESS else ("⚠" if status == FindingStatus.SKIPPED else "✗")
    print(f"    {sym} {name}: {detail or status.value}")
