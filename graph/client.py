from __future__ import annotations
import logging
import time
import requests
from models.graph import (
    User, SubscribedSku, CredentialRegistration,
    SecurityDefaults, ConditionalAccessPolicy, AuthorizationPolicy,
)
from graph.errors import GraphAPIError

logger = logging.getLogger(__name__)
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

_GUEST_FIELDS = ["id", "displayName", "userPrincipalName", "accountEnabled", "userType", "signInActivity"]


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
            if not resp.ok:
                self._raise_graph_error(resp)
            return resp
        raise RuntimeError(f"Request failed after 4 retries: {url}")

    @staticmethod
    def _raise_graph_error(resp: requests.Response) -> None:
        """Parse Graph error body and raise GraphAPIError with actionable fields."""
        try:
            body = resp.json()
            err = body.get("error", {})
            code = err.get("code") or "UnknownError"
            message = err.get("message") or resp.reason or "No message"
        except Exception:
            code = "UnknownError"
            message = resp.reason or "No message"
        raise GraphAPIError(resp.status_code, code, message)

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

    def get_guest_users(self) -> list[User]:
        params = {"$select": ",".join(_GUEST_FIELDS), "$filter": "userType eq 'Guest'"}
        raw = self._get_paginated(f"{GRAPH_BASE}/users", params=params)
        return [User.model_validate(u) for u in raw]

    def get_subscribed_skus(self) -> list[SubscribedSku]:
        resp = self._request_with_retry(f"{GRAPH_BASE}/subscribedSkus")
        return [SubscribedSku.model_validate(s) for s in resp.json().get("value", [])]

    def _activated_roles(self) -> list[dict]:
        resp = self._request_with_retry(f"{GRAPH_BASE}/directoryRoles")
        return resp.json().get("value", [])

    def get_role_members(self, role_template_id: str) -> list[User]:
        role = next(
            (r for r in self._activated_roles() if r.get("roleTemplateId") == role_template_id),
            None,
        )
        if not role:
            logger.warning("Role template %s not found in activated directory roles.", role_template_id)
            return []
        raw = self._get_paginated(f"{GRAPH_BASE}/directoryRoles/{role['id']}/members")
        return [User.model_validate(m) for m in raw]

    def get_role_members_map(self, templates: dict[str, str]) -> dict[str, list[User]]:
        """Resolve members for several roles with a single directoryRoles listing."""
        by_template = {r.get("roleTemplateId"): r for r in self._activated_roles()}
        out: dict[str, list[User]] = {}
        for template_id, name in templates.items():
            role = by_template.get(template_id)
            if not role:
                continue  # Role not activated in this tenant → no members.
            raw = self._get_paginated(f"{GRAPH_BASE}/directoryRoles/{role['id']}/members")
            out[name] = [User.model_validate(m) for m in raw]
        return out

    def get_credential_registrations(self) -> list[CredentialRegistration]:
        raw = self._get_paginated(f"{GRAPH_BASE}/reports/authenticationMethods/userRegistrationDetails")
        return [CredentialRegistration.model_validate(r) for r in raw]

    def get_security_defaults(self) -> SecurityDefaults:
        resp = self._request_with_retry(
            f"{GRAPH_BASE}/policies/identitySecurityDefaultsEnforcementPolicy"
        )
        return SecurityDefaults.model_validate(resp.json())

    def get_conditional_access_policies(self) -> list[ConditionalAccessPolicy]:
        raw = self._get_paginated(f"{GRAPH_BASE}/identity/conditionalAccess/policies")
        return [ConditionalAccessPolicy.model_validate(p) for p in raw]

    def get_authorization_policy(self) -> AuthorizationPolicy:
        resp = self._request_with_retry(f"{GRAPH_BASE}/policies/authorizationPolicy")
        return AuthorizationPolicy.model_validate(resp.json())
