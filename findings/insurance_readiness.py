from __future__ import annotations
from models.findings import (
    MFACoverageFinding, GlobalAdminsFinding,
    DormantUsersFinding, DisabledLicensedFinding, FindingStatus,
)
from models.readiness import ControlResult, InsuranceReadiness


def _mfa_control(f: MFACoverageFinding) -> ControlResult:
    if f.status != FindingStatus.SUCCESS:
        return ControlResult(name="MFA Coverage", status="SKIPPED",
                             detail=f.skipped_reason or "Data unavailable.", points=0)
    pct = f.coverage_pct
    if pct >= 95:
        return ControlResult(name="MFA Coverage", status="PASS",
                             detail=f"{pct:.0f}% of privileged users have MFA registered", points=2)
    if pct >= 80:
        return ControlResult(name="MFA Coverage", status="WARNING",
                             detail=f"{pct:.0f}% MFA coverage (threshold: ≥95% PASS)", points=1)
    return ControlResult(name="MFA Coverage", status="FAIL",
                         detail=f"{pct:.0f}% MFA coverage (threshold: ≥80% WARNING)", points=0)


def _admin_control(f: GlobalAdminsFinding) -> ControlResult:
    if f.status != FindingStatus.SUCCESS:
        return ControlResult(name="Global Admin Count", status="SKIPPED",
                             detail=f.skipped_reason or "Data unavailable.", points=0)
    c = f.count
    if c <= 3:
        return ControlResult(name="Global Admin Count", status="PASS",
                             detail=f"{c} Global Admin(s) (≤3 is good)", points=2)
    if c <= 5:
        return ControlResult(name="Global Admin Count", status="WARNING",
                             detail=f"{c} Global Admins (4–5 is moderate risk)", points=1)
    return ControlResult(name="Global Admin Count", status="FAIL",
                         detail=f"{c} Global Admins (≥6 is high risk)", points=0)


def _dormant_control(f: DormantUsersFinding) -> ControlResult:
    if f.status != FindingStatus.SUCCESS:
        return ControlResult(name="Dormant Licensed Users", status="SKIPPED",
                             detail=f.skipped_reason or "Data unavailable.", points=0)
    c = f.total_count
    if c == 0:
        return ControlResult(name="Dormant Licensed Users", status="PASS",
                             detail="No dormant licensed users", points=2)
    if c <= 5:
        return ControlResult(name="Dormant Licensed Users", status="WARNING",
                             detail=f"{c} dormant licensed user(s)", points=1)
    return ControlResult(name="Dormant Licensed Users", status="FAIL",
                         detail=f"{c} dormant licensed users (>5 is high risk)", points=0)


def _disabled_control(f: DisabledLicensedFinding) -> ControlResult:
    if f.status != FindingStatus.SUCCESS:
        return ControlResult(name="Disabled Licensed Users", status="SKIPPED",
                             detail=f.skipped_reason or "Data unavailable.", points=0)
    c = f.total_count
    if c == 0:
        return ControlResult(name="Disabled Licensed Users", status="PASS",
                             detail="No disabled licensed users", points=2)
    if c <= 3:
        return ControlResult(name="Disabled Licensed Users", status="WARNING",
                             detail=f"{c} disabled licensed user(s)", points=1)
    return ControlResult(name="Disabled Licensed Users", status="FAIL",
                         detail=f"{c} disabled licensed users (>3 is high risk)", points=0)


def _tier(score_pct: float) -> str:
    if score_pct >= 90:
        return "Strong"
    if score_pct >= 70:
        return "Good"
    if score_pct >= 40:
        return "Fair"
    return "Poor"


def evaluate_readiness(
    mfa: MFACoverageFinding,
    admins: GlobalAdminsFinding,
    dormant: DormantUsersFinding,
    disabled: DisabledLicensedFinding,
) -> InsuranceReadiness:
    controls = [
        _mfa_control(mfa),
        _admin_control(admins),
        _dormant_control(dormant),
        _disabled_control(disabled),
    ]
    evaluated = [c for c in controls if c.status != "SKIPPED"]
    skipped_names = [c.name for c in controls if c.status == "SKIPPED"]
    total = sum(c.points for c in controls)
    max_pts = len(evaluated) * 2
    pct = round(total / max_pts * 100, 1) if max_pts > 0 else 0.0
    return InsuranceReadiness(
        controls=controls,
        total_score=total,
        max_possible_score=max_pts,
        score_pct=pct,
        skipped_controls=skipped_names,
        tier=_tier(pct),
    )
