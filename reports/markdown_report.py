from __future__ import annotations
import pathlib
from models.findings import FindingStatus
from models.assessment import AssessmentResult

_FOOTER = ("*Generated locally. No data sent to Cloud Locksmith. Point-in-time assessment only — "
           "no changes were made to your tenant.*")
POSTURE_DISCLAIMER = (
    "*Identity Security Posture Score reflects only the Microsoft 365 identity/access controls "
    "this tool could evaluate. It is not a measure of overall cybersecurity maturity, breach "
    "likelihood, compliance, or insurance eligibility. See docs/METHODOLOGY.md.*"
)
_SUCCESS = FindingStatus.SUCCESS


def _status_block(status: FindingStatus, reason: str | None) -> list[str]:
    return [f"**Status:** {status.value}", f"**Reason:** {reason or 'Data unavailable.'}", ""]


def write_markdown(result: AssessmentResult, output_path: pathlib.Path) -> None:
    p = result.posture
    lw = result.license_waste
    lines: list[str] = ["# Microsoft 365 Security Assessment\n"]

    # ── Identity Security Posture Score ─────────────────────────────────────
    lines += ["## Identity Security Posture Score\n"]
    evaluated = len(p.controls) - len(p.skipped_controls)
    lines.append(
        f"**Grade: {p.grade}** — Score: {p.total_score}/{p.max_possible_score} "
        f"({p.score_pct:.0f}%) — {evaluated} of {len(p.controls)} controls evaluated\n"
    )
    if p.skipped_controls:
        lines.append(f"> Skipped: {', '.join(p.skipped_controls)}\n")
    if p.grade_cap_reason:
        lines.append(f"> {p.grade_cap_reason}\n")
    lines += ["| Control | Status | Detail |", "|---|---|---|"]
    for ctrl in p.controls:
        lines.append(f"| {ctrl.name} | {ctrl.status} | {ctrl.detail} |")
    lines += ["", POSTURE_DISCLAIMER, ""]

    # ── Identity & privileged access ────────────────────────────────────────
    lines += ["## Identity & Privileged Access\n", "### Global Administrators\n"]
    admins = result.global_admins
    if admins.status == _SUCCESS:
        lines += [f"- Count: {admins.count}", f"- Risk Level: {admins.risk_level}", ""]
    else:
        lines += _status_block(admins.status, admins.skipped_reason)

    lines += ["### Privileged MFA Coverage\n"]
    pmfa = result.privileged_mfa
    if pmfa.status == _SUCCESS:
        lines += [f"- Privileged Users: {pmfa.privileged_user_count}",
                  f"- MFA Registered: {pmfa.mfa_registered_count}",
                  f"- Coverage: {pmfa.coverage_pct:.1f}%", ""]
    else:
        lines += _status_block(pmfa.status, pmfa.skipped_reason)

    lines += ["### Tenant-wide MFA Coverage\n"]
    tmfa = result.tenant_mfa
    if tmfa.status == _SUCCESS:
        lines += [f"- Users Reported: {tmfa.total_users}",
                  f"- MFA Registered: {tmfa.mfa_registered_count}",
                  f"- Coverage: {tmfa.coverage_pct:.1f}%", ""]
    else:
        lines += _status_block(tmfa.status, tmfa.skipped_reason)

    lines += ["### Privileged Role Holders\n"]
    roles = result.privileged_roles
    if roles.status == _SUCCESS:
        lines.append(f"- Distinct privileged users: {roles.distinct_privileged_users}")
        if roles.roles:
            lines += ["", "| Role | Members |", "|---|---|"]
            lines += [f"| {r.role_name} | {r.member_count} |" for r in roles.roles]
        lines.append("")
    else:
        lines += _status_block(roles.status, roles.skipped_reason)

    # ── External / guest ────────────────────────────────────────────────────
    lines += ["## External / Guest Collaboration\n", "### Guest Accounts\n"]
    guests = result.guest_users
    if guests.status == _SUCCESS:
        lines.append(f"- Total guests: {guests.total_count}")
        _append_examples(lines, guests.examples)
    else:
        lines += _status_block(guests.status, guests.skipped_reason)

    lines += ["### Stale Guest Accounts (90+ days inactive)\n"]
    stale = result.stale_guests
    if stale.status == _SUCCESS:
        lines.append(f"- Total stale guests: {stale.total_count}")
        _append_examples(lines, stale.examples)
    else:
        lines += _status_block(stale.status, stale.skipped_reason)

    # ── Tenant policy ───────────────────────────────────────────────────────
    lines += ["## Tenant Policy\n", "### Security Defaults\n"]
    sd = result.security_defaults
    if sd.status == _SUCCESS:
        lines += [f"- Enabled: {'Yes' if sd.enabled else 'No'}", ""]
    else:
        lines += _status_block(sd.status, sd.skipped_reason)

    lines += ["### Conditional Access\n"]
    ca = result.conditional_access
    if ca.status == _SUCCESS:
        lines += [f"- Total policies: {ca.policy_count}",
                  f"- Enabled: {ca.enabled_count}",
                  f"- Report-only: {ca.report_only_count}"]
        if ca.examples:
            lines.append("- Example enabled policies: " + ", ".join(ca.examples))
        lines.append("")
    else:
        lines += _status_block(ca.status, ca.skipped_reason)

    lines += ["### User App Consent\n"]
    uc = result.user_consent
    if uc.status == _SUCCESS:
        lines += [f"- Users can consent to apps: {'Yes' if uc.users_can_consent else 'No'}",
                  f"- {uc.detail}", ""]
    else:
        lines += _status_block(uc.status, uc.skipped_reason)

    # ── Account hygiene (cost / cleanup) ────────────────────────────────────
    lines += [
        "## Account Hygiene (Cost / Cleanup)\n",
        "_These are cost/cleanup observations. Dormant **enabled** accounts are also scored "
        "above as an identity signal; disabled accounts cannot sign in and are reported here "
        "for reclaimable licensing only — they do not affect the posture score._\n",
        "### Dormant Enabled Licensed Accounts (90+ days inactive)\n",
    ]
    dormant = result.dormant_users
    if dormant.status == _SUCCESS:
        lines.append(f"- Total: {dormant.total_count}")
        _append_examples(lines, dormant.examples)
    else:
        lines += _status_block(dormant.status, dormant.skipped_reason)

    lines += ["### Disabled but Still-Licensed Accounts\n"]
    disabled = result.disabled_licensed_users
    if disabled.status == _SUCCESS:
        lines.append(f"- Total: {disabled.total_count} (reclaimable license; not a sign-in risk)")
        _append_examples(lines, disabled.examples)
    else:
        lines += _status_block(disabled.status, disabled.skipped_reason)

    # ── License optimization ────────────────────────────────────────────────
    lines += ["## License Optimization\n"]
    if lw.status == _SUCCESS:
        lines += [
            "| Metric | Value |", "|---|---|",
            f"| Active (paid) units | {lw.active_units} |",
            f"| Consumed units | {lw.consumed_units} |",
            f"| Potentially reclaimable seats | {lw.unassigned_units} |",
            f"| Est. reclaimable spend (monthly) | ${lw.estimated_reclaimable_monthly_usd:,.2f} |",
            f"| Est. reclaimable spend (annual) | ${lw.estimated_reclaimable_annual_usd:,.2f} |",
            f"| Priced reclaimable seats | {lw.priced_unassigned_units} |",
            f"| Unpriced reclaimable seats | {lw.unpriced_unassigned_units} |",
            "",
            f"> Estimates from {lw.pricing_source}. Unassigned seats are *potentially reclaimable*, "
            "not proven waste, and should be reviewed before any change.",
        ]
        if lw.partial_pricing_warning:
            lines += ["", f"> ⚠ {lw.partial_pricing_warning}"]
        if lw.unknown_skus:
            lines += ["", f"> Unpriced SKUs: {', '.join(lw.unknown_skus)}"]
        lines.append("")
    else:
        lines += _status_block(lw.status, lw.skipped_reason)

    # ── Metadata ────────────────────────────────────────────────────────────
    lines += [
        "## Assessment Metadata\n",
        "| Field | Value |", "|---|---|",
        f"| Generated | {result.generated_at} |",
        f"| Schema Version | {result.schema_version} |",
        "| Authentication | Microsoft Device Code Flow |",
        "| Permissions | Read-only delegated |",
        "| Data Handling | No assessment data was transmitted to Cloud Locksmith. |",
        "| Token Handling | Authentication tokens were discarded after assessment completion. |",
        "", "---", _FOOTER,
    ]

    pathlib.Path(output_path).write_text("\n".join(lines), encoding="utf-8")


def _append_examples(lines: list[str], examples: list) -> None:
    if examples:
        lines.append("- Examples (first 3):")
        for ex in examples:
            lines.append(f"  - {ex.display_name} ({ex.user_principal_name})")
    lines.append("")
