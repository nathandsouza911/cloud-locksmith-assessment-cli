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


def test_license_waste_estimates_annual_cost():
    # SPE_E3 = $360/yr; 20 unassigned → $7,200
    stub = StubGraphDataProvider(skus=[_sku("SPE_E3", enabled=100, consumed=80)])
    finding = UnassignedLicenseFinder(stub).run()
    assert finding.estimated_annual_waste_usd == 7200.0


def test_license_waste_unknown_sku_priced_at_zero():
    stub = StubGraphDataProvider(skus=[_sku("UNKNOWN_SKU", enabled=50, consumed=30)])
    finding = UnassignedLicenseFinder(stub).run()
    assert finding.estimated_annual_waste_usd == 0.0


def test_license_waste_no_waste():
    stub = StubGraphDataProvider(skus=[_sku("SPE_E3", enabled=100, consumed=100)])
    finding = UnassignedLicenseFinder(stub).run()
    assert finding.unassigned_units == 0
    assert finding.estimated_annual_waste_usd == 0.0


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
        CredentialRegistration(userId="a1", userPrincipalName="a1@t.com", isMfaRegistered=True),
        CredentialRegistration(userId="a2", userPrincipalName="a2@t.com", isMfaRegistered=True),
    ]
    stub = StubGraphDataProvider(registrations=regs)
    finding = AdminMFAFinder(stub, admins).run()
    assert finding.status == FindingStatus.SUCCESS
    assert finding.coverage_pct == 100.0
    assert finding.privileged_user_count == 2


def test_admin_mfa_partial_coverage():
    admins = [_user("a1"), _user("a2")]
    regs = [
        CredentialRegistration(userId="a1", userPrincipalName="a1@t.com", isMfaRegistered=True),
        CredentialRegistration(userId="a2", userPrincipalName="a2@t.com", isMfaRegistered=False),
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
        CredentialRegistration(userId="a1", userPrincipalName="a1@t.com", isMfaRegistered=True),
        CredentialRegistration(userId="other", userPrincipalName="other@t.com", isMfaRegistered=True),
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
