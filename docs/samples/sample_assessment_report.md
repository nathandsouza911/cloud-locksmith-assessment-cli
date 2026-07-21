# Microsoft 365 Security Assessment

## Identity Security Posture Score

**Grade: Fair** — Score: 8/14 (57%) — 7 of 7 controls evaluated

| Control | Status | Detail |
|---|---|---|
| Privileged MFA Coverage | PASS | 100% of privileged users have MFA registered |
| Global Admin Count | WARNING | 4 Global Admins (4–5; consider reducing) |
| Tenant MFA Coverage | WARNING | 82% tenant MFA coverage (≥90% to PASS) |
| Baseline Access Enforcement | PASS | 3 enabled Conditional Access policy(ies) |
| User App Consent | WARNING | Users can consent to third-party apps (restrict to admins) |
| Dormant Enabled Accounts | FAIL | 6 dormant enabled accounts — unused sign-in surface |
| Stale Guest Access | WARNING | 5 stale guest account(s) — review access |

*Identity Security Posture Score reflects only the Microsoft 365 identity/access controls this tool could evaluate. It is not a measure of overall cybersecurity maturity, breach likelihood, compliance, or insurance eligibility. See docs/METHODOLOGY.md.*

## Identity & Privileged Access

### Global Administrators

- Count: 4
- Risk Level: Moderate

### Privileged MFA Coverage

- Privileged Users: 6
- MFA Registered: 6
- Coverage: 100.0%

### Tenant-wide MFA Coverage

- Users Reported: 150
- MFA Registered: 123
- Coverage: 82.0%

### Privileged Role Holders

- Distinct privileged users: 7

| Role | Members |
|---|---|
| Global Administrator | 4 |
| Security Administrator | 2 |
| Exchange Administrator | 2 |

## External / Guest Collaboration

### Guest Accounts

- Total guests: 14
- Examples (first 3):
  - Partner Contact (partner_contoso.example#EXT#@contoso.example)

### Stale Guest Accounts (90+ days inactive)

- Total stale guests: 5
- Examples (first 3):
  - Old Vendor (vendor_old#EXT#@contoso.example)

## Tenant Policy

### Security Defaults

- Enabled: No

### Conditional Access

- Total policies: 5
- Enabled: 3
- Report-only: 1
- Example enabled policies: Require MFA for admins, Block legacy authentication, Require compliant device

### User App Consent

- Users can consent to apps: Yes
- Ordinary users can consent to third-party apps. Restricting this to admin approval reduces illicit-consent (OAuth phishing) risk.

## Account Hygiene (Cost / Cleanup)

_These are cost/cleanup observations. Dormant **enabled** accounts are also scored above as an identity signal; disabled accounts cannot sign in and are reported here for reclaimable licensing only — they do not affect the posture score._

### Dormant Enabled Licensed Accounts (90+ days inactive)

- Total: 6
- Examples (first 3):
  - Sample Dormant One (dormant1@contoso.example)
  - Sample Dormant Two (dormant2@contoso.example)

### Disabled but Still-Licensed Accounts

- Total: 2 (reclaimable license; not a sign-in risk)
- Examples (first 3):
  - Former Employee (former@contoso.example)

## License Optimization

| Metric | Value |
|---|---|
| Active (paid) units | 175 |
| Consumed units | 161 |
| Potentially reclaimable seats | 14 |
| Est. reclaimable spend (monthly) | $446.00 |
| Est. reclaimable spend (annual) | $5,352.00 |
| Priced reclaimable seats | 12 |
| Unpriced reclaimable seats | 2 |

> Estimates from Microsoft public list prices (approximate). Unassigned seats are *potentially reclaimable*, not proven waste, and should be reviewed before any change.

> ⚠ 2 reclaimable seat(s) across 1 SKU(s) have no pricing data; the dollar estimate covers only priced SKUs.

> Unpriced SKUs: CONTOSO_ADDON

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