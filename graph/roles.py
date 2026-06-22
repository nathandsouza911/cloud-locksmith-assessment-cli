from __future__ import annotations
from graph.provider import GraphDataProvider
from models.graph import User

GLOBAL_ADMIN_TEMPLATE_ID = "62e90394-69f5-4237-9190-012177145e10"


def fetch_global_admins(provider: GraphDataProvider) -> list[User]:
    return provider.get_role_members(GLOBAL_ADMIN_TEMPLATE_ID)
