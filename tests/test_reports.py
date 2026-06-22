import io
import json
import sys
import tempfile
from datetime import datetime, timezone

import pytest

from models.findings import (
    FindingStatus, LicenseWasteFinding, DormantUsersFinding,
    DisabledLicensedFinding, GlobalAdminsFinding, MFACoverageFinding,
)
from models.readiness import InsuranceReadiness, ControlResult
from reports.executive_summary import print_summary
from reports.markdown_report import write_markdown
from reports.pdf_report import write_pdf


def _strong_readiness() -> InsuranceReadiness:
    controls = [
        ControlResult(name="MFA Coverage", status="PASS", detail="100%", points=2),
        ControlResult(name="Global Admin Count", status="PASS", detail="2 admins", points=2),
        ControlResult(name="Dormant Licensed Users", status="PASS", detail="0", points=2),
        ControlResult(name="Disabled Licensed Users", status="PASS", detail="0", points=2),
    ]
    return InsuranceReadiness(controls=controls, total_score=8, max_possible_score=8,
                              score_pct=100.0, tier="Strong")


def test_print_summary_contains_tier(capsys):
    lw = LicenseWasteFinding(status=FindingStatus.SUCCESS, estimated_annual_waste_usd=1000.0, unassigned_units=5)
    dormant = DormantUsersFinding(status=FindingStatus.SUCCESS, total_count=0)
    disabled = DisabledLicensedFinding(status=FindingStatus.SUCCESS, total_count=0)
    admins = GlobalAdminsFinding(status=FindingStatus.SUCCESS, count=2, risk_level="Good")
    mfa = MFACoverageFinding(status=FindingStatus.SUCCESS, coverage_pct=100.0,
                             privileged_user_count=2, mfa_registered_count=2)
    print_summary(lw, dormant, disabled, admins, mfa, _strong_readiness())
    out = capsys.readouterr().out
    assert "STRONG" in out
    assert "INSURANCE READINESS ESTIMATE" in out


def test_print_summary_contains_footer(capsys):
    lw = LicenseWasteFinding()
    dormant = DormantUsersFinding()
    disabled = DisabledLicensedFinding()
    admins = GlobalAdminsFinding()
    mfa = MFACoverageFinding()
    print_summary(lw, dormant, disabled, admins, mfa, _strong_readiness())
    out = capsys.readouterr().out
    assert "No data sent to Cloud Locksmith" in out


def test_print_summary_skipped_finding(capsys):
    mfa = MFACoverageFinding(status=FindingStatus.SKIPPED, skipped_reason="Data unavailable.")
    lw = LicenseWasteFinding()
    dormant = DormantUsersFinding()
    disabled = DisabledLicensedFinding()
    admins = GlobalAdminsFinding()
    controls = [
        ControlResult(name="MFA Coverage", status="SKIPPED", detail="Data unavailable.", points=0),
        ControlResult(name="Global Admin Count", status="PASS", detail="2 admins", points=2),
        ControlResult(name="Dormant Licensed Users", status="PASS", detail="0", points=2),
        ControlResult(name="Disabled Licensed Users", status="PASS", detail="0", points=2),
    ]
    readiness = InsuranceReadiness(controls=controls, total_score=6, max_possible_score=6,
                                   score_pct=100.0, skipped_controls=["MFA Coverage"], tier="Strong")
    print_summary(lw, dormant, disabled, admins, mfa, readiness)
    out = capsys.readouterr().out
    assert "SKIPPED" in out


def test_markdown_contains_footer(tmp_path):
    lw = LicenseWasteFinding(status=FindingStatus.SUCCESS, estimated_annual_waste_usd=5000.0,
                             active_units=100, consumed_units=80, unassigned_units=20)
    dormant = DormantUsersFinding(status=FindingStatus.SUCCESS, total_count=2)
    disabled = DisabledLicensedFinding(status=FindingStatus.SUCCESS, total_count=1)
    admins = GlobalAdminsFinding(status=FindingStatus.SUCCESS, count=3, risk_level="Good")
    mfa = MFACoverageFinding(status=FindingStatus.SUCCESS, coverage_pct=95.0,
                             privileged_user_count=3, mfa_registered_count=3)
    out = tmp_path / "report.md"
    write_markdown(lw, dormant, disabled, admins, mfa, _strong_readiness(), out)
    content = out.read_text(encoding="utf-8")
    assert "No data sent to Cloud Locksmith" in content


def test_markdown_contains_assessment_version(tmp_path):
    out = tmp_path / "report.md"
    write_markdown(LicenseWasteFinding(), DormantUsersFinding(), DisabledLicensedFinding(),
                   GlobalAdminsFinding(), MFACoverageFinding(), _strong_readiness(), out)
    assert "1.0.0" in out.read_text(encoding="utf-8")


def test_markdown_skipped_finding_renders(tmp_path):
    dormant = DormantUsersFinding(status=FindingStatus.SKIPPED,
                                  skipped_reason="Sign-in activity unavailable for this tenant.")
    out = tmp_path / "report.md"
    write_markdown(LicenseWasteFinding(), dormant, DisabledLicensedFinding(),
                   GlobalAdminsFinding(), MFACoverageFinding(), _strong_readiness(), out)
    content = out.read_text(encoding="utf-8")
    assert "SKIPPED" in content
    assert "Sign-in activity unavailable" in content


def test_markdown_contains_estimate_disclaimer(tmp_path):
    out = tmp_path / "report.md"
    write_markdown(LicenseWasteFinding(), DormantUsersFinding(), DisabledLicensedFinding(),
                   GlobalAdminsFinding(), MFACoverageFinding(), _strong_readiness(), out)
    assert "not an underwriting decision" in out.read_text(encoding="utf-8")


def test_json_output_shape():
    """Verify the JSON dict produced in cli.py has the required top-level keys."""
    lw = LicenseWasteFinding(status=FindingStatus.SUCCESS, estimated_annual_waste_usd=1000.0,
                             active_units=100, consumed_units=80, unassigned_units=20)
    dormant = DormantUsersFinding(status=FindingStatus.SUCCESS, total_count=0)
    disabled = DisabledLicensedFinding(status=FindingStatus.SUCCESS, total_count=0)
    admins = GlobalAdminsFinding(status=FindingStatus.SUCCESS, count=2, risk_level="Good")
    mfa = MFACoverageFinding(status=FindingStatus.SUCCESS, coverage_pct=100.0,
                             privileged_user_count=2, mfa_registered_count=2)
    readiness = _strong_readiness()

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assessment_version": "1.0.0",
        "license_waste": json.loads(lw.model_dump_json()),
        "dormant_users": json.loads(dormant.model_dump_json()),
        "disabled_licensed_users": json.loads(disabled.model_dump_json()),
        "global_admins": json.loads(admins.model_dump_json()),
        "mfa_coverage": json.loads(mfa.model_dump_json()),
        "insurance_readiness": json.loads(readiness.model_dump_json()),
        "metadata": {
            "assessment_version": "1.0.0",
            "authentication": "Microsoft Device Code Flow",
            "permissions": "Read-only delegated",
            "data_handling": "No data transmitted to Cloud Locksmith.",
            "token_handling": "Tokens discarded after assessment.",
        },
    }
    assert "tenant_id" not in result
    assert result["assessment_version"] == "1.0.0"
    assert result["metadata"]["assessment_version"] == "1.0.0"
    assert "status" in result["license_waste"]
    assert "tier" in result["insurance_readiness"]


def test_pdf_is_written(tmp_path):
    out = tmp_path / "report.pdf"
    write_pdf(
        LicenseWasteFinding(status=FindingStatus.SUCCESS, estimated_annual_waste_usd=5000.0,
                            active_units=100, consumed_units=80, unassigned_units=20),
        DormantUsersFinding(status=FindingStatus.SUCCESS, total_count=3),
        DisabledLicensedFinding(status=FindingStatus.SUCCESS, total_count=1),
        GlobalAdminsFinding(status=FindingStatus.SUCCESS, count=2, risk_level="Good"),
        MFACoverageFinding(status=FindingStatus.SUCCESS, coverage_pct=95.0,
                           privileged_user_count=2, mfa_registered_count=2),
        _strong_readiness(),
        out,
    )
    assert out.exists()
    assert out.stat().st_size > 1000  # non-trivial PDF
