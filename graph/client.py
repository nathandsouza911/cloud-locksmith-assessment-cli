from __future__ import annotations
import logging
import time
import requests
from models.graph import User, SubscribedSku, CredentialRegistration

logger = logging.getLogger(__name__)
GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class GraphClient:
    """HTTP client for Microsoft Graph. Satisfies GraphDataProvider structurally."""

    def __init__(self, token: dict) -> None:
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token['access_token']}",
            "Content-Type": "application/json",
        })

    def _request_with_retry(self, url: str, params: dict | None = None) -> requests.Response:
        for attempt in range(4):
            resp = self._session.get(url, params=params)
            if resp.status_code in (429, 503):
                delay = int(resp.headers.get("Retry-After", 2 ** attempt))
                logger.warning("Rate limited — retrying in %ds (attempt %d)", delay, attempt + 1)
                time.sleep(delay)
                continue
            resp.raise_for_status()
            return resp
        raise RuntimeError(f"Request failed after 4 retries: {url}")

    def _get_paginated(self, url: str, params: dict | None = None) -> list[dict]:
        results: list[dict] = []
        next_url: str | None = url
        first = True
        while next_url:
            resp = self._request_with_retry(next_url, params=params if first else None)
            first = False
            data = resp.json()
            results.extend(data.get("value", []))
            next_url = data.get("@odata.nextLink")
        return results

    def get_users(self, select: list[str], filter_expr: str | None = None) -> list[User]:
        params: dict = {"$select": ",".join(select)}
        if filter_expr:
            params["$filter"] = filter_expr
        raw = self._get_paginated(f"{GRAPH_BASE}/users", params=params)
        return [User.model_validate(u) for u in raw]

    def get_subscribed_skus(self) -> list[SubscribedSku]:
        resp = self._request_with_retry(f"{GRAPH_BASE}/subscribedSkus")
        return [SubscribedSku.model_validate(s) for s in resp.json().get("value", [])]

    def get_role_members(self, role_template_id: str) -> list[User]:
        roles_resp = self._request_with_retry(f"{GRAPH_BASE}/directoryRoles")
        roles = roles_resp.json().get("value", [])
        role = next((r for r in roles if r.get("roleTemplateId") == role_template_id), None)
        if not role:
            logger.warning("Role template %s not found in activated directory roles.", role_template_id)
            return []
        raw = self._get_paginated(f"{GRAPH_BASE}/directoryRoles/{role['id']}/members")
        return [User.model_validate(m) for m in raw]

    def get_credential_registrations(self) -> list[CredentialRegistration]:
        raw = self._get_paginated(f"{GRAPH_BASE}/reports/credentialUserRegistrationDetails")
        return [CredentialRegistration.model_validate(r) for r in raw]
