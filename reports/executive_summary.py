from __future__ import annotations
import sys
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich import box as rich_box
from models.findings import FindingStatus
from models.assessment import AssessmentResult

_BRAND = "steel_blue1"
_GRADE_COLORS = {"Strong": "green", "Good": "green", "Fair": "yellow", "Weak": "red"}
_STATUS_STYLES = {
    "PASS":    ("✓ PASS",    "bold green"),
    "WARNING": ("⚠ WARNING", "bold yellow"),
    "FAIL":    ("✗ FAIL",    "bold red"),
    "SKIPPED": ("– SKIPPED", "dim"),
}

POSTURE_DISCLAIMER = (
    "Identity Security Posture Score reflects only the Microsoft 365 identity/access "
    "controls this tool could evaluate. It is not a measure of overall cybersecurity "
    "maturity, breach likelihood, compliance, or insurance eligibility."
)
_FOOTER = (
    "Generated locally. No data sent to Cloud Locksmith. "
    "Point-in-time assessment only — no changes were made to your tenant."
)


def print_summary(result: AssessmentResult) -> None:
    c = _console()
    _header(c, result)
    _posture(c, result)
    _identity(c, result)
    _external(c, result)
    _policy(c, result)
    _hygiene(c, result)
    _license(c, result)
    c.rule(style="dim")
    c.print(f"  [dim]{_FOOTER}[/dim]")
    c.print()


def _header(c: Console, result: AssessmentResult) -> None:
    header = Text(justify="center")
    header.append("CLOUD LOCKSMITH\n", style="bold bright_white")
    header.append("Microsoft 365 Assessment CLI\n", style="white")
    header.append("\n")
    header.append("Local  •  Read-Only  •  No Data Leaves Your Tenant\n", style="dim white")
    header.append(f"Schema Version: {result.schema_version}", style="dim white")
    c.print()
    c.print(Panel(header, border_style=_BRAND, padding=(1, 4)))
    c.print()


def _posture(c: Console, result: AssessmentResult) -> None:
    p = result.posture
    evaluated = len(p.controls) - len(p.skipped_controls)
    grade_color = _GRADE_COLORS.get(p.grade, "white")
    c.print(Rule("[bold]IDENTITY SECURITY POSTURE SCORE[/bold]", style=_BRAND))
    c.print()
    c.print(
        f"  Grade: [bold {grade_color}]{p.grade.upper()}[/bold {grade_color}]"
        f"  —  Score: {p.total_score}/{p.max_possible_score}"
        f" ({p.score_pct:.0f}%)"
        f"  —  {evaluated} of {len(p.controls)} controls evaluated"
    )
    if p.skipped_controls:
        c.print(f"  [dim]Skipped: {', '.join(p.skipped_controls)}[/dim]")
    if p.grade_cap_reason:
        c.print(f"  [yellow]⚠[/yellow]  {p.grade_cap_reason}")
    c.print()
    tbl = Table(box=rich_box.SIMPLE, show_header=True,
                header_style=f"bold {_BRAND}", padding=(0, 1), show_edge=False)
    tbl.add_column("Control", min_width=26)
    tbl.add_column("Status", min_width=10)
    tbl.add_column("Detail", style="dim", overflow="fold")
    for ctrl in p.controls:
        tbl.add_row(ctrl.name, _status_text(ctrl.status), ctrl.detail)
    c.print(tbl)
    c.print(f"  [dim]{POSTURE_DISCLAIMER}[/dim]")
    c.print()


def _identity(c: Console, result: AssessmentResult) -> None:
    c.print(Rule("[bold]IDENTITY & PRIVILEGED ACCESS[/bold]", style=_BRAND))
    c.print()
    admins, pmfa, tmfa, roles = (
        result.global_admins, result.privileged_mfa, result.tenant_mfa, result.privileged_roles,
    )
    _row(c, "Global Admins", admins.status,
         f"{admins.count} admins ({admins.risk_level} risk)" if admins.status == FindingStatus.SUCCESS else admins.skipped_reason)
    _row(c, "Privileged MFA Coverage", pmfa.status,
         f"{pmfa.coverage_pct:.0f}% ({pmfa.mfa_registered_count}/{pmfa.privileged_user_count})" if pmfa.status == FindingStatus.SUCCESS else pmfa.skipped_reason)
    _row(c, "Tenant-wide MFA Coverage", tmfa.status,
         f"{tmfa.coverage_pct:.0f}% ({tmfa.mfa_registered_count}/{tmfa.total_users})" if tmfa.status == FindingStatus.SUCCESS else tmfa.skipped_reason)
    if roles.status == FindingStatus.SUCCESS:
        top = ", ".join(f"{r.role_name.split()[0]}:{r.member_count}" for r in roles.roles[:4])
        _row(c, "Privileged Role Holders", roles.status,
             f"{roles.distinct_privileged_users} distinct users across {len(roles.roles)} roles"
             + (f" ({top}…)" if top else ""))
    else:
        _row(c, "Privileged Role Holders", roles.status, roles.skipped_reason)
    c.print()


def _external(c: Console, result: AssessmentResult) -> None:
    c.print(Rule("[bold]EXTERNAL / GUEST COLLABORATION[/bold]", style=_BRAND))
    c.print()
    guests, stale = result.guest_users, result.stale_guests
    _row(c, "Guest Accounts", guests.status,
         f"{guests.total_count} guest user(s)" if guests.status == FindingStatus.SUCCESS else guests.skipped_reason)
    _row(c, "Stale Guests (90d+)", stale.status,
         f"{stale.total_count} stale guest(s)" if stale.status == FindingStatus.SUCCESS else stale.skipped_reason)
    c.print()


def _policy(c: Console, result: AssessmentResult) -> None:
    c.print(Rule("[bold]TENANT POLICY[/bold]", style=_BRAND))
    c.print()
    sd, ca, uc = result.security_defaults, result.conditional_access, result.user_consent
    if sd.status == FindingStatus.SUCCESS:
        _row(c, "Security Defaults", sd.status, "Enabled" if sd.enabled else "Disabled")
    else:
        _row(c, "Security Defaults", sd.status, sd.skipped_reason)
    if ca.status == FindingStatus.SUCCESS:
        _row(c, "Conditional Access", ca.status,
             f"{ca.enabled_count} enabled / {ca.policy_count} total"
             + (f", {ca.report_only_count} report-only" if ca.report_only_count else ""))
    else:
        _row(c, "Conditional Access", ca.status, ca.skipped_reason)
    if uc.status == FindingStatus.SUCCESS:
        _row(c, "User App Consent", uc.status,
             "Users can consent to apps" if uc.users_can_consent else "Restricted to admins")
    else:
        _row(c, "User App Consent", uc.status, uc.skipped_reason)
    c.print()


def _hygiene(c: Console, result: AssessmentResult) -> None:
    """Cost/cleanup findings — reported, but they do not affect the score."""
    c.print(Rule("[bold]ACCOUNT HYGIENE (COST / CLEANUP)[/bold]", style=_BRAND))
    c.print()
    dormant, disabled = result.dormant_users, result.disabled_licensed_users
    _row(c, "Dormant enabled licensed accounts", dormant.status,
         f"{dormant.total_count} account(s) with no sign-in 90d+ (also scored above)"
         if dormant.status == FindingStatus.SUCCESS else dormant.skipped_reason)
    _row(c, "Disabled but still-licensed accounts", disabled.status,
         f"{disabled.total_count} account(s) — reclaimable license, not a sign-in risk"
         if disabled.status == FindingStatus.SUCCESS else disabled.skipped_reason)
    c.print("  [dim]These are cost/cleanup observations and do not affect the posture score.[/dim]")
    c.print()


def _license(c: Console, result: AssessmentResult) -> None:
    lw = result.license_waste
    c.print(Rule("[bold]LICENSE OPTIMIZATION[/bold]", style=_BRAND))
    c.print()
    if lw.status == FindingStatus.SUCCESS:
        c.print(f"  Potentially reclaimable seats   [bold]{lw.unassigned_units}[/bold]")
        c.print(f"  Est. reclaimable spend          [bold]${lw.estimated_reclaimable_monthly_usd:,.2f}/mo[/bold]"
                f"  ·  [bold]${lw.estimated_reclaimable_annual_usd:,.2f}/yr[/bold]  [dim](estimate)[/dim]")
        if lw.partial_pricing_warning:
            c.print(f"  [yellow]⚠[/yellow]  {lw.partial_pricing_warning}")
        c.print(f"  [dim]Estimates from {lw.pricing_source}. Unassigned seats are potentially "
                f"reclaimable, not proven waste.[/dim]")
    else:
        c.print(f"  [dim]{lw.status.value}[/dim]")
        if lw.skipped_reason:
            c.print(f"  [dim]{lw.skipped_reason}[/dim]")
    c.print()


def _console() -> Console:
    """Create a UTF-8 Console. Falls back gracefully in test / pipe contexts."""
    try:
        file = open(sys.stdout.fileno(), "w", encoding="utf-8", closefd=False)
        return Console(file=file, legacy_windows=False)
    except Exception:
        return Console(legacy_windows=False)


def print_next_steps() -> None:
    c = _console()
    body = (
        "[bold]This assessment is a local, point-in-time snapshot.[/bold]\n\n"
        "The [bold]Cloud Locksmith[/bold] platform is a separate, paid service for teams that\n"
        "need to operate posture over time rather than run it by hand:\n\n"
        "  [dim]•[/dim]  Scheduled posture scanning with alerting\n"
        "  [dim]•[/dim]  Historical posture tracking and evidence history\n"
        "  [dim]•[/dim]  Multi-tenant fleet operations for MSPs\n"
        "  [dim]•[/dim]  Controlled remediation with verification and rollback\n\n"
        "[dim]This CLI stays free and open source. Learn more:[/dim]  [bold]https://cloudlocksmith.co[/bold]"
    )
    c.print(Panel(body, title="[bold]ABOUT CLOUD LOCKSMITH[/bold]", border_style=_BRAND, padding=(1, 2)))
    c.print()


def _status_text(status: str) -> Text:
    label, style = _STATUS_STYLES.get(status, (status, ""))
    return Text(label, style=style)


def _row(c: Console, name: str, status: FindingStatus, detail: str | None) -> None:
    if status == FindingStatus.SUCCESS:
        icon = "[bold green]✓[/bold green]"
    elif status == FindingStatus.SKIPPED:
        icon = "[dim]–[/dim]"
    else:
        icon = "[bold red]✗[/bold red]"
    c.print(f"  {icon}  {name}: {detail or status.value}")
