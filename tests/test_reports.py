from models.findings import (
    FindingStatus, LicenseWasteFinding, DormantUsersFinding,
    DisabledLicensedFinding, GlobalAdminsFinding, MFACoverageFinding,
    TenantMFAFinding, PrivilegedRolesFinding, RoleMemberSummary,
    GuestUsersFinding, StaleGuestsFinding, SecurityDefaultsFinding,
    ConditionalAccessFinding, UserConsentFinding,
)
from models.posture import PostureScore, ControlResult
from models.assessment import AssessmentResult
from reports.executive_summary import print_summary
from reports.markdown_report import write_markdown
from reports.pdf_report import write_pdf

_S = FindingStatus.SUCCESS


def _posture(grade: str = "Strong", skipped=None, cap=None) -> PostureScore:
    controls = [
        ControlResult(name="Privileged MFA Coverage", status="PASS", detail="100%", points=2),
        ControlResult(name="Global Admin Count", status="PASS", detail="2 admins", points=2),
        ControlResult(name="Tenant MFA Coverage", status="PASS", detail="98%", points=2),
        ControlResult(name="Baseline Access Enforcement", status="PASS", detail="Security Defaults enabled", points=2),
    ]
    return PostureScore(controls=controls, total_score=8, max_possible_score=8,
                        score_pct=100.0, grade=grade,
                        skipped_controls=skipped or [], grade_cap_reason=cap)


def _result(posture=None, license_waste=None, **overrides) -> AssessmentResult:
    base = dict(
        license_waste=license_waste or LicenseWasteFinding(
            status=_S, active_units=100, consumed_units=80, unassigned_units=20,
            estimated_reclaimable_annual_usd=7200.0, estimated_reclaimable_monthly_usd=600.0,
            priced_unassigned_units=20),
        global_admins=GlobalAdminsFinding(status=_S, count=2, risk_level="Good"),
        privileged_mfa=MFACoverageFinding(status=_S, coverage_pct=100.0,
                                          privileged_user_count=2, mfa_registered_count=2),
        tenant_mfa=TenantMFAFinding(status=_S, coverage_pct=98.0, total_users=100,
                                    mfa_registered_count=98),
        privileged_roles=PrivilegedRolesFinding(status=_S, distinct_privileged_users=4,
                                                roles=[RoleMemberSummary(role_name="Global Administrator", member_count=2)]),
        dormant_users=DormantUsersFinding(status=_S, total_count=1),
        disabled_licensed_users=DisabledLicensedFinding(status=_S, total_count=0),
        guest_users=GuestUsersFinding(status=_S, total_count=3),
        stale_guests=StaleGuestsFinding(status=_S, total_count=1),
        security_defaults=SecurityDefaultsFinding(status=_S, enabled=True),
        conditional_access=ConditionalAccessFinding(status=_S, policy_count=4, enabled_count=3),
        user_consent=UserConsentFinding(status=_S, users_can_consent=False, detail="Admin-restricted"),
        posture=posture or _posture(),
    )
    base.update(overrides)
    return AssessmentResult(**base)


def test_print_summary_contains_grade(capsys):
    print_summary(_result())
    out = capsys.readouterr().out
    assert "STRONG" in out
    assert "IDENTITY SECURITY POSTURE SCORE" in out


def test_print_summary_contains_footer(capsys):
    print_summary(_result())
    out = capsys.readouterr().out
    assert "No data sent to Cloud Locksmith" in out


def test_print_summary_scopes_the_claim(capsys):
    print_summary(_result())
    out = capsys.readouterr().out.lower()
    # The disclaimer scopes the score and explicitly disclaims insurance/maturity.
    # (Rich may wrap the disclaimer, so match single, non-splittable tokens.)
    assert "insurance" in out
    assert "identity security posture score" in out


def test_print_summary_skipped_finding(capsys):
    result = _result(
        posture=_posture(grade="Good", skipped=["Privileged MFA Coverage"],
                         cap="Grade capped at Good because Privileged MFA Coverage could not be evaluated."),
        privileged_mfa=MFACoverageFinding(status=FindingStatus.SKIPPED, skipped_reason="Data unavailable."),
    )
    print_summary(result)
    out = capsys.readouterr().out
    assert "SKIPPED" in out or "Skipped" in out


def test_markdown_contains_footer(tmp_path):
    out = tmp_path / "report.md"
    write_markdown(_result(), out)
    content = out.read_text(encoding="utf-8")
    assert "No data sent to Cloud Locksmith" in content


def test_markdown_contains_schema_version(tmp_path):
    out = tmp_path / "report.md"
    write_markdown(_result(), out)
    assert "Schema Version" in out.read_text(encoding="utf-8")


def test_markdown_contains_all_control_sections(tmp_path):
    out = tmp_path / "report.md"
    write_markdown(_result(), out)
    content = out.read_text(encoding="utf-8")
    for heading in ["Identity Security Posture Score", "Tenant-wide MFA Coverage",
                    "Security Defaults", "Conditional Access", "User App Consent",
                    "Guest Accounts", "License Optimization"]:
        assert heading in content, f"missing section: {heading}"


def test_markdown_skipped_finding_renders(tmp_path):
    result = _result(dormant_users=DormantUsersFinding(
        status=FindingStatus.SKIPPED, skipped_reason="Sign-in activity unavailable for this tenant."))
    out = tmp_path / "report.md"
    write_markdown(result, out)
    content = out.read_text(encoding="utf-8")
    assert "SKIPPED" in content
    assert "Sign-in activity unavailable" in content


def test_markdown_contains_posture_disclaimer(tmp_path):
    out = tmp_path / "report.md"
    write_markdown(_result(), out)
    text = out.read_text(encoding="utf-8").lower()
    assert "insurance eligibility" in text
    assert "not a measure of overall cybersecurity" in text


def test_json_output_shape():
    result = _result()
    import json
    data = json.loads(result.model_dump_json())
    assert data["schema_version"]
    assert "posture" in data
    assert "grade" in data["posture"]
    assert "security_defaults" in data
    assert "conditional_access" in data
    # No tenant identifiers leak into the machine-readable output.
    assert "tenant_id" not in data


def test_pdf_is_written(tmp_path):
    out = tmp_path / "report.pdf"
    write_pdf(_result(), out)
    assert out.exists()
    assert out.stat().st_size > 1000


def test_assessment_output_has_no_credential_fields(tmp_path):
    """The JSON and Markdown outputs must never contain tokens/secrets/auth headers."""
    import json
    result = _result()
    blobs = [result.model_dump_json().lower()]
    md = tmp_path / "r.md"
    write_markdown(result, md)
    blobs.append(md.read_text(encoding="utf-8").lower())
    forbidden = ["access_token", "refresh_token", "bearer ", "client_secret",
                 "authorization", "id_token", "password"]
    for blob in blobs:
        for term in forbidden:
            assert term not in blob, f"sensitive term leaked into output: {term!r}"


def test_disabled_licensed_is_not_a_scored_control(tmp_path):
    """Regression: disabled-but-licensed is cost/hygiene, never in the score table."""
    md = tmp_path / "r.md"
    write_markdown(_result(), md)
    content = md.read_text(encoding="utf-8")
    posture_table = content.split("## Identity Security Posture Score")[1].split("##")[0]
    assert "Disabled" not in posture_table
