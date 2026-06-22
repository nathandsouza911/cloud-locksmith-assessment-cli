import pytest
from pydantic import Field
from models.graph import User, SubscribedSku, PrepaidUnits, CredentialRegistration
from tests.conftest import StubGraphDataProvider
from graph.users import fetch_all_licensed_users, fetch_disabled_users
from graph.licenses import fetch_subscribed_skus
from graph.roles import fetch_global_admins, GLOBAL_ADMIN_TEMPLATE_ID
from graph.mfa import fetch_credential_registrations


def _user(id: str, enabled: bool = True, licensed: bool = True) -> User:
    licenses = [{"skuId": "abc"}] if licensed else []
    return User(id=id, displayName=f"User {id}", userPrincipalName=f"u{id}@t.com",
                accountEnabled=enabled, assignedLicenses=licenses)


def test_fetch_all_licensed_users_filters_unlicensed():
    stub = StubGraphDataProvider(users=[
        _user("1", licensed=True),
        _user("2", licensed=False),
    ])
    result = fetch_all_licensed_users(stub)
    assert len(result) == 1
    assert result[0].id == "1"


def test_fetch_disabled_users_returns_disabled():
    stub = StubGraphDataProvider(users=[
        _user("1", enabled=True),
        _user("2", enabled=False),
    ])
    result = fetch_disabled_users(stub)
    assert len(result) == 1
    assert result[0].id == "2"


def test_fetch_subscribed_skus():
    sku = SubscribedSku(skuId="x", skuPartNumber="SPE_E3", consumedUnits=80,
                        prepaidUnits=PrepaidUnits(enabled=100, suspended=0, warning=0))
    stub = StubGraphDataProvider(skus=[sku])
    result = fetch_subscribed_skus(stub)
    assert result[0].skuPartNumber == "SPE_E3"


def test_global_admin_template_id_is_correct():
    assert GLOBAL_ADMIN_TEMPLATE_ID == "62e90394-69f5-4237-9190-012177145e10"


def test_fetch_global_admins():
    admin = _user("admin1")
    stub = StubGraphDataProvider(role_members=[admin])
    result = fetch_global_admins(stub)
    assert result[0].id == "admin1"


def test_fetch_credential_registrations():
    reg = CredentialRegistration(userId="u1", userPrincipalName="u1@t.com", isMfaRegistered=True)
    stub = StubGraphDataProvider(registrations=[reg])
    result = fetch_credential_registrations(stub)
    assert result[0].isMfaRegistered is True
