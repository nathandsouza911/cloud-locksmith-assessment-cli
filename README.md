# Cloud Locksmith Assessment CLI

A fast, local, read-only Microsoft 365 security posture assessment you can run in a few minutes.

It authenticates with Microsoft Device Code flow, reads a focused set of identity and tenant-policy signals through the Microsoft Graph API, and produces a terminal summary plus Markdown, PDF, and JSON reports. Everything runs on your machine.

**Local · Read-only · No SaaS account · No remediation · Transparent Graph permissions.**

---

## Example result

```
IDENTITY SECURITY POSTURE SCORE

  Grade: FAIR  —  Score: 9/14 (64%)  —  7 of 7 controls evaluated

  Control                       Status       Detail
  Privileged MFA Coverage       ✓ PASS       100% of privileged users have MFA registered
  Global Admin Count            ⚠ WARNING    4 Global Admins (4–5; consider reducing)
  Tenant MFA Coverage           ⚠ WARNING    82% tenant MFA coverage (≥90% to PASS)
  Baseline Access Enforcement   ✓ PASS       3 enabled Conditional Access policy(ies)
  User App Consent              ⚠ WARNING    Users can consent to third-party apps
  Dormant Enabled Accounts      ✗ FAIL       6 dormant enabled accounts — unused sign-in surface
  Stale Guest Access            ⚠ WARNING    5 stale guest account(s) — review access
```

Only genuine identity/access security signals are scored. Cost/cleanup facts — unassigned licenses, disabled-but-licensed accounts, guest *inventory* — are reported separately and never move the score.

See the full [sample Markdown report](docs/samples/sample_assessment_report.md), [sample PDF](docs/samples/sample_assessment_report.pdf), and [sample JSON](docs/samples/sample_assessment_results.json) — all generated from **synthetic data**, so you can inspect the output before granting any permissions.

---

## Trust promises

- **Local.** All processing happens on your machine. No assessment data is transmitted to Cloud Locksmith or any third party.
- **Read-only.** Every Graph call is a `GET`. The requested scopes are all `*.Read.All`. The tool cannot write, delete, or modify anything in your tenant.
- **No SaaS account.** You do not sign up for anything to use this CLI.
- **No remediation.** The CLI detects and explains. It never changes configuration, removes licenses, or touches policies.
- **Transparent permissions.** The exact scopes and every endpoint called are documented in [docs/PERMISSIONS.md](docs/PERMISSIONS.md).
- **No token persistence.** Access tokens are held in memory and discarded when the process exits.

---

## Quick start

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/getting-started/installation/), and an Azure App Registration (see [Setup](#setup)).

```bash
git clone https://github.com/nathandsouza911/cloud-locksmith-assessment-cli
cd cloud-locksmith-assessment-cli
uv sync

# Set the client ID of your Azure App Registration
export CLOUDLOCKSMITH_CLIENT_ID="your-app-client-id"      # macOS/Linux
# $env:CLOUDLOCKSMITH_CLIENT_ID = "your-app-client-id"    # PowerShell

uv run cloudlocksmith assess
```

Or pass the client ID on the command line (takes precedence over the env var):

```bash
uv run cloudlocksmith assess --client-id "your-app-client-id"
```

You will be shown a URL and a one-time code. Open the URL, enter the code, and sign in. The assessment then runs automatically (typically 30–90 seconds).

> **One-command execution once published to PyPI.** The package is PyPI-ready. After publication, `uvx cloudlocksmith assess` (with `CLOUDLOCKSMITH_CLIENT_ID` set) will run it without a manual clone. This repository does not publish anything on your behalf.

---

## What it checks

Twelve read-only checks, plus a derived **Identity Security Posture Score** built from the seven that are genuine security signals. Cost/hygiene and informational checks are reported but **do not affect the score** — a fact is not a failure.

| # | Check | Classification | Scored? | Notes |
|---|---|---|---|---|
| 1 | Privileged-user MFA registration coverage | Security control | ✅ | Requires Entra ID P1/P2 |
| 2 | Global Administrator count | Security control | ✅ | — |
| 3 | Tenant-wide MFA registration coverage | Security control | ✅ | Requires Entra ID P1/P2 |
| 4 | Baseline access enforcement (Security Defaults or CA) | Security control | ✅ | Requires `Policy.Read.All` |
| 5 | User app-consent policy | Security control | ✅ | Requires `Policy.Read.All` |
| 6 | Dormant **enabled** licensed accounts (90+ days) | Security/hygiene | ✅ | Requires Entra ID P1/P2 |
| 7 | Stale guest access (90+ days) | Security/hygiene | ✅ | Requires Entra ID P1/P2 |
| 8 | Privileged role holders (high-impact roles) | Informational | — | — |
| 9 | Conditional Access policy inventory | Informational | — | Requires `Policy.Read.All` + P1/P2 |
| 10 | Guest / external account inventory | Informational | — | — |
| 11 | Disabled but still-licensed accounts | Cost/hygiene | — | Reclaimable license, not a sign-in risk |
| 12 | License optimization (potentially reclaimable seats) | Cost | — | Estimates only — see below |

Checks that cannot run in a given tenant (for example, MFA reporting without Entra ID P1/P2) are reported as **SKIPPED** with a clear reason, and the score is computed only over what could be evaluated. See [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for the exact classification, thresholds, and scoring, and [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) for what the tool does not do.

---

## How it compares to ScubaGear and Maester

This CLI is **not** more comprehensive than, more secure than, or a replacement for deep assessment/testing frameworks such as [ScubaGear](https://github.com/cisagov/ScubaGear) or [Maester](https://maester.dev). Those are excellent, thorough tools with large, configurable, standards-mapped control sets and (for Maester) a Pester-based testing workflow. They evaluate far more than this CLI does.

Cloud Locksmith Assessment CLI aims to be a complementary, narrower tool:

- **Fast and low-friction** — one command, minimal configuration.
- **Local and read-only** — device-code sign-in, no infrastructure to stand up.
- **Understandable** — plain-language findings and executive-friendly PDF/Markdown output.
- **Right-sized for MSPs and smaller organizations** that want a quick posture snapshot they can hand to a non-specialist stakeholder.

If you need exhaustive, standards-mapped coverage (e.g. CISA SCuBA baselines) or a scriptable test framework, use ScubaGear or Maester. Many teams will reasonably use both: this CLI for a quick recurring snapshot, and a deeper framework for detailed audits.

---

## Permissions and Graph endpoints

The tool requests five **read-only delegated** scopes, all requiring admin consent: `Directory.Read.All`, `Reports.Read.All`, `Organization.Read.All`, `AuditLog.Read.All`, and `Policy.Read.All`.

Full details — every scope, every endpoint, and what each reads — are in **[docs/PERMISSIONS.md](docs/PERMISSIONS.md)**.

### Who must consent vs. who can run

- **Granting admin consent** to the scopes requires a **Global Administrator** (or Privileged Role Administrator).
- **Running the assessment after consent has been granted** only requires read access to the endpoints above. Because every scope is read-only and every call is a `GET`, the tool cannot change your tenant regardless of who signs in. Per Microsoft's role documentation, a **Global Reader** has read access to all of these endpoints, so you can model least privilege: consent once with a privileged account, then run day-to-day as Global Reader.

> **How to confirm in your own tenant:** the tool self-checks at runtime. If the signed-in role lacks access to a specific read, that control is reported **SKIPPED with the exact reason** (e.g. an authorization error) — nothing fails silently and nothing else is affected. To validate least privilege before a broad rollout, run `cloudlocksmith assess` once with a Global Reader account and confirm no control reports a permission/authorization SKIP. The per-endpoint expectations are in the [run-role matrix](docs/PERMISSIONS.md#run-role-matrix).

---

## Methodology and scoring

The **Identity Security Posture Score** rolls up the seven scored identity controls into a 0–100% ratio and a grade of **Weak / Fair / Good / Strong**. It is a transparent point ratio (points earned ÷ points achievable across evaluated controls), not a predictive model — full formula, thresholds, and limitations are in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

> The Identity Security Posture Score reflects only the Microsoft 365 identity/access controls this tool could evaluate. **It is not a measure of overall cybersecurity maturity, breach likelihood, compliance, or cyber-insurance eligibility.**

License figures are **estimates** derived from approximate public list prices (or a pricing file you supply). "Potentially reclaimable" seats are unassigned paid seats — not proven waste, and never a recommendation to remove a license automatically. See [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

---

## Automation / MSP usage

The CLI is scriptable without turning into a fleet platform.

- **Stable JSON + schema versioning** — the JSON output carries a `schema_version`; see [docs/SCHEMA.md](docs/SCHEMA.md).
- **Documented exit codes** — success-with-findings is *not* treated as a failure by default; use `--strict` for CI. See [docs/EXIT_CODES.md](docs/EXIT_CODES.md).
- **Per-tenant runs** — point the tool at different app registrations and output directories:

```bash
for tenant in contoso fabrikam; do
  CLOUDLOCKSMITH_CLIENT_ID="${tenant}_client_id" \
    uv run cloudlocksmith assess --output-dir "reports/${tenant}" --quiet
done
```

Aggregating those outputs across tenants, over time, with alerting is intentionally **out of scope** for the free CLI — that is what the paid platform is for (see below).

---

## What this tool explicitly does NOT do

- Does not modify any Microsoft 365 configuration.
- Does not remove or reassign licenses.
- Does not create or modify Conditional Access or any other policy.
- Does not perform any remediation, verification, or rollback.
- Does not store authentication tokens to disk.
- Does not transmit assessment data to Cloud Locksmith or any external service.
- Does not aggregate across tenants, schedule scans, or provide historical dashboards.

---

## Relationship to the paid Cloud Locksmith platform

This CLI is a **point-in-time, local, read-only** detection and explanation tool. The commercial **Cloud Locksmith** platform is a separate, paid service for teams that need to *operate* posture over time rather than run it by hand:

| Cloud Locksmith Assessment CLI (free, open source) | Cloud Locksmith platform (paid) |
|---|---|
| Point-in-time, local, read-only | Scheduled posture scanning |
| Detection + explanation | Historical posture tracking |
| Manual remediation guidance | Alerting |
| Exports (JSON/MD/PDF) | Multi-tenant fleet operations |
| Single tenant, run by hand | Controlled remediation with verification and rollback, evidence history |

There is one quiet, factual pointer to the platform in the CLI output. No upgrade nagging.

---

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A Microsoft Azure App Registration with device-code (public client) flow enabled

### Azure App Registration

1. **Azure Portal → Microsoft Entra ID → App registrations → New registration**
2. Name: `Cloud Locksmith Assessment CLI`
3. Supported account types: **Accounts in any organizational directory** (or single-tenant if you prefer)
4. No redirect URI needed
5. Under **Authentication**, enable **Allow public client flows**
6. Under **API permissions**, add the five delegated permissions listed in [docs/PERMISSIONS.md](docs/PERMISSIONS.md) and **grant admin consent**
7. Copy the **Application (client) ID** and set it as `CLOUDLOCKSMITH_CLIENT_ID`

> A future release may offer a Cloud Locksmith-published multi-tenant application so no app registration is needed. The design and open questions are documented in [docs/AUTH_RECOMMENDATION.md](docs/AUTH_RECOMMENDATION.md).

### Optional: custom license pricing

Point `CLOUDLOCKSMITH_PRICING_FILE` at a JSON file mapping `skuPartNumber` → annual USD price to override the built-in approximate list prices:

```json
{ "SPE_E3": 396.00, "CONTOSO_CUSTOM": 120.00 }
```

---

## Developer install and tests

```bash
uv sync
uv run pytest tests/ -v
uv run python scripts/generate_samples.py   # regenerate docs/samples
```

Packaging is PyPI-ready (`uv build` produces a working wheel whose `cloudlocksmith` entry point runs standalone). A standalone Windows `.exe` is a documented follow-up — see [docs/AUTH_RECOMMENDATION.md](docs/AUTH_RECOMMENDATION.md) and the launch notes.

---

## Free and open-source commitment

The local assessment capabilities in this CLI are free and open source and are intended to stay that way. Cloud Locksmith may add further free assessment capabilities over time. We do not intend to remove existing open-source capabilities from this CLI simply to move them behind the paid platform. (This is a statement of intent, not a perpetual warranty for every individual feature.)

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [docs/PRIVACY.md](docs/PRIVACY.md), and [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) — we document limitations openly rather than hide them.

---

## About Cloud Locksmith

This CLI is published and maintained by [Cloud Locksmith](https://cloudlocksmith.co). It performs a lightweight, point-in-time evaluation of a focused set of Microsoft 365 security controls for administrators and MSPs who want a quick, local view of tenant posture.

## License

MIT — see [LICENSE](LICENSE).
