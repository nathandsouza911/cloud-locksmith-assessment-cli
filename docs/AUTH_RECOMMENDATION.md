# Authentication design and the shared-client-ID decision

This document records the authentication model shipped at launch, and a written recommendation for a possible future change that requires a business/security decision. It exists so that decision can be made deliberately rather than by accident.

## What ships today (launch)

- **Bring-your-own App Registration.** The user creates an Azure App Registration, enables public-client (device-code) flows, adds the five read-only delegated scopes, grants admin consent, and sets `CLOUDLOCKSMITH_CLIENT_ID`.
- **No secrets.** Device Code is a public-client flow. There is no client secret anywhere in this tool, and none should ever be added.
- **No embedded client ID.** The tool ships with no default application ID. This keeps trust and ownership entirely with the user's own tenant.

This is the most transparent and lowest-risk model for an initial open-source release: a skeptical administrator can read the code, create their own app, and see exactly what is requested.

## The friction

BYO App Registration is the single biggest onboarding step. The ideal UX is:

```
run command → Microsoft device login → consent → assessment
```

with no portal work. That requires a **Cloud Locksmith-owned, multi-tenant, public-client application** whose Application (client) ID is shipped as the default (with BYO preserved as an override).

## Why this is a business/security decision, not a code change

Embedding a shared multi-tenant client ID is technically simple but carries real, non-code consequences that must be owned by Cloud Locksmith, not decided implicitly in a PR:

1. **Publisher verification.** For a multi-tenant app that other organizations consent to, Microsoft **publisher verification** (verified MPN/Partner ID) is effectively required for a trustworthy consent experience and to avoid unverified-publisher warnings. This is an organizational onboarding step.
2. **Consent screen identity.** Every tenant that runs the tool will see *Cloud Locksmith's* app name and publisher on the admin-consent screen. That is a brand and trust commitment.
3. **Admin-consent behavior.** The five scopes require admin consent. A shared app does not remove the need for a Global Admin to consent once per tenant; it only removes the app-registration step.
4. **Operational ownership.** Cloud Locksmith would own the lifecycle of that app object (secret-less, but still: name, redirect config, permission list, incident response if the app is abused or flagged).
5. **Reputational risk.** A single shared identifier used across many tenants concentrates reputation. If the app is ever flagged, every user is affected at once.
6. **Delegated-only, read-only must be preserved.** The shared app must request exactly the same read-only delegated scopes. It must never drift toward application permissions or write scopes.

## Recommendation

1. **Launch BYO-only** (current state). It is defensible, transparent, and safe.
2. **Treat the shared client ID as an approved-in-principle follow-up** gated on:
   - completing Microsoft **publisher verification** for the Cloud Locksmith tenant,
   - a decision on the app's display name/branding shown at consent,
   - a security sign-off that the app is delegated-only, read-only, secret-less, and monitored.
3. **When implemented,** ship it as the *default* client ID with `CLOUDLOCKSMITH_CLIENT_ID` remaining a first-class override for privacy-conscious/BYO users. Never fabricate or hardcode a placeholder ID before the real app exists.

## Standalone Windows executable (related follow-up)

A single-file `.exe` (e.g. via PyInstaller) would further reduce friction for administrators without Python. It is feasible but not free of risk: bundling `reportlab` and `msal`, code-signing to avoid SmartScreen warnings, and a larger artifact to maintain. Recommended as a **follow-up**, not part of the initial release. The packaging is already PyPI-ready, which covers the `uvx`/`pipx` audience with no extra engineering.
