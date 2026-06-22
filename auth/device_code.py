from __future__ import annotations
import os
import msal

AUTHORITY = "https://login.microsoftonline.com/common"

# Scopes validated against Graph endpoints:
# User.Read             — basic profile for the signed-in user
# Directory.Read.All    — list users, resolve directory roles and members
# Reports.Read.All      — credentialUserRegistrationDetails (admin consent required)
# Organization.Read.All — org-level metadata
# AuditLog.Read.All     — signInActivity on User objects (requires AAD Premium P1/P2)
SCOPES: list[str] = [
    "User.Read",
    "Directory.Read.All",
    "Reports.Read.All",
    "Organization.Read.All",
    "AuditLog.Read.All",
]


def acquire_token() -> dict:
    """Run MSAL Device Code flow. Returns token dict. Never persists to disk."""
    client_id = os.environ.get("CLOUDLOCKSMITH_CLIENT_ID")
    if not client_id:
        raise RuntimeError(
            "CLOUDLOCKSMITH_CLIENT_ID environment variable not set. "
            "Register an Azure AD app and set this to its Application (client) ID. "
            "See README.md for setup instructions."
        )
    app = msal.PublicClientApplication(client_id, authority=AUTHORITY)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(
            f"Device Code flow failed: {flow.get('error_description', 'unknown error')}"
        )
    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise RuntimeError(
            f"Authentication failed: {result.get('error_description', 'unknown error')}"
        )
    return result
