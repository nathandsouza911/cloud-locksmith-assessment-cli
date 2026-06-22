from __future__ import annotations
import pathlib
from datetime import datetime, timezone
from models.findings import (
    LicenseWasteFinding, DormantUsersFinding, DisabledLicensedFinding,
    GlobalAdminsFinding, MFACoverageFinding, FindingStatus,
)
from models.readiness import InsuranceReadiness

ASSESSMENT_VERSION = "1.0.0"
_FOOTER = "*Generated locally. No data sent to Cloud Locksmith. Assessment only. Not a remediation tool.*"
_ESTIMATE_DISCLAIMER = (
    "*This simplified estimate is based on a limited set of Microsoft 365 controls "
    "and is not an underwriting decision.*"
)


def write_markdown(
    license_waste: LicenseWasteFinding,
    dormant: DormantUsersFinding,
    disabled: DisabledLicensedFinding,
    admins: GlobalAdminsFinding,
    mfa: MFACoverageFinding,
    readiness: InsuranceReadiness,
    output_path: pathlib.Path,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    lines: list[str] = []

    lines += ["# Microsoft 365 Security Assessment\n", "## Executive Summary\n"]
    if license_waste.status == FindingStatus.SUCCESS:
        lines += [
            f"- **Estimated Annual License Waste:** ${license_waste.estimated_annual_waste_usd:,.2f}",
            f"- **Unassigned Licenses:** {license_waste.unassigned_units}",
        ]
    lines += [f"- **Insurance Readiness Estimate:** {readiness.tier}", ""]

    lines += ["## License Waste Analysis\n"]
    if license_waste.status == FindingStatus.SUCCESS:
        lines += [
            "| Metric | Value |", "|---|---|",
            f"| Active Units | {license_waste.active_units} |",
            f"| Consumed Units | {license_waste.consumed_units} |",
            f"| Unassigned Units | {license_waste.unassigned_units} |",
            f"| Estimated Annual Waste | ${license_waste.estimated_annual_waste_usd:,.2f} |", "",
        ]
    else:
        lines += [f"**Status:** {license_waste.status.value}",
                  f"**Reason:** {license_waste.skipped_reason}", ""]

    lines += ["## Security Findings\n", "### Global Administrators\n"]
    if admins.status == FindingStatus.SUCCESS:
        lines += [f"- Count: {admins.count}", f"- Risk Level: {admins.risk_level}", ""]
    else:
        lines += [f"**Status:** {admins.status.value}", f"**Reason:** {admins.skipped_reason}", ""]

    lines += ["### MFA Coverage (Privileged Users)\n"]
    if mfa.status == FindingStatus.SUCCESS:
        lines += [
            f"- Privileged Users: {mfa.privileged_user_count}",
            f"- MFA Registered: {mfa.mfa_registered_count}",
            f"- Coverage: {mfa.coverage_pct:.1f}%", "",
        ]
    else:
        lines += [f"**Status:** {mfa.status.value}", f"**Reason:** {mfa.skipped_reason}", ""]

    lines += ["### Dormant Licensed Users (90+ days inactive)\n"]
    if dormant.status == FindingStatus.SUCCESS:
        lines.append(f"- Total: {dormant.total_count}")
        if dormant.examples:
            lines.append("- Examples (first 3):")
            for ex in dormant.examples:
                lines.append(f"  - {ex.display_name} ({ex.user_principal_name})")
        lines.append("")
    else:
        lines += [f"**Status:** {dormant.status.value}", f"**Reason:** {dormant.skipped_reason}", ""]

    lines += ["### Disabled Licensed Users\n"]
    if disabled.status == FindingStatus.SUCCESS:
        lines.append(f"- Total: {disabled.total_count}")
        if disabled.examples:
            lines.append("- Examples (first 3):")
            for ex in disabled.examples:
                lines.append(f"  - {ex.display_name} ({ex.user_principal_name})")
        lines.append("")
    else:
        lines += [f"**Status:** {disabled.status.value}", f"**Reason:** {disabled.skipped_reason}", ""]

    lines += ["## Insurance Readiness Estimate\n"]
    evaluated = len(readiness.controls) - len(readiness.skipped_controls)
    lines.append(
        f"**Tier: {readiness.tier}** — Score: {readiness.total_score}/{readiness.max_possible_score} "
        f"({readiness.score_pct:.0f}%) — {evaluated} of {len(readiness.controls)} controls evaluated\n"
    )
    if readiness.skipped_controls:
        lines.append(f"> ⚠ Skipped: {', '.join(readiness.skipped_controls)}\n")
    lines += ["| Control | Status | Detail |", "|---|---|---|"]
    for ctrl in readiness.controls:
        lines.append(f"| {ctrl.name} | {ctrl.status} | {ctrl.detail} |")
    lines += ["", _ESTIMATE_DISCLAIMER, ""]

    lines += [
        "## Assessment Metadata\n",
        "| Field | Value |", "|---|---|",
        f"| Generated | {now} |",
        f"| Assessment Version | {ASSESSMENT_VERSION} |",
        "| Authentication | Microsoft Device Code Flow |",
        "| Permissions | Read-only delegated permissions |",
        "| Data Handling | No assessment data was transmitted to Cloud Locksmith. |",
        "| Token Handling | Authentication tokens were discarded after assessment completion. |",
        "", "---", _FOOTER,
    ]

    output_path = pathlib.Path(output_path)
    output_path.write_text("\n".join(lines), encoding="utf-8")
