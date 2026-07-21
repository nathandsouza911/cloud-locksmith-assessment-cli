# Microsoft 365 Security Assessment

## Identity Security Posture Score

**Grade: Good** — Score: 6/6 (100%) — 3 of 7 controls evaluated

> Skipped: Privileged MFA Coverage, Tenant MFA Coverage, Dormant Enabled Accounts, Stale Guest Access

> Grade capped at Good because Privileged MFA Coverage could not be evaluated.

| Control | Status | Detail |
|---|---|---|
| Privileged MFA Coverage | SKIPPED | Requires Microsoft Entra ID P1 or P2 licensing. |
| Global Admin Count | PASS | 2 Global Admin(s) (≤3 recommended) |
| Tenant MFA Coverage | SKIPPED | Requires Microsoft Entra ID P1 or P2 licensing. |
| Baseline Access Enforcement | PASS | Security Defaults enabled |
| User App Consent | PASS | User app consent restricted to administrators |
| Dormant Enabled Accounts | SKIPPED | Sign-in activity unavailable for this tenant. |
| Stale Guest Access | SKIPPED | Sign-in activity unavailable for this tenant. |

*Identity Security Posture Score reflects only the Microsoft 365 identity/access controls this tool could evaluate. It is not a measure of overall cybersecurity maturity, breach likelihood, compliance, or insurance eligibility. See docs/METHODOLOGY.md.*

## Identity & Privileged Access

### Global Administrators

- Count: 2
- Risk Level: Good

### Privileged MFA Coverage

**Status:** SKIPPED
**Reason:** Requires Microsoft Entra ID P1 or P2 licensing.

### Tenant-wide MFA Coverage

**Status:** SKIPPED
**Reason:** Requires Microsoft Entra ID P1 or P2 licensing.

### Privileged Role Holders

- Distinct privileged users: 2

| Role | Members |
|---|---|
| Global Administrator | 2 |

## External / Guest Collaboration

### Guest Accounts

- Total guests: 2

### Stale Guest Accounts (90+ days inactive)

**Status:** SKIPPED
**Reason:** Sign-in activity unavailable for this tenant.

## Tenant Policy

### Security Defaults

- Enabled: Yes

### Conditional Access

**Status:** SKIPPED
**Reason:** Conditional Access inventory requires Policy.Read.All admin consent and Microsoft Entra ID P1 or P2 licensing.

### User App Consent

- Users can consent to apps: No
- User app consent is restricted to administrators (recommended).

## Account Hygiene (Cost / Cleanup)

_These are cost/cleanup observations. Dormant **enabled** accounts are also scored above as an identity signal; disabled accounts cannot sign in and are reported here for reclaimable licensing only — they do not affect the posture score._

### Dormant Enabled Licensed Accounts (90+ days inactive)

**Status:** SKIPPED
**Reason:** Sign-in activity unavailable for this tenant.

### Disabled but Still-Licensed Accounts

- Total: 1 (reclaimable license; not a sign-in risk)

## License Optimization

| Metric | Value |
|---|---|
| Active (paid) units | 30 |
| Consumed units | 28 |
| Potentially reclaimable seats | 2 |
| Est. reclaimable spend (monthly) | $25.00 |
| Est. reclaimable spend (annual) | $300.00 |
| Priced reclaimable seats | 2 |
| Unpriced reclaimable seats | 0 |

> Estimates from Microsoft public list prices (approximate). Unassigned seats are *potentially reclaimable*, not proven waste, and should be reviewed before any change.

## Assessment Metadata

| Field | Value |
|---|---|
| Generated | 2026-01-15T09:00:00+00:00 |
| Schema Version | 2.0.0 |
| Authentication | Microsoft Device Code Flow |
| Permissions | Read-only delegated |
| Data Handling | No assessment data was transmitted to Cloud Locksmith. |
| Token Handling | Authentication tokens were discarded after assessment completion. |

---
*Generated locally. No data sent to Cloud Locksmith. Point-in-time assessment only — no changes were made to your tenant.*