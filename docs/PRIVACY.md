# Privacy

The Cloud Locksmith Assessment CLI is designed so that **your tenant data never leaves your machine.**

## What the tool reads

Only the read-only Graph endpoints documented in [PERMISSIONS.md](PERMISSIONS.md). In summary: user and guest directory objects, role memberships, MFA registration status, last-sign-in timestamps, subscription/SKU inventory, and tenant policy state (Security Defaults, Conditional Access names/states, user-consent setting).

## What the tool does with it

- All analysis runs locally, in the CLI process.
- Results are written **only** to the local output directory you choose (default `output/`, which is gitignored).
- **No assessment data is transmitted to Cloud Locksmith or any third party.** The tool makes network calls only to Microsoft's `login.microsoftonline.com` (sign-in) and `graph.microsoft.com` (the reads above).

## Authentication tokens

- Tokens are obtained via Microsoft Device Code flow and held **in memory only**.
- Tokens are **not persisted to disk** and are discarded when the process exits.
- The tool handles no passwords; you authenticate directly with Microsoft in your browser.

## What ends up in the reports

Reports contain aggregate counts and, for a few controls, up to **three example accounts** (display name and UPN) to make findings actionable — for example, the first three dormant licensed users. If you intend to share a report externally, review it first. The output directory is gitignored by default to avoid accidental commits.

## Telemetry

There is **no telemetry**. The tool does not phone home, count runs, or report usage.

## Your responsibilities

- Store generated reports appropriately — they describe your tenant's security posture.
- If you supply a custom pricing file, it stays local and is only read, never transmitted.
