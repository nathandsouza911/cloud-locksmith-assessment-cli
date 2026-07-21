from __future__ import annotations
import os
import msal

AUTHORITY = "https://login.microsoftonline.com/common"

# Validated scope set — all are read-only delegated and require admin consent:
# Directory.Read.All    — list users/guests, resolve directory roles and members
# Reports.Read.All      — MFA registration details (requires Entra P1/P2 + admin consent)
# Organization.Read.All — subscribed SKUs, org metadata
# AuditLog.Read.All     — signInActivity on User objects (requires Entra P1/P2 + admin consent)
# Policy.Read.All       — security defaults, Conditional Access, authorization policy
SCOPES: list[str] = [
    "Directory.Read.All",
    "Reports.Read.All",
    "Organization.Read.All",
    "AuditLog.Read.All",
    "Policy.Read.All",
]


CLIENT_ID_ENV = "CLOUDLOCKSMITH_CLIENT_ID"

_MISSING_CLIENT_ID_MSG = (
    "No Azure App Registration client ID was provided.\n"
    "\n"
    "  What's missing: the Application (client) ID of an Entra App Registration.\n"
    "  Why it's needed: this CLI signs in with your own app registration (device-code,\n"
    "                   public-client, delegated read-only). No client secret is used.\n"
    "\n"
    "  Provide it either way (the --client-id flag takes precedence over the env var):\n"
    f"    cloudlocksmith assess --client-id <CLIENT_ID>\n"
    f"    export {CLIENT_ID_ENV}=<CLIENT_ID>        # macOS/Linux\n"
    f"    $env:{CLIENT_ID_ENV} = '<CLIENT_ID>'      # PowerShell\n"
    "\n"
    "  Setup guide: README.md (Setup) and docs/PERMISSIONS.md."
)


def resolve_client_id(client_id: str | None = None) -> str:
    """Resolve the client ID with documented precedence: explicit argument
    (e.g. the --client-id flag) first, then the environment variable."""
    resolved = client_id or os.environ.get(CLIENT_ID_ENV)
    if not resolved:
        raise RuntimeError(_MISSING_CLIENT_ID_MSG)
    return resolved


def acquire_token(client_id: str | None = None) -> dict:
    """Run MSAL Device Code flow. Returns token dict. Never persists to disk.

    Client ID precedence: explicit `client_id` argument (the CLI --client-id
    flag) overrides the CLOUDLOCKSMITH_CLIENT_ID environment variable.
    """
    client_id = resolve_client_id(client_id)
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
