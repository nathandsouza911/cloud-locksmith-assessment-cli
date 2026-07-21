# Methodology and scoring

This document describes exactly how each check is classified, how the Identity Security Posture Score is computed, and the known limitations. Nothing here is a black box; a technical reader should be able to reproduce the conceptual logic.

## Guiding principle: a fact is not a failure

The tool separates **scored security signals** from **cost/hygiene observations** and **informational context**. Having guests, having Conditional Access policies, or having unassigned licenses is not inherently a security failure, so those facts never move the score.

## Check classification

| Check | Classification | Scored? | Rationale |
|---|---|---|---|
| Privileged MFA Coverage | Security control | Yes (required) | Unprotected privileged accounts are the highest-value identity risk. |
| Global Admin Count | Security control | Yes (required) | Excess standing Global Admin access widens blast radius (MS/CIS guidance: minimize). |
| Tenant MFA Coverage | Security control | Yes | Registration coverage is a real authentication-hardening signal. |
| Baseline Access Enforcement | Security control | Yes | Either Security Defaults or an enabled Conditional Access policy indicates baseline enforcement exists. |
| User App Consent | Security control | Yes | User-consent-to-apps enables illicit consent (OAuth phishing); admin-restricted is the hardened state. |
| Dormant Enabled Accounts | Security/hygiene | Yes | An **enabled**, licensed account unused 90d+ is live, unmonitored sign-in surface. |
| Stale Guest Access | Security/hygiene | Yes | External accounts with no recent sign-in are unreviewed standing access. |
| Privileged Role Holders | Informational | No | Role inventory is context; a fair "how many is too many" threshold is org-specific. |
| Guest Account Inventory | Informational | No | Having guests is normal collaboration, not a failure. |
| Conditional Access Inventory | Informational (feeds Baseline Access Enforcement) | No (indirectly) | Policy *presence* is neither good nor bad on its own; it informs the baseline control. |
| Disabled but Still-Licensed | Cost/hygiene | No | A disabled account cannot authenticate — this is reclaimable spend, not a sign-in risk. |
| License Optimization | Cost/hygiene | No | Unassigned seats are a cost observation, not a security failure. |

"Dormant" and "stale" use a **90-day** last-sign-in threshold; an account with no recorded sign-in at all is counted. Dormant is measured on **enabled** accounts only, which also prevents overlap with the disabled-account count.

## Scored control thresholds

| Control | PASS (2) | WARNING (1) | FAIL (0) |
|---|---|---|---|
| Privileged MFA Coverage | ≥95% | ≥80% | <80% |
| Global Admin Count | ≤3 | 4–5 | ≥6 |
| Tenant MFA Coverage | ≥90% | ≥70% | <70% |
| Baseline Access Enforcement | Security Defaults on, or ≥1 enabled CA policy | SD off and CA unreadable | SD off and 0 enabled CA policies |
| User App Consent | Restricted to admins | Users can self-consent | — |
| Dormant Enabled Accounts | 0 | 1–5 | >5 |
| Stale Guest Access | 0 | 1–5 | >5 |

## Identity Security Posture Score

```
score_pct = (points earned across evaluated controls)
            / (2 × number of evaluated controls) × 100
```

Only the seven scored controls above contribute. SKIPPED controls are excluded from **both** the numerator and the denominator, so a tenant is never penalized for data it cannot expose (for example, no Entra ID P1/P2). Unavailable or forbidden Graph data becomes **SKIPPED with a reason** — never a silent PASS or FAIL.

Grade bands:

| Grade | Score |
|---|---|
| Strong | ≥ 90% |
| Good | ≥ 70% |
| Fair | ≥ 40% |
| Weak | < 40% |

### Weighting and single-signal distortion

All scored controls carry equal weight (max 2 points each). With up to seven scored controls, no single control can swing the result by more than ~14 percentage points, so one weak signal cannot by itself collapse the grade. The report always shows "N of M controls evaluated" so a grade computed over fewer controls can be read with appropriate caution.

### Grade cap for missing required controls

Two controls are **required** for full confidence: **Privileged MFA Coverage** and **Global Admin Count**. If one is SKIPPED, the grade is capped at **Good**; if both are SKIPPED, it is capped at **Fair**. The cap can only lower a grade, never raise it, and the report states the reason.

### What the score is — and is not

The score answers a narrow question: *based on the Microsoft 365 identity/access controls this tool was able to evaluate, how does the observed posture look?*

It is **not** a measure of:

- overall organizational cybersecurity maturity,
- breach likelihood,
- cyber-insurance eligibility or an underwriting outcome,
- compliance certification.

It excludes entire domains (endpoint, network, data protection, email security, application security, physical, process). Treat it as a prioritization aid, not a verdict.

### Why a 0–100 number at all

The percentage is a transparent ratio of points earned to points achievable across evaluated controls — not a statistical or predictive model, and it implies no calibrated precision. If you prefer to ignore the number, the per-control PASS/WARNING/FAIL table stands on its own; the grade is only a convenience roll-up of that table.

## License optimization

- **Potentially reclaimable seats** = paid (`prepaidUnits.enabled`) minus assigned (`consumedUnits`) per SKU, summed. These are *unassigned* seats — **potentially reclaimable, not proven waste**. A deliberate buffer of spare seats is legitimate.
- **Estimated reclaimable spend** prices only the reclaimable seats of SKUs present in the pricing map. Unknown SKUs are counted as reclaimable seats but **excluded** from the dollar figure (never priced as $0 "waste"), and are listed by name. A SKU explicitly priced at $0 (e.g. free plans) counts as *priced* at $0, not unknown.
- The unassigned-seat pool and the "disabled but still-licensed" count are **separate** reclaimable pools (unassigned = never consumed; disabled-licensed = consumed by a disabled account). They are reported separately and never summed, to avoid double-counting.
- Pricing comes from an approximate public list-price map ([`pricing/sku_pricing.py`](../pricing/sku_pricing.py)) or a user-supplied override file (`CLOUDLOCKSMITH_PRICING_FILE`), which takes precedence. These are **estimates for directional sizing only** — not authoritative billing data, and not tied to your EA/CSP/contract pricing, which may differ materially.
- The CLI never recommends removing a specific license automatically. Reclaimable counts are a starting point for human review.
