from __future__ import annotations
from graph.provider import GraphDataProvider
from models.graph import CredentialRegistration


def fetch_credential_registrations(provider: GraphDataProvider) -> list[CredentialRegistration]:
    return provider.get_credential_registrations()
