from __future__ import annotations
from dataclasses import dataclass, field
import pytest
from models.graph import User, SubscribedSku, CredentialRegistration


@dataclass
class StubGraphDataProvider:
    users: list[User] = field(default_factory=list)
    skus: list[SubscribedSku] = field(default_factory=list)
    role_members: list[User] = field(default_factory=list)
    registrations: list[CredentialRegistration] = field(default_factory=list)

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


@pytest.fixture
def stub_provider():
    return StubGraphDataProvider()
