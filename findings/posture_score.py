from __future__ import annotations
from models.findings import (
    MFACoverageFinding, GlobalAdminsFinding, DormantUsersFinding,
    TenantMFAFinding, SecurityDefaultsFinding, ConditionalAccessFinding,
    UserConsentFinding, StaleGuestsFinding, FindingStatus,
)
from models.posture import ControlResult, PostureScore, GRADE_BANDS

# The score answers a deliberately narrow question:
#   "Based on the Microsoft 365 identity/access controls this tool was able to
#    evaluate, how does the observed posture look?"
# Only genuine security signals are scored. Cost/hygiene facts (unassigned
# licenses, disabled-but-licensed accounts, guest *inventory*, privileged-role
# *inventory*) are reported but never move the score — a fact is not a failure.

# Controls that must be evaluated for the score to reach the top grades. If a
# required control is skipped, the grade is capped (see _apply_grade_cap).
_REQUIRED_CONTROLS = {"Privileged MFA Coverage", "Global Admin Count"}
_GRADE_ORDER = ["Weak", "Fair", "Good", "Strong"]

_SUCCESS = FindingStatus.SUCCESS


def _skipped(name: str, reason: str | None) -> ControlResult:
    return ControlResult(name=name, status="SKIPPED", detail=reason or "Data unavailable.", points=0)


def _priv_mfa(f: MFACoverageFinding) -> ControlResult:
    name = "Privileged MFA Coverage"
    if f.status != _SUCCESS:
        return _skipped(name, f.skipped_reason)
    pct = f.coverage_pct
    if pct >= 95:
        return ControlResult(name=name, status="PASS", points=2,
                             detail=f"{pct:.0f}% of privileged users have MFA registered")
    if pct >= 80:
        return ControlResult(name=name, status="WARNING", points=1,
                             detail=f"{pct:.0f}% privileged MFA coverage (≥95% to PASS)")
    return ControlResult(name=name, status="FAIL", points=0,
                         detail=f"{pct:.0f}% privileged MFA coverage (≥80% to WARNING)")


def _tenant_mfa(f: TenantMFAFinding) -> ControlResult:
    name = "Tenant MFA Coverage"
    if f.status != _SUCCESS:
        return _skipped(name, f.skipped_reason)
    pct = f.coverage_pct
    if pct >= 90:
        return ControlResult(name=name, status="PASS", points=2,
                             detail=f"{pct:.0f}% of users have MFA registered")
    if pct >= 70:
        return ControlResult(name=name, status="WARNING", points=1,
                             detail=f"{pct:.0f}% tenant MFA coverage (≥90% to PASS)")
    return ControlResult(name=name, status="FAIL", points=0,
                         detail=f"{pct:.0f}% tenant MFA coverage (≥70% to WARNING)")


def _admins(f: GlobalAdminsFinding) -> ControlResult:
    name = "Global Admin Count"
    if f.status != _SUCCESS:
        return _skipped(name, f.skipped_reason)
    c = f.count
    if c <= 3:
        return ControlResult(name=name, status="PASS", points=2, detail=f"{c} Global Admin(s) (≤3 recommended)")
    if c <= 5:
        return ControlResult(name=name, status="WARNING", points=1, detail=f"{c} Global Admins (4–5; consider reducing)")
    return ControlResult(name=name, status="FAIL", points=0, detail=f"{c} Global Admins (≥6; minimize standing access)")


def _dormant(f: DormantUsersFinding) -> ControlResult:
    name = "Dormant Enabled Accounts"
    if f.status != _SUCCESS:
        return _skipped(name, f.skipped_reason)
    c = f.total_count
    if c == 0:
        return ControlResult(name=name, status="PASS", points=2, detail="No dormant enabled licensed accounts")
    if c <= 5:
        return ControlResult(name=name, status="WARNING", points=1, detail=f"{c} dormant enabled account(s) — review")
    return ControlResult(name=name, status="FAIL", points=0, detail=f"{c} dormant enabled accounts — unused sign-in surface")


def _baseline_enforcement(sd: SecurityDefaultsFinding, ca: ConditionalAccessFinding) -> ControlResult:
    """Security Defaults OR at least one enabled Conditional Access policy."""
    name = "Baseline Access Enforcement"
    sd_ok = sd.status == _SUCCESS
    ca_ok = ca.status == _SUCCESS
    if not sd_ok and not ca_ok:
        return _skipped(name, sd.skipped_reason or ca.skipped_reason)
    if sd_ok and sd.enabled:
        return ControlResult(name=name, status="PASS", points=2, detail="Security Defaults enabled")
    if ca_ok and ca.enabled_count > 0:
        return ControlResult(name=name, status="PASS", points=2,
                             detail=f"{ca.enabled_count} enabled Conditional Access policy(ies)")
    if ca_ok:  # CA readable and confirms zero enabled policies
        return ControlResult(name=name, status="FAIL", points=0,
                             detail="Security Defaults off and no enabled Conditional Access policies")
    # SD readable and off, but CA not readable → cannot fully confirm
    return ControlResult(name=name, status="WARNING", points=1,
                         detail="Security Defaults off; Conditional Access could not be confirmed")


def _user_consent(f: UserConsentFinding) -> ControlResult:
    name = "User App Consent"
    if f.status != _SUCCESS:
        return _skipped(name, f.skipped_reason)
    if f.users_can_consent:
        return ControlResult(name=name, status="WARNING", points=1,
                             detail="Users can consent to third-party apps (restrict to admins)")
    return ControlResult(name=name, status="PASS", points=2,
                         detail="User app consent restricted to administrators")


def _stale_guests(f: StaleGuestsFinding) -> ControlResult:
    name = "Stale Guest Access"
    if f.status != _SUCCESS:
        return _skipped(name, f.skipped_reason)
    c = f.total_count
    if c == 0:
        return ControlResult(name=name, status="PASS", points=2, detail="No stale guest accounts")
    if c <= 5:
        return ControlResult(name=name, status="WARNING", points=1, detail=f"{c} stale guest account(s) — review access")
    return ControlResult(name=name, status="FAIL", points=0, detail=f"{c} stale guest accounts — external access to review")


def _grade(score_pct: float) -> str:
    for threshold, label in GRADE_BANDS:
        if score_pct >= threshold:
            return label
    return "Weak"


def _apply_grade_cap(grade: str, skipped_names: list[str]) -> tuple[str, str | None]:
    skipped_required = [n for n in skipped_names if n in _REQUIRED_CONTROLS]
    if not skipped_required:
        return grade, None
    cap = "Good" if len(skipped_required) == 1 else "Fair"
    if _GRADE_ORDER.index(grade) > _GRADE_ORDER.index(cap):
        names = ", ".join(skipped_required)
        return cap, f"Grade capped at {cap} because {names} could not be evaluated."
    return grade, None


def evaluate_posture(
    mfa: MFACoverageFinding,
    admins: GlobalAdminsFinding,
    dormant: DormantUsersFinding,
    tenant_mfa: TenantMFAFinding,
    security_defaults: SecurityDefaultsFinding,
    conditional_access: ConditionalAccessFinding,
    user_consent: UserConsentFinding,
    stale_guests: StaleGuestsFinding,
) -> PostureScore:
    controls = [
        _priv_mfa(mfa),
        _admins(admins),
        _tenant_mfa(tenant_mfa),
        _baseline_enforcement(security_defaults, conditional_access),
        _user_consent(user_consent),
        _dormant(dormant),
        _stale_guests(stale_guests),
    ]
    evaluated = [c for c in controls if c.status != "SKIPPED"]
    skipped_names = [c.name for c in controls if c.status == "SKIPPED"]
    total = sum(c.points for c in controls)
    max_pts = len(evaluated) * 2
    pct = round(total / max_pts * 100, 1) if max_pts > 0 else 0.0
    raw_grade = _grade(pct)
    grade, cap_reason = _apply_grade_cap(raw_grade, skipped_names)
    return PostureScore(
        controls=controls,
        total_score=total,
        max_possible_score=max_pts,
        score_pct=pct,
        skipped_controls=skipped_names,
        grade=grade,
        grade_cap_reason=cap_reason,
    )
