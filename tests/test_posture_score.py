"""Tests for the Identity Security Posture Score engine (findings/posture_score.py)."""
from models.findings import (
    FindingStatus, MFACoverageFinding, GlobalAdminsFinding,
    DormantUsersFinding, TenantMFAFinding, SecurityDefaultsFinding,
    ConditionalAccessFinding, UserConsentFinding, StaleGuestsFinding,
)
from findings.posture_score import evaluate_posture

_S = FindingStatus.SUCCESS
_SK = FindingStatus.SKIPPED


def _mfa(pct: float) -> MFACoverageFinding:
    return MFACoverageFinding(status=_S, coverage_pct=pct, privileged_user_count=5,
                              mfa_registered_count=int(5 * pct / 100))


def _tmfa(pct: float) -> TenantMFAFinding:
    return TenantMFAFinding(status=_S, coverage_pct=pct, total_users=100,
                            mfa_registered_count=int(pct))


def _admins(count: int) -> GlobalAdminsFinding:
    risk = "Good" if count <= 3 else "Moderate" if count <= 5 else "High"
    return GlobalAdminsFinding(status=_S, count=count, risk_level=risk)


def _dormant(count: int) -> DormantUsersFinding:
    return DormantUsersFinding(status=_S, total_count=count)


def _sd(enabled: bool) -> SecurityDefaultsFinding:
    return SecurityDefaultsFinding(status=_S, enabled=enabled)


def _ca(enabled_count: int, total: int | None = None) -> ConditionalAccessFinding:
    return ConditionalAccessFinding(status=_S, enabled_count=enabled_count,
                                    policy_count=total if total is not None else enabled_count)


def _consent(users_can_consent: bool) -> UserConsentFinding:
    return UserConsentFinding(status=_S, users_can_consent=users_can_consent, detail="x")


def _stale(count: int) -> StaleGuestsFinding:
    return StaleGuestsFinding(status=_S, total_count=count)


# Number of scored controls (cost/hygiene facts are NOT scored).
SCORED_CONTROLS = 7


def _all_pass_with(**overrides):
    args = dict(
        mfa=_mfa(100), admins=_admins(2), dormant=_dormant(0), tenant_mfa=_tmfa(100),
        security_defaults=_sd(True), conditional_access=_ca(0),
        user_consent=_consent(False), stale_guests=_stale(0),
    )
    args.update(overrides)
    return evaluate_posture(
        args["mfa"], args["admins"], args["dormant"], args["tenant_mfa"],
        args["security_defaults"], args["conditional_access"], args["user_consent"],
        args["stale_guests"],
    )


def test_all_pass_is_strong():
    r = _all_pass_with()
    assert r.grade == "Strong"
    assert r.score_pct == 100.0
    assert r.grade_cap_reason is None
    assert r.max_possible_score == SCORED_CONTROLS * 2
    assert len(r.controls) == SCORED_CONTROLS


def test_all_fail_is_weak():
    r = _all_pass_with(
        mfa=_mfa(50), admins=_admins(7), dormant=_dormant(10), tenant_mfa=_tmfa(40),
        security_defaults=_sd(False), conditional_access=_ca(0, total=0),
        user_consent=_consent(True), stale_guests=_stale(10),
    )
    assert r.grade == "Weak"
    assert r.total_score <= 2  # only the user-consent WARNING earns a point
    assert r.score_pct < 40


def test_cost_hygiene_facts_are_not_scored():
    # No control named for disabled/unassigned-licenses/guest-inventory exists.
    names = {c.name for c in _all_pass_with().controls}
    assert "Disabled Licensed Users" not in names
    assert "Guest Accounts" not in names
    assert "Privileged Role Holders" not in names


def test_baseline_enforcement_pass_via_conditional_access():
    r = _all_pass_with(security_defaults=_sd(False), conditional_access=_ca(1, total=1))
    baseline = next(c for c in r.controls if c.name == "Baseline Access Enforcement")
    assert baseline.status == "PASS"


def test_baseline_enforcement_fails_when_off_and_no_ca():
    r = _all_pass_with(security_defaults=_sd(False), conditional_access=_ca(0, total=0))
    baseline = next(c for c in r.controls if c.name == "Baseline Access Enforcement")
    assert baseline.status == "FAIL"


def test_baseline_warns_when_sd_off_and_ca_unreadable():
    r = _all_pass_with(
        security_defaults=_sd(False),
        conditional_access=ConditionalAccessFinding(status=_SK, skipped_reason="no P1/P2"),
    )
    baseline = next(c for c in r.controls if c.name == "Baseline Access Enforcement")
    assert baseline.status == "WARNING"


def test_user_consent_warns_when_users_can_consent():
    r = _all_pass_with(user_consent=_consent(True))
    uc = next(c for c in r.controls if c.name == "User App Consent")
    assert uc.status == "WARNING"


def test_skipped_control_excluded_from_max():
    r = _all_pass_with(stale_guests=StaleGuestsFinding(status=_SK, skipped_reason="no premium"))
    assert "Stale Guest Access" in r.skipped_controls
    assert r.max_possible_score == (SCORED_CONTROLS - 1) * 2  # 12


def test_no_premium_tenant_is_not_punished():
    # A tenant without P1/P2 skips the license-dependent controls; the remaining
    # readable controls all PASS, so the score is not dragged down by SKIPs.
    r = _all_pass_with(
        mfa=MFACoverageFinding(status=_SK, skipped_reason="P1/P2 required"),
        tenant_mfa=TenantMFAFinding(status=_SK, skipped_reason="P1/P2 required"),
        conditional_access=ConditionalAccessFinding(status=_SK, skipped_reason="P1/P2 required"),
        stale_guests=StaleGuestsFinding(status=_SK, skipped_reason="P1/P2 required"),
    )
    # Evaluated: admins, baseline (via SD), user consent, dormant → all PASS.
    assert r.score_pct == 100.0
    # But a required control (Privileged MFA) was skipped → grade capped at Good.
    assert r.grade == "Good"
    assert r.grade_cap_reason is not None


def test_grade_capped_at_good_when_privileged_mfa_skipped():
    r = _all_pass_with(mfa=MFACoverageFinding(status=_SK, skipped_reason="consent"))
    assert r.grade == "Good"
    assert "Privileged MFA Coverage" in r.grade_cap_reason


def test_grade_capped_at_fair_when_both_required_skipped():
    r = _all_pass_with(
        mfa=MFACoverageFinding(status=_SK, skipped_reason="consent"),
        admins=GlobalAdminsFinding(status=_SK, skipped_reason="no role data"),
    )
    assert r.grade == "Fair"


def test_all_skipped_scores_zero_not_pass():
    # If nothing can be evaluated, the score is 0% — never a silent PASS.
    r = evaluate_posture(
        MFACoverageFinding(status=_SK, skipped_reason="x"),
        GlobalAdminsFinding(status=_SK, skipped_reason="x"),
        DormantUsersFinding(status=_SK, skipped_reason="x"),
        TenantMFAFinding(status=_SK, skipped_reason="x"),
        SecurityDefaultsFinding(status=_SK, skipped_reason="x"),
        ConditionalAccessFinding(status=_SK, skipped_reason="x"),
        UserConsentFinding(status=_SK, skipped_reason="x"),
        StaleGuestsFinding(status=_SK, skipped_reason="x"),
    )
    assert r.max_possible_score == 0
    assert r.score_pct == 0.0
    assert r.grade == "Weak"


def test_tenant_mfa_thresholds():
    assert _all_pass_with(tenant_mfa=_tmfa(90)).controls[2].status == "PASS"
    assert _all_pass_with(tenant_mfa=_tmfa(75)).controls[2].status == "WARNING"
    assert _all_pass_with(tenant_mfa=_tmfa(50)).controls[2].status == "FAIL"
