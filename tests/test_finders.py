import pytest
from models.graph import SubscribedSku, PrepaidUnits
from models.findings import FindingStatus
from tests.conftest import StubGraphDataProvider
from findings.unassigned_licenses import UnassignedLicenseFinder


def _sku(part: str, enabled: int, consumed: int) -> SubscribedSku:
    return SubscribedSku(
        skuId=part,
        skuPartNumber=part,
        consumedUnits=consumed,
        prepaidUnits=PrepaidUnits(enabled=enabled, suspended=0, warning=0),
    )


def test_license_waste_calculates_unassigned():
    stub = StubGraphDataProvider(skus=[_sku("SPE_E3", enabled=100, consumed=80)])
    finding = UnassignedLicenseFinder(stub).run()
    assert finding.status == FindingStatus.SUCCESS
    assert finding.unassigned_units == 20
    assert finding.active_units == 100
    assert finding.consumed_units == 80


def test_license_waste_estimates_annual_and_monthly_cost():
    # SPE_E3 = $360/yr; 20 reclaimable → $7,200/yr, $600/mo
    stub = StubGraphDataProvider(skus=[_sku("SPE_E3", enabled=100, consumed=80)])
    finding = UnassignedLicenseFinder(stub).run()
    assert finding.estimated_reclaimable_annual_usd == 7200.0
    assert finding.estimated_reclaimable_monthly_usd == 600.0
    assert finding.priced_unassigned_units == 20


def test_license_waste_unknown_sku_excluded_from_dollars():
    stub = StubGraphDataProvider(skus=[_sku("UNKNOWN_SKU", enabled=50, consumed=30)])
    finding = UnassignedLicenseFinder(stub).run()
    # Unknown SKU seats are counted as reclaimable but NOT priced as $0 waste.
    assert finding.estimated_reclaimable_annual_usd == 0.0
    assert finding.unassigned_units == 20
    assert finding.unpriced_unassigned_units == 20
    assert finding.priced_unassigned_units == 0
    assert "UNKNOWN_SKU" in finding.unknown_skus


def test_license_waste_no_waste():
    stub = StubGraphDataProvider(skus=[_sku("SPE_E3", enabled=100, consumed=100)])
    finding = UnassignedLicenseFinder(stub).run()
    assert finding.unassigned_units == 0
    assert finding.estimated_reclaimable_annual_usd == 0.0


def test_license_waste_zero_priced_sku_counts_as_priced_not_unknown():
    # FLOW_FREE is a known SKU priced at $0 — its spare seats are "priced" ($0),
    # not "unpriced/unknown", so there is no partial-pricing warning.
    stub = StubGraphDataProvider(skus=[_sku("FLOW_FREE", enabled=50, consumed=10)])
    finding = UnassignedLicenseFinder(stub).run()
    assert finding.unassigned_units == 40
    assert finding.priced_unassigned_units == 40
    assert finding.unpriced_unassigned_units == 0
    assert finding.estimated_reclaimable_annual_usd == 0.0
    assert finding.partial_pricing_warning is None


def test_license_waste_mixed_priced_and_unpriced():
    stub = StubGraphDataProvider(skus=[
        _sku("SPE_E3", enabled=100, consumed=90),      # 10 priced, $360/yr each
        _sku("CONTOSO_CUSTOM", enabled=20, consumed=15),  # 5 unpriced
    ])
    finding = UnassignedLicenseFinder(stub).run()
    assert finding.unassigned_units == 15
    assert finding.priced_unassigned_units == 10
    assert finding.unpriced_unassigned_units == 5
    assert finding.estimated_reclaimable_annual_usd == 3600.0
    assert "CONTOSO_CUSTOM" in finding.unknown_skus
    assert finding.partial_pricing_warning is not None


def test_license_waste_user_pricing_override(tmp_path, monkeypatch):
    import json
    from pricing.sku_pricing import PRICING_OVERRIDE_ENV
    override = tmp_path / "pricing.json"
    override.write_text(json.dumps({"SPE_E3": 400.0, "CONTOSO_CUSTOM": 100.0}), encoding="utf-8")
    monkeypatch.setenv(PRICING_OVERRIDE_ENV, str(override))
    stub = StubGraphDataProvider(skus=[
        _sku("SPE_E3", enabled=100, consumed=90),          # override: $400 → $4000
        _sku("CONTOSO_CUSTOM", enabled=20, consumed=15),   # override: $100 → $500
    ])
    finding = UnassignedLicenseFinder(stub).run()
    # Override takes precedence over the built-in $360 for SPE_E3, and prices the custom SKU.
    assert finding.estimated_reclaimable_annual_usd == 4500.0
    assert finding.unpriced_unassigned_units == 0


def test_license_waste_skipped_when_no_skus():
    stub = StubGraphDataProvider(skus=[])
    finding = UnassignedLicenseFinder(stub).run()
    assert finding.status == FindingStatus.SKIPPED
    assert finding.skipped_reason is not None


def test_license_waste_returns_error_on_exception():
    class FailingProvider:
        def get_subscribed_skus(self): raise RuntimeError("Graph error")
        def get_users(self, **_): return []
        def get_role_members(self, _): return []
        def get_credential_registrations(self): return []

    finding = UnassignedLicenseFinder(FailingProvider()).run()
    assert finding.status == FindingStatus.ERROR
    assert finding.skipped_reason is not None


from findings.disabled_licenses import DisabledLicensedFinder
from models.graph import User


def _user(id: str, enabled: bool = True, licensed: bool = True) -> User:
    licenses = [{"skuId": "abc"}] if licensed else []
    return User(id=id, displayName=f"User {id}", userPrincipalName=f"u{id}@t.com",
                accountEnabled=enabled, assignedLicenses=licenses)


def test_disabled_licensed_finds_correct_count():
    stub = StubGraphDataProvider(users=[
        _user("1", enabled=False, licensed=True),
        _user("2", enabled=False, licensed=False),
        _user("3", enabled=True, licensed=True),
    ])
    finding = DisabledLicensedFinder(stub).run()
    assert finding.status == FindingStatus.SUCCESS
    assert finding.total_count == 1


def test_disabled_licensed_examples_capped_at_three():
    users = [_user(str(i), enabled=False, licensed=True) for i in range(10)]
    stub = StubGraphDataProvider(users=users)
    finding = DisabledLicensedFinder(stub).run()
    assert finding.total_count == 10
    assert len(finding.examples) == 3


def test_disabled_licensed_maps_to_user_summary():
    stub = StubGraphDataProvider(users=[_user("1", enabled=False, licensed=True)])
    finding = DisabledLicensedFinder(stub).run()
    assert finding.examples[0].display_name == "User 1"
    assert finding.examples[0].user_principal_name == "u1@t.com"


def test_disabled_licensed_handles_null_display_fields():
    # A directory object may lack displayName/UPN; building examples must not crash.
    u = User(id="guid-1", displayName=None, userPrincipalName=None,
             accountEnabled=False, assignedLicenses=[{"skuId": "abc"}])
    finding = DisabledLicensedFinder(StubGraphDataProvider(users=[u])).run()
    assert finding.status == FindingStatus.SUCCESS
    assert finding.examples[0].display_name == "guid-1"
    assert finding.examples[0].user_principal_name == "guid-1"


def test_disabled_licensed_zero_is_success_not_skipped():
    # An empty list of disabled users is a good result (no disabled accounts), not SKIPPED
    stub = StubGraphDataProvider(users=[])
    finding = DisabledLicensedFinder(stub).run()
    assert finding.status == FindingStatus.SUCCESS
    assert finding.total_count == 0


from datetime import datetime, timedelta, timezone
from findings.dormant_users import DormantUserFinder
from models.graph import SignInActivity


def _user_with_signin(id: str, days_ago: int | None) -> User:
    if days_ago is None:
        activity = None
    elif days_ago < 0:
        activity = SignInActivity(lastSignInDateTime=None)
    else:
        activity = SignInActivity(
            lastSignInDateTime=datetime.now(timezone.utc) - timedelta(days=days_ago)
        )
    return User(id=id, displayName=f"User {id}", userPrincipalName=f"u{id}@t.com",
                accountEnabled=True, assignedLicenses=[{"skuId": "abc"}],
                signInActivity=activity)


def test_dormant_user_90_plus_days():
    stub = StubGraphDataProvider(users=[
        _user_with_signin("1", days_ago=91),
        _user_with_signin("2", days_ago=30),
    ])
    finding = DormantUserFinder(stub).run()
    assert finding.status == FindingStatus.SUCCESS
    assert finding.total_count == 1


def test_dormant_user_null_signin_counted_as_dormant():
    stub = StubGraphDataProvider(users=[_user_with_signin("1", days_ago=-1)])
    finding = DormantUserFinder(stub).run()
    assert finding.total_count == 1


def test_dormant_user_signin_activity_absent_returns_skipped():
    # All signInActivity fields are None → tenant lacks AAD Premium
    stub = StubGraphDataProvider(users=[_user_with_signin("1", days_ago=None)])
    finding = DormantUserFinder(stub).run()
    assert finding.status == FindingStatus.SKIPPED
    assert finding.skipped_reason == "Sign-in activity unavailable for this tenant."


def test_dormant_user_examples_capped_at_three():
    users = [_user_with_signin(str(i), days_ago=100) for i in range(10)]
    stub = StubGraphDataProvider(users=users)
    finding = DormantUserFinder(stub).run()
    assert finding.total_count == 10
    assert len(finding.examples) == 3


from findings.admin_mfa import AdminMFAFinder
from models.graph import CredentialRegistration


def test_admin_mfa_full_coverage():
    admins = [_user("a1"), _user("a2")]
    regs = [
        CredentialRegistration(id="a1", userPrincipalName="a1@t.com", isMfaRegistered=True),
        CredentialRegistration(id="a2", userPrincipalName="a2@t.com", isMfaRegistered=True),
    ]
    stub = StubGraphDataProvider(registrations=regs)
    finding = AdminMFAFinder(stub, admins).run()
    assert finding.status == FindingStatus.SUCCESS
    assert finding.coverage_pct == 100.0
    assert finding.privileged_user_count == 2


def test_admin_mfa_partial_coverage():
    admins = [_user("a1"), _user("a2")]
    regs = [
        CredentialRegistration(id="a1", userPrincipalName="a1@t.com", isMfaRegistered=True),
        CredentialRegistration(id="a2", userPrincipalName="a2@t.com", isMfaRegistered=False),
    ]
    stub = StubGraphDataProvider(registrations=regs)
    finding = AdminMFAFinder(stub, admins).run()
    assert finding.coverage_pct == 50.0


def test_admin_mfa_no_registrations_returns_skipped():
    admins = [_user("a1")]
    stub = StubGraphDataProvider(registrations=[])
    finding = AdminMFAFinder(stub, admins).run()
    assert finding.status == FindingStatus.SKIPPED
    assert finding.skipped_reason == "Credential registration data unavailable."


def test_admin_mfa_no_admins_returns_skipped():
    stub = StubGraphDataProvider()
    finding = AdminMFAFinder(stub, admin_users=[]).run()
    assert finding.status == FindingStatus.SKIPPED


def test_admin_mfa_only_counts_admin_users():
    admins = [_user("a1")]
    # Registration for non-admin user "other" — must not be counted
    regs = [
        CredentialRegistration(id="a1", userPrincipalName="a1@t.com", isMfaRegistered=True),
        CredentialRegistration(id="other", userPrincipalName="other@t.com", isMfaRegistered=True),
    ]
    stub = StubGraphDataProvider(registrations=regs)
    finding = AdminMFAFinder(stub, admins).run()
    assert finding.privileged_user_count == 1
    assert finding.mfa_registered_count == 1


from findings.global_admins import GlobalAdminFinder


def test_global_admins_good_risk():
    admins = [_user(str(i)) for i in range(3)]
    stub = StubGraphDataProvider(role_members=admins)
    finding = GlobalAdminFinder(stub).run()
    assert finding.status == FindingStatus.SUCCESS
    assert finding.count == 3
    assert finding.risk_level == "Good"


def test_global_admins_moderate_risk():
    admins = [_user(str(i)) for i in range(5)]
    stub = StubGraphDataProvider(role_members=admins)
    finding = GlobalAdminFinder(stub).run()
    assert finding.risk_level == "Moderate"


def test_global_admins_high_risk():
    admins = [_user(str(i)) for i in range(7)]
    stub = StubGraphDataProvider(role_members=admins)
    finding = GlobalAdminFinder(stub).run()
    assert finding.risk_level == "High"


def test_global_admins_skipped_when_no_members():
    stub = StubGraphDataProvider(role_members=[])
    finding = GlobalAdminFinder(stub).run()
    assert finding.status == FindingStatus.SKIPPED
    assert finding.skipped_reason is not None


# ── SKU pricing warning ───────────────────────────────────────────────────────

def test_license_waste_warns_on_unknown_sku():
    stub = StubGraphDataProvider(skus=[_sku("UNKNOWN_SKU_XYZ", enabled=50, consumed=30)])
    finding = UnassignedLicenseFinder(stub).run()
    assert finding.status == FindingStatus.SUCCESS
    assert finding.partial_pricing_warning is not None
    assert "pricing data" in finding.partial_pricing_warning


def test_license_waste_no_warning_when_all_skus_known():
    stub = StubGraphDataProvider(skus=[_sku("SPE_E3", enabled=100, consumed=80)])
    finding = UnassignedLicenseFinder(stub).run()
    assert finding.partial_pricing_warning is None


def test_license_waste_skipped_message_describes_tenant_type():
    stub = StubGraphDataProvider(skus=[])
    finding = UnassignedLicenseFinder(stub).run()
    assert "commercial" in finding.skipped_reason.lower()
    assert "developer" in finding.skipped_reason.lower()


# ── MFA 403 classification ────────────────────────────────────────────────────

from graph.errors import GraphAPIError
from findings.admin_mfa import AdminMFAFinder, _classify_mfa_403


def test_classify_mfa_403_consent_named_code():
    msg = _classify_mfa_403("Authorization_RequestDenied", "Insufficient privileges to complete the operation.")
    assert "admin consent" in msg.lower()


def test_classify_mfa_403_consent_keyword_fallback():
    msg = _classify_mfa_403("AccessDenied", "You must grant consent to access this resource.")
    assert "admin consent" in msg.lower()


def test_classify_mfa_403_licensing_named_code():
    # The exact error code returned by Graph for tenants without Entra P1/P2
    msg = _classify_mfa_403(
        "Authentication_RequestFromNonPremiumTenantOrB2CTenant",
        "Tenant is not a B2C tenant and doesn't have premium license",
    )
    assert "P1 or P2" in msg


def test_classify_mfa_403_licensing_keyword_fallback():
    msg = _classify_mfa_403("AccessDenied", "The tenant requires Azure AD Premium license.")
    assert "P1 or P2" in msg


def test_classify_mfa_403_fallback():
    msg = _classify_mfa_403("AccessDenied", "Some other unknown reason.")
    assert "Possible causes" in msg


def test_admin_mfa_graph_api_403_returns_skipped():
    class Failing403Provider:
        def get_credential_registrations(self):
            raise GraphAPIError(403, "Authorization_RequestDenied", "Insufficient privileges.")
        def get_users(self, **_): return []
        def get_role_members(self, _): return []
        def get_subscribed_skus(self): return []

    admins = [_user("a1")]
    finding = AdminMFAFinder(Failing403Provider(), admins).run()
    assert finding.status == FindingStatus.SKIPPED
    assert "admin consent" in finding.skipped_reason.lower()


def test_admin_mfa_graph_api_non_403_returns_error():
    class Failing500Provider:
        def get_credential_registrations(self):
            raise GraphAPIError(500, "ServiceUnavailable", "Service is down.")
        def get_users(self, **_): return []
        def get_role_members(self, _): return []
        def get_subscribed_skus(self): return []

    admins = [_user("a1")]
    finding = AdminMFAFinder(Failing500Provider(), admins).run()
    assert finding.status == FindingStatus.ERROR
