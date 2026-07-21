"""Tests for the controls added for the open-source launch."""
from datetime import datetime, timedelta, timezone

from models.findings import FindingStatus
from models.graph import (
    User, SignInActivity, CredentialRegistration,
    SecurityDefaults, ConditionalAccessPolicy, AuthorizationPolicy,
    DefaultUserRolePermissions,
)
from graph.errors import GraphAPIError
from tests.conftest import StubGraphDataProvider

from findings.tenant_mfa import TenantMFAFinder
from findings.privileged_roles import PrivilegedRolesFinder
from findings.guest_users import GuestUsersFinder
from findings.stale_guests import StaleGuestsFinder
from findings.security_defaults import SecurityDefaultsFinder
from findings.conditional_access import ConditionalAccessFinder
from findings.user_consent import UserConsentFinder

_S = FindingStatus.SUCCESS


def _guest(id: str, days_ago: int | None) -> User:
    if days_ago is None:
        activity = None
    elif days_ago < 0:
        activity = SignInActivity(lastSignInDateTime=None)
    else:
        activity = SignInActivity(lastSignInDateTime=datetime.now(timezone.utc) - timedelta(days=days_ago))
    return User(id=id, displayName=f"Guest {id}", userPrincipalName=f"g{id}@ext.com",
                userType="Guest", signInActivity=activity)


# ── Tenant-wide MFA ───────────────────────────────────────────────────────────

def test_tenant_mfa_coverage():
    regs = [
        CredentialRegistration(id="1", isMfaRegistered=True),
        CredentialRegistration(id="2", isMfaRegistered=True),
        CredentialRegistration(id="3", isMfaRegistered=False),
        CredentialRegistration(id="4", isMfaRegistered=True),
    ]
    finding = TenantMFAFinder(StubGraphDataProvider(registrations=regs)).run()
    assert finding.status == _S
    assert finding.total_users == 4
    assert finding.mfa_registered_count == 3
    assert finding.coverage_pct == 75.0


def test_tenant_mfa_skipped_when_no_data():
    finding = TenantMFAFinder(StubGraphDataProvider(registrations=[])).run()
    assert finding.status == FindingStatus.SKIPPED


def test_tenant_mfa_403_is_skipped():
    class Failing:
        def get_credential_registrations(self):
            raise GraphAPIError(403, "Authorization_RequestDenied", "denied")
    finding = TenantMFAFinder(Failing()).run()
    assert finding.status == FindingStatus.SKIPPED


# ── Privileged role sprawl ────────────────────────────────────────────────────

def test_privileged_roles_distinct_count():
    u1 = User(id="1", displayName="A", userPrincipalName="a@t.com")
    u2 = User(id="2", displayName="B", userPrincipalName="b@t.com")
    mapping = {
        "Global Administrator": [u1, u2],
        "Security Administrator": [u1],  # u1 holds two roles → counted once
    }
    finding = PrivilegedRolesFinder(StubGraphDataProvider(role_members_map=mapping)).run()
    assert finding.status == _S
    assert finding.distinct_privileged_users == 2
    assert len(finding.roles) == 2


def test_privileged_roles_skipped_when_none():
    finding = PrivilegedRolesFinder(StubGraphDataProvider(role_members_map={})).run()
    assert finding.status == FindingStatus.SKIPPED


# ── Guests ────────────────────────────────────────────────────────────────────

def test_guest_inventory_counts_and_caps_examples():
    guests = [_guest(str(i), days_ago=10) for i in range(6)]
    finding = GuestUsersFinder(StubGraphDataProvider(guests=guests)).run()
    assert finding.status == _S
    assert finding.total_count == 6
    assert len(finding.examples) == 3


def test_stale_guests_detects_90_day():
    guests = [_guest("1", days_ago=120), _guest("2", days_ago=10)]
    finding = StaleGuestsFinder(StubGraphDataProvider(guests=guests)).run()
    assert finding.total_count == 1


def test_stale_guests_never_signed_in_counts():
    finding = StaleGuestsFinder(StubGraphDataProvider(guests=[_guest("1", days_ago=-1)])).run()
    assert finding.total_count == 1


def test_stale_guests_skipped_when_no_signin_data():
    finding = StaleGuestsFinder(StubGraphDataProvider(guests=[_guest("1", days_ago=None)])).run()
    assert finding.status == FindingStatus.SKIPPED


def test_stale_guests_zero_when_no_guests():
    finding = StaleGuestsFinder(StubGraphDataProvider(guests=[])).run()
    assert finding.status == _S
    assert finding.total_count == 0


# ── Security Defaults ─────────────────────────────────────────────────────────

def test_security_defaults_enabled():
    finding = SecurityDefaultsFinder(
        StubGraphDataProvider(security_defaults=SecurityDefaults(isEnabled=True))).run()
    assert finding.status == _S
    assert finding.enabled is True


def test_security_defaults_403_skipped():
    class Failing:
        def get_security_defaults(self):
            raise GraphAPIError(403, "Authorization_RequestDenied", "denied")
    finding = SecurityDefaultsFinder(Failing()).run()
    assert finding.status == FindingStatus.SKIPPED
    assert "Policy.Read.All" in finding.skipped_reason


# ── Conditional Access ────────────────────────────────────────────────────────

def test_conditional_access_counts_states():
    policies = [
        ConditionalAccessPolicy(id="1", displayName="Require MFA", state="enabled"),
        ConditionalAccessPolicy(id="2", displayName="Block legacy", state="enabled"),
        ConditionalAccessPolicy(id="3", displayName="Pilot", state="enabledForReportingButNotEnforced"),
        ConditionalAccessPolicy(id="4", displayName="Off", state="disabled"),
    ]
    finding = ConditionalAccessFinder(StubGraphDataProvider(conditional_access=policies)).run()
    assert finding.status == _S
    assert finding.policy_count == 4
    assert finding.enabled_count == 2
    assert finding.report_only_count == 1
    assert "Require MFA" in finding.examples


def test_conditional_access_403_skipped():
    class Failing:
        def get_conditional_access_policies(self):
            raise GraphAPIError(403, "Authorization_RequestDenied", "denied")
    finding = ConditionalAccessFinder(Failing()).run()
    assert finding.status == FindingStatus.SKIPPED


# ── User consent ──────────────────────────────────────────────────────────────

def _authz(policies: list[str]) -> AuthorizationPolicy:
    return AuthorizationPolicy(
        defaultUserRolePermissions=DefaultUserRolePermissions(permissionGrantPoliciesAssigned=policies))


def test_user_consent_users_can_consent():
    policy = _authz(["ManagePermissionGrantsForSelf.microsoft-user-default-legacy"])
    finding = UserConsentFinder(StubGraphDataProvider(authorization_policy=policy)).run()
    assert finding.status == _S
    assert finding.users_can_consent is True


def test_user_consent_restricted_to_admins():
    finding = UserConsentFinder(StubGraphDataProvider(authorization_policy=_authz([]))).run()
    assert finding.status == _S
    assert finding.users_can_consent is False


def test_user_consent_403_skipped():
    class Failing:
        def get_authorization_policy(self):
            raise GraphAPIError(403, "Authorization_RequestDenied", "denied")
    finding = UserConsentFinder(Failing()).run()
    assert finding.status == FindingStatus.SKIPPED
