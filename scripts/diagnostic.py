"""
INTERNAL DIAGNOSTIC UTILITY — not part of the assessment CLI.

Used during development to probe live Graph API responses and diagnose
tenant-specific errors (licensing, endpoint availability, etc.).

Not intended for end users. Output may contain tenant metadata.

Usage (from repo root):
    uv run python scripts/diagnostic.py
"""
from __future__ import annotations
import json
import pathlib
import requests
from datetime import datetime, timezone

from auth.device_code import acquire_token

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
OUTPUT = pathlib.Path("output")

_PRIVACY_WARNING = (
    "\n"
    "  ┌─────────────────────────────────────────────────────────────────────────┐\n"
    "  │  DIAGNOSTIC PRIVACY NOTICE                                               │\n"
    "  │  Diagnostic output may contain tenant-specific metadata (tenant name,   │\n"
    "  │  tenant ID, SKU inventory, error bodies). Files are written locally      │\n"
    "  │  and are NEVER automatically transmitted to Cloud Locksmith or anyone.   │\n"
    "  │  No access tokens, refresh tokens, or authorization headers are written. │\n"
    "  │  Review and redact diagnostic files before sharing them publicly.        │\n"
    "  └─────────────────────────────────────────────────────────────────────────┘\n"
)

# Keys that must never appear in a written diagnostic file, at any depth. The
# diagnostic never intentionally collects these; this is a defense-in-depth
# scrub so a future change cannot accidentally serialize a credential.
_SENSITIVE_KEYS = {
    "access_token", "refresh_token", "id_token", "authorization",
    "client_secret", "password", "secret", "bearer",
}


def _scrub(obj):
    """Recursively drop any credential-like fields before writing to disk."""
    if isinstance(obj, dict):
        return {
            k: _scrub(v)
            for k, v in obj.items()
            if k.lower() not in _SENSITIVE_KEYS
        }
    if isinstance(obj, list):
        return [_scrub(v) for v in obj]
    return obj

# Known Entra ID P1 / P2 service plan IDs
_ENTRA_P1_PLAN_ID = "41781fb2-bc02-4b7c-bd55-b576c07bb09d"
_ENTRA_P2_PLAN_ID = "eec0eb4f-6444-4f95-aba0-50c24d67f998"

# Known developer/trial SKU part numbers
_DEVELOPER_SKUS = {
    "DEVELOPERPACK",
    "DEVELOPERPACK_E5",
    "M365_F1",
    "MICROSOFT_365_DEVELOPER",
}


def _get(session: requests.Session, url: str, params: dict | None = None) -> dict:
    """Raw GET — always returns the full response dict regardless of status."""
    resp = session.get(url, params=params)
    try:
        body = resp.json()
    except Exception:
        body = {"_raw": resp.text}
    body["_http_status"] = resp.status_code
    body["_url"] = url
    return body


def _get_paginated(session: requests.Session, url: str, params: dict | None = None) -> list[dict]:
    results: list[dict] = []
    next_url: str | None = url
    first = True
    while next_url:
        resp = session.get(next_url, params=params if first else None)
        first = False
        if not resp.ok:
            try:
                body = resp.json()
            except Exception:
                body = {"_raw": resp.text}
            body["_http_status"] = resp.status_code
            return [body]
        data = resp.json()
        results.extend(data.get("value", []))
        next_url = data.get("@odata.nextLink")
    return results


def _classify_tenant(org: dict, skus: list[dict]) -> str:
    valid_skus = [s for s in skus if isinstance(s, dict) and "_http_status" not in s]
    sku_parts = {s.get("skuPartNumber", "") for s in valid_skus}

    if sku_parts & _DEVELOPER_SKUS:
        return "Developer"

    has_plans = bool(org.get("assignedPlans") or org.get("provisionedPlans"))
    if not valid_skus and not has_plans:
        return "Free/Unlicensed Azure AD"

    if not valid_skus:
        return "Unknown (no SKU data)"

    all_trial = all(
        s.get("capabilityStatus") in ("Warning", "Suspended")
        for s in valid_skus
    )
    if all_trial:
        return "Trial / Suspended"

    return "Commercial"


def _find_plan(assigned_plans: list[dict], plan_id: str) -> dict | None:
    return next(
        (p for p in assigned_plans if p.get("servicePlanId") == plan_id and p.get("capabilityStatus") == "Enabled"),
        None,
    )


def run_diagnostic() -> None:
    OUTPUT.mkdir(exist_ok=True)
    print(_PRIVACY_WARNING)
    print("Starting Device Code authentication...")
    token = acquire_token()
    print("Authenticated. Running diagnostic...\n")

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token['access_token']}",
        "Content-Type": "application/json",
    })

    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "privacy_notice": (
            "May contain tenant-specific metadata. Written locally only; never "
            "transmitted to Cloud Locksmith. No tokens/credentials are included. "
            "Review and redact before sharing publicly."
        ),
        "sections": {},
    }

    # ── 1. Organization ────────────────────────────────────────────────────────
    print("[1/4] Fetching organization details...")
    org_resp = _get(session, f"{GRAPH_BASE}/organization")
    orgs = org_resp.get("value", [])
    org = orgs[0] if orgs else {}
    report["sections"]["organization"] = {
        "http_status": org_resp.get("_http_status"),
        "display_name": org.get("displayName"),
        "tenant_id": org.get("id"),
        "country": org.get("countryLetterCode"),
        "created_date_time": org.get("createdDateTime"),
        "assigned_plans_raw": org.get("assignedPlans", []),
        "provisioned_plans_raw": org.get("provisionedPlans", []),
    }

    assigned_plans: list[dict] = org.get("assignedPlans", [])
    entra_p1 = _find_plan(assigned_plans, _ENTRA_P1_PLAN_ID)
    entra_p2 = _find_plan(assigned_plans, _ENTRA_P2_PLAN_ID)
    report["sections"]["organization"]["entra_p1_enabled"] = entra_p1 is not None
    report["sections"]["organization"]["entra_p2_enabled"] = entra_p2 is not None
    report["sections"]["organization"]["entra_p1_plan_detail"] = entra_p1
    report["sections"]["organization"]["entra_p2_plan_detail"] = entra_p2

    # ── 2. Subscribed SKUs ─────────────────────────────────────────────────────
    print("[2/4] Fetching subscribed SKUs...")
    skus_raw = _get_paginated(session, f"{GRAPH_BASE}/subscribedSkus")
    sku_summary = []
    for s in skus_raw:
        if "_http_status" in s:
            sku_summary.append({"error": s})
        else:
            sku_summary.append({
                "skuPartNumber": s.get("skuPartNumber"),
                "skuId": s.get("skuId"),
                "capabilityStatus": s.get("capabilityStatus"),
                "consumedUnits": s.get("consumedUnits"),
                "prepaidUnits": s.get("prepaidUnits"),
            })
    report["sections"]["subscribed_skus"] = {
        "count": len([s for s in sku_summary if "error" not in s]),
        "skus": sku_summary,
    }

    tenant_type = _classify_tenant(org, skus_raw)
    report["sections"]["tenant_classification"] = {
        "tenant_type": tenant_type,
        "classification_basis": (
            "SKU part numbers and capability status evaluated against known developer/trial identifiers."
        ),
    }

    # ── 3. MFA Endpoint — full raw response ────────────────────────────────────
    print("[3/4] Probing MFA registration endpoint (capturing full error body)...")
    mfa_url = f"{GRAPH_BASE}/reports/authenticationMethods/userRegistrationDetails"
    mfa_resp_raw = session.get(mfa_url, params={"$top": "1"})
    try:
        mfa_body = mfa_resp_raw.json()
    except Exception:
        mfa_body = {"_raw": mfa_resp_raw.text}

    mfa_error = mfa_body.get("error", {})
    report["sections"]["mfa_endpoint"] = {
        "url": mfa_url,
        "http_status": mfa_resp_raw.status_code,
        "success": mfa_resp_raw.ok,
        "full_response_body": mfa_body,
        "graph_error_code": mfa_error.get("code"),
        "graph_error_message": mfa_error.get("message"),
        "graph_inner_error": mfa_error.get("innerError"),
        "record_count_if_success": len(mfa_body.get("value", [])) if mfa_resp_raw.ok else None,
    }

    # ── 4. Assigned Plans ──────────────────────────────────────────────────────
    print("[4/4] Summarizing assigned plans...")
    enabled_plans = [
        {"servicePlanId": p.get("servicePlanId"), "service": p.get("service"), "capabilityStatus": p.get("capabilityStatus")}
        for p in assigned_plans
        if p.get("capabilityStatus") == "Enabled"
    ]
    report["sections"]["assigned_plans"] = {
        "total": len(assigned_plans),
        "enabled_count": len(enabled_plans),
        "enabled_plans": enabled_plans,
    }

    # ── Write outputs ──────────────────────────────────────────────────────────
    report = _scrub(report)  # defense-in-depth: never write credential-like fields
    json_path = OUTPUT / "diagnostic_report.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    md_path = OUTPUT / "diagnostic_report.md"
    _write_markdown(report, md_path)

    print(f"\n  ✓ JSON → {json_path}")
    print(f"  ✓ MD   → {md_path}")
    _print_summary(report)


def _print_summary(report: dict) -> None:
    s = report["sections"]
    org = s.get("organization", {})
    mfa = s.get("mfa_endpoint", {})
    skus = s.get("subscribed_skus", {})
    tc = s.get("tenant_classification", {})

    print("\n" + "=" * 62)
    print("  DIAGNOSTIC SUMMARY")
    print("=" * 62)
    print(f"  Tenant         : {org.get('display_name')} ({org.get('tenant_id')})")
    print(f"  Tenant Type    : {tc.get('tenant_type')}")
    print(f"  Country        : {org.get('country')}")
    print(f"  Entra P1       : {'YES' if org.get('entra_p1_enabled') else 'NO'}")
    print(f"  Entra P2       : {'YES' if org.get('entra_p2_enabled') else 'NO'}")
    print(f"  SKU Count      : {skus.get('count')}")
    print(f"\n  MFA Endpoint   : HTTP {mfa.get('http_status')} ({'OK' if mfa.get('success') else 'FAILED'})")
    if not mfa.get("success"):
        print(f"  Error Code     : {mfa.get('graph_error_code')}")
        print(f"  Error Message  : {mfa.get('graph_error_message')}")
    else:
        print(f"  Records Found  : {mfa.get('record_count_if_success')}")
    print("=" * 62 + "\n")


def _write_markdown(report: dict, path: pathlib.Path) -> None:
    s = report["sections"]
    org = s.get("organization", {})
    mfa = s.get("mfa_endpoint", {})
    skus = s.get("subscribed_skus", {})
    tc = s.get("tenant_classification", {})
    plans = s.get("assigned_plans", {})

    lines = [
        "# Cloud Locksmith — Live Graph Diagnostic Report",
        f"\nGenerated: {report['generated_at']}\n",
        "---\n",
        "## Tenant Classification\n",
        "| Field | Value |",
        "|---|---|",
        f"| Display Name | {org.get('display_name')} |",
        f"| Tenant ID | `{org.get('tenant_id')}` |",
        f"| Country | {org.get('country')} |",
        f"| Created | {org.get('created_date_time')} |",
        f"| **Tenant Type** | **{tc.get('tenant_type')}** |",
        f"| Entra ID P1 | {'✓ Enabled' if org.get('entra_p1_enabled') else '✗ Not found'} |",
        f"| Entra ID P2 | {'✓ Enabled' if org.get('entra_p2_enabled') else '✗ Not found'} |",
        "",
        "## Subscription Inventory\n",
    ]
    sku_list = [s for s in skus.get("skus", []) if "error" not in s]
    if sku_list:
        lines += ["| SKU | Status | Consumed | Prepaid (Enabled) |", "|---|---|---|---|"]
        for s in sku_list:
            pu = s.get("prepaidUnits") or {}
            lines.append(
                f"| {s.get('skuPartNumber')} | {s.get('capabilityStatus')} "
                f"| {s.get('consumedUnits')} | {pu.get('enabled')} |"
            )
    else:
        lines.append("_No commercial SKUs found._")
    lines.append("")

    lines += [
        "## MFA Endpoint Probe\n",
        f"**Endpoint:** `GET {mfa.get('url')}`\n",
        f"**HTTP Status:** {mfa.get('http_status')} ({'Success' if mfa.get('success') else 'Failed'})\n",
    ]
    if not mfa.get("success"):
        lines += [
            f"**Graph Error Code:** `{mfa.get('graph_error_code')}`\n",
            f"**Graph Error Message:** {mfa.get('graph_error_message')}\n",
        ]
        inner = mfa.get("graph_inner_error")
        if inner:
            lines += [f"**Inner Error:**\n```json\n{json.dumps(inner, indent=2)}\n```\n"]
        lines += [
            "**Full Response Body:**",
            "```json",
            json.dumps(mfa.get("full_response_body"), indent=2, default=str),
            "```\n",
        ]
    else:
        lines.append(f"**Records returned:** {mfa.get('record_count_if_success')}\n")

    lines += [
        "## Assigned Plans (Enabled)\n",
        f"Total assigned plans: {plans.get('total')} — Enabled: {plans.get('enabled_count')}\n",
        "| Service Plan ID | Service | Status |",
        "|---|---|---|",
    ]
    for p in plans.get("enabled_plans", []):
        lines.append(f"| `{p.get('servicePlanId')}` | {p.get('service')} | {p.get('capabilityStatus')} |")
    lines += ["", "---", "_Internal diagnostic utility. Not part of the assessment CLI._"]

    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    run_diagnostic()
