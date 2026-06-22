import pytest
from models.findings import (
    FindingStatus, MFACoverageFinding, GlobalAdminsFinding,
    DormantUsersFinding, DisabledLicensedFinding,
)
from findings.insurance_readiness import evaluate_readiness


def _mfa(pct: float) -> MFACoverageFinding:
    return MFACoverageFinding(status=FindingStatus.SUCCESS, coverage_pct=pct,
                              privileged_user_count=5, mfa_registered_count=int(5 * pct / 100))

def _admins(count: int) -> GlobalAdminsFinding:
    risk = "Good" if count <= 3 else "Moderate" if count <= 5 else "High"
    return GlobalAdminsFinding(status=FindingStatus.SUCCESS, count=count, risk_level=risk)

def _dormant(count: int) -> DormantUsersFinding:
    return DormantUsersFinding(status=FindingStatus.SUCCESS, total_count=count)

def _disabled(count: int) -> DisabledLicensedFinding:
    return DisabledLicensedFinding(status=FindingStatus.SUCCESS, total_count=count)

def _skipped_mfa() -> MFACoverageFinding:
    return MFACoverageFinding(status=FindingStatus.SKIPPED,
                              skipped_reason="Credential registration data unavailable.")


def test_all_pass_is_strong():
    r = evaluate_readiness(_mfa(100), _admins(2), _dormant(0), _disabled(0))
    assert r.tier == "Strong"
    assert r.total_score == 8
    assert r.score_pct == 100.0


def test_all_fail_is_poor():
    r = evaluate_readiness(_mfa(50), _admins(7), _dormant(10), _disabled(5))
    assert r.tier == "Poor"
    assert r.total_score == 0
    assert r.score_pct == 0.0


def test_mixed_scoring():
    # MFA 90% → WARNING (1pt), admins 2 → PASS (2pt), dormant 3 → WARNING (1pt), disabled 0 → PASS (2pt)
    # total = 6, max = 8, pct = 75% → Good
    r = evaluate_readiness(_mfa(90), _admins(2), _dormant(3), _disabled(0))
    assert r.tier == "Good"
    assert r.total_score == 6
    assert r.score_pct == 75.0


def test_skipped_mfa_excluded_from_max():
    # MFA SKIPPED (0pt, excluded), admins 2 → PASS (2pt), dormant 0 → PASS (2pt), disabled 0 → PASS (2pt)
    # total = 6, max = 6, pct = 100% → Strong
    r = evaluate_readiness(_skipped_mfa(), _admins(2), _dormant(0), _disabled(0))
    assert r.max_possible_score == 6
    assert r.score_pct == 100.0
    assert r.tier == "Strong"
    assert "MFA Coverage" in r.skipped_controls


def test_all_skipped_is_poor():
    skipped = FindingStatus.SKIPPED
    r = evaluate_readiness(
        MFACoverageFinding(status=skipped, skipped_reason="x"),
        GlobalAdminsFinding(status=skipped, skipped_reason="x"),
        DormantUsersFinding(status=skipped, skipped_reason="x"),
        DisabledLicensedFinding(status=skipped, skipped_reason="x"),
    )
    assert r.tier == "Poor"
    assert r.max_possible_score == 0
    assert r.score_pct == 0.0
    assert len(r.skipped_controls) == 4


def test_mfa_thresholds():
    assert evaluate_readiness(_mfa(95), _admins(2), _dormant(0), _disabled(0)).controls[0].status == "PASS"
    assert evaluate_readiness(_mfa(85), _admins(2), _dormant(0), _disabled(0)).controls[0].status == "WARNING"
    assert evaluate_readiness(_mfa(70), _admins(2), _dormant(0), _disabled(0)).controls[0].status == "FAIL"


def test_admin_thresholds():
    assert evaluate_readiness(_mfa(100), _admins(3), _dormant(0), _disabled(0)).controls[1].status == "PASS"
    assert evaluate_readiness(_mfa(100), _admins(4), _dormant(0), _disabled(0)).controls[1].status == "WARNING"
    assert evaluate_readiness(_mfa(100), _admins(6), _dormant(0), _disabled(0)).controls[1].status == "FAIL"


def test_dormant_thresholds():
    assert evaluate_readiness(_mfa(100), _admins(2), _dormant(0), _disabled(0)).controls[2].status == "PASS"
    assert evaluate_readiness(_mfa(100), _admins(2), _dormant(5), _disabled(0)).controls[2].status == "WARNING"
    assert evaluate_readiness(_mfa(100), _admins(2), _dormant(6), _disabled(0)).controls[2].status == "FAIL"


def test_disabled_thresholds():
    assert evaluate_readiness(_mfa(100), _admins(2), _dormant(0), _disabled(0)).controls[3].status == "PASS"
    assert evaluate_readiness(_mfa(100), _admins(2), _dormant(0), _disabled(3)).controls[3].status == "WARNING"
    assert evaluate_readiness(_mfa(100), _admins(2), _dormant(0), _disabled(4)).controls[3].status == "FAIL"
