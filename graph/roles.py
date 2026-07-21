from __future__ import annotations
from graph.provider import GraphDataProvider
from models.graph import User

GLOBAL_ADMIN_TEMPLATE_ID = "62e90394-69f5-4237-9190-012177145e10"

# Curated set of high-impact directory roles for the privileged-sprawl control.
# Keys are well-known roleTemplateIds; values are display names for reporting.
# Read-only roles (e.g. Global Reader) are intentionally excluded — they are not
# a lateral-movement / tenant-takeover risk in the way write-capable roles are.
PRIVILEGED_ROLE_TEMPLATES: dict[str, str] = {
    GLOBAL_ADMIN_TEMPLATE_ID: "Global Administrator",
    "e8611ab8-c189-46e8-94e1-60213ab1f814": "Privileged Role Administrator",
    "7be44c8a-adaf-4e2a-84d6-ab2649e08a13": "Privileged Authentication Administrator",
    "194ae4cb-b126-40b2-bd5b-6091b380977d": "Security Administrator",
    "9b895d92-2cd3-44c7-9d02-a6ac2d5ea5c3": "Application Administrator",
    "158c047a-c907-4556-b7ef-446551a6b5f7": "Cloud Application Administrator",
    "fe930be7-5e62-47db-91af-98c3a49a38b1": "User Administrator",
    "c4e39bd9-1100-46d3-8c65-fb160da0071f": "Authentication Administrator",
    "29232cdf-9323-42fd-ade2-1d097af3e4de": "Exchange Administrator",
    "f28a1f50-f6e7-4571-818b-6a12f2af6b6c": "SharePoint Administrator",
    "b1be1c3e-b65d-4f19-8427-f6fa0d97feb9": "Conditional Access Administrator",
}


def fetch_global_admins(provider: GraphDataProvider) -> list[User]:
    return provider.get_role_members(GLOBAL_ADMIN_TEMPLATE_ID)


def fetch_privileged_role_members(provider: GraphDataProvider) -> dict[str, list[User]]:
    return provider.get_role_members_map(PRIVILEGED_ROLE_TEMPLATES)
