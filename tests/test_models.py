import pytest
from models.findings import FindingStatus, LicenseWasteFinding, DormantUsersFinding, UserSummary
from models.graph import User, SubscribedSku, PrepaidUnits, SignInActivity
from models.posture import ControlResult, PostureScore


def test_finding_status_values():
    assert FindingStatus.SUCCESS == "SUCCESS"
    assert FindingStatus.SKIPPED == "SKIPPED"
    assert FindingStatus.ERROR == "ERROR"


def test_license_waste_finding_defaults_to_success():
    f = LicenseWasteFinding()
    assert f.status == FindingStatus.SUCCESS
    assert f.skipped_reason is None
    assert f.estimated_reclaimable_annual_usd == 0.0
    assert f.estimated_reclaimable_monthly_usd == 0.0


def test_dormant_users_finding_list_is_not_shared():
    # Verifies Field(default_factory=list) — two instances must not share the same list
    a = DormantUsersFinding()
    b = DormantUsersFinding()
    a.examples.append(UserSummary(display_name="X", user_principal_name="x@y.com"))
    assert len(b.examples) == 0


def test_user_licenses_not_shared():
    a = User(id="1", displayName="A", userPrincipalName="a@t.com")
    b = User(id="2", displayName="B", userPrincipalName="b@t.com")
    a.assignedLicenses.append({"skuId": "abc"})
    assert len(b.assignedLicenses) == 0


def test_posture_score_controls_not_shared():
    a = PostureScore(total_score=0, max_possible_score=0, score_pct=0.0, grade="Weak")
    b = PostureScore(total_score=0, max_possible_score=0, score_pct=0.0, grade="Weak")
    a.controls.append(ControlResult(name="X", status="PASS", detail="ok", points=2))
    assert len(b.controls) == 0


def test_user_summary_fields():
    s = UserSummary(display_name="Jane Smith", user_principal_name="jsmith@contoso.com")
    assert s.display_name == "Jane Smith"
    assert s.user_principal_name == "jsmith@contoso.com"


def test_subscribed_sku_parses():
    raw = {
        "skuId": "abc123",
        "skuPartNumber": "SPE_E3",
        "consumedUnits": 80,
        "prepaidUnits": {"enabled": 100, "suspended": 0, "warning": 0},
    }
    sku = SubscribedSku.model_validate(raw)
    assert sku.skuPartNumber == "SPE_E3"
    assert sku.prepaidUnits.enabled == 100
