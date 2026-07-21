from __future__ import annotations
from dataclasses import dataclass, field
import pytest
from models.graph import (
    User, SubscribedSku, CredentialRegistration,
    SecurityDefaults, ConditionalAccessPolicy, AuthorizationPolicy,
)


@dataclass
class StubGraphDataProvider:
    users: list[User] = field(default_factory=list)
    skus: list[SubscribedSku] = field(default_factory=list)
    role_members: list[User] = field(default_factory=list)
    registrations: list[CredentialRegistration] = field(default_factory=list)
    guests: list[User] = field(default_factory=list)
    role_members_map: dict[str, list[User]] = field(default_factory=dict)
    security_defaults: SecurityDefaults | None = None
    conditional_access: list[ConditionalAccessPolicy] = field(default_factory=list)
    authorization_policy: AuthorizationPolicy | None = None

    def get_users(self, select: list[str], filter_expr: str | None = None) -> list[User]:
        if filter_expr and "accountEnabled eq false" in filter_expr:
            return [u for u in self.users if not u.accountEnabled]
        return self.users

    def get_subscribed_skus(self) -> list[SubscribedSku]:
        return self.skus

    def get_role_members(self, role_template_id: str) -> list[User]:
        return self.role_members

    def get_credential_registrations(self) -> list[CredentialRegistration]:
        return self.registrations

    def get_guest_users(self) -> list[User]:
        return self.guests

    def get_role_members_map(self, templates: dict[str, str]) -> dict[str, list[User]]:
        return self.role_members_map

    def get_security_defaults(self) -> SecurityDefaults:
        return self.security_defaults or SecurityDefaults(isEnabled=False)

    def get_conditional_access_policies(self) -> list[ConditionalAccessPolicy]:
        return self.conditional_access

    def get_authorization_policy(self) -> AuthorizationPolicy:
        return self.authorization_policy or AuthorizationPolicy()


@pytest.fixture
def stub_provider():
    return StubGraphDataProvider()
