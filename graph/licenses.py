from __future__ import annotations
from graph.provider import GraphDataProvider
from models.graph import SubscribedSku


def fetch_subscribed_skus(provider: GraphDataProvider) -> list[SubscribedSku]:
    return provider.get_subscribed_skus()
