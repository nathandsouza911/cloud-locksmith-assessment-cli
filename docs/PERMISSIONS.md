# Permissions and Graph endpoints

The Cloud Locksmith Assessment CLI uses **read-only, delegated** Microsoft Graph permissions and the Microsoft Device Code authentication flow. **Every request is an HTTP `GET`.** There are no write scopes, no application (app-only) permissions, and no Exchange/mail permissions. The tool cannot write, delete, or modify anything in your tenant.

## Authoritative scope table

All five scopes are **delegated** and **read-only** (`*.Read.All`), and all require admin consent.

| Scope | Why required | Exact checks/features using it | Representative endpoints | Read/Write |
|---|---|---|---|---|
| `Directory.Read.All` | Enumerate users/guests and resolve directory role membership | Global Admin count, Privileged role holders, Guest inventory, Dormant/Disabled accounts (user list & license flags) | `GET /users`, `GET /directoryRoles`, `GET /directoryRoles/{id}/members` | Read |
| `Reports.Read.All` | Read MFA registration status | Privileged MFA Coverage, Tenant MFA Coverage | `GET /reports/authenticationMethods/userRegistrationDetails` | Read |
| `Organization.Read.All` | Read subscription/SKU inventory | License Optimization (reclaimable seats & estimated spend) | `GET /subscribedSkus` | Read |
| `AuditLog.Read.All` | Read last-sign-in timestamps | Dormant Enabled Accounts, Stale Guest Access (`signInActivity`) | `GET /users?$select=...,signInActivity` | Read |
| `Policy.Read.All` | Read tenant policy state | Security Defaults, Conditional Access inventory, User App Consent | `GET /policies/identitySecurityDefaultsEnforcementPolicy`, `GET /identity/conditionalAccess/policies`, `GET /policies/authorizationPolicy` | Read |

`signInActivity` is a property of the user object requested via `$select`; it is powered by `AuditLog.Read.All`. There is no separate endpoint for it.

### Are any scopes broader than necessary?

`Directory.Read.All` is broader than the strict minimum (`User.Read.All` + `RoleManagement.Read.Directory` would cover the user/role reads). We deliberately keep `Directory.Read.All` because it is the well-understood, single directory-read scope that Global Reader already carries, and splitting it would add consent-screen complexity without reducing the effective read surface a Global Reader already has. This is a documented, conscious trade-off; narrowing it is a possible future refinement but is not a security regression, since every scope here is read-only.

## The exact endpoints called

Source of truth: [`graph/client.py`](../graph/client.py). Every call is a `GET`.

| Endpoint | Scope | Purpose |
|---|---|---|
| `GET /v1.0/directoryRoles` | `Directory.Read.All` | List activated directory roles |
| `GET /v1.0/directoryRoles/{id}/members` | `Directory.Read.All` | Members of Global Admin and other privileged roles |
| `GET /v1.0/users` (with `$select`, `$filter`) | `Directory.Read.All` (+`AuditLog.Read.All` for `signInActivity`) | Licensed/disabled users, sign-in activity |
| `GET /v1.0/users?$filter=userType eq 'Guest'` | `Directory.Read.All` (+`AuditLog.Read.All`) | Guest inventory and staleness |
| `GET /v1.0/subscribedSkus` | `Organization.Read.All` | Subscription/license inventory |
| `GET /v1.0/reports/authenticationMethods/userRegistrationDetails` | `Reports.Read.All` | MFA registration status per user |
| `GET /v1.0/policies/identitySecurityDefaultsEnforcementPolicy` | `Policy.Read.All` | Security Defaults on/off |
| `GET /v1.0/identity/conditionalAccess/policies` | `Policy.Read.All` | CA policy inventory (names/states only) |
| `GET /v1.0/policies/authorizationPolicy` | `Policy.Read.All` | Whether users can consent to third-party apps |

You can confirm there are no other calls: search the codebase for `GRAPH_BASE` — every usage is in `graph/client.py` and every one is `self._session.get(...)`.

## Least privilege: consent vs. run

### Who must grant consent
Granting **admin consent** to these scopes requires a **Global Administrator** or **Privileged Role Administrator**. This is a one-time action per tenant (per app registration).

### Who can run the assessment afterward
Once consent is granted, the assessment performs only reads. A **Global Reader** has read access to all endpoints above and should be able to run it without any write privileges. Recommended model: consent once with a privileged account, then run day-to-day as Global Reader.

### Run-role matrix

Expected minimum run role per endpoint, based on Microsoft's published role/permission documentation:

| Endpoint | Delegated scope | Expected minimum run role |
|---|---|---|
| `/directoryRoles`, `/directoryRoles/{id}/members` | `Directory.Read.All` | Global Reader |
| `/users` (+`signInActivity`) | `Directory.Read.All`, `AuditLog.Read.All` | Global Reader |
| `/subscribedSkus` | `Organization.Read.All` | Global Reader |
| `/reports/.../userRegistrationDetails` | `Reports.Read.All` | Global Reader (or Reports Reader) + Entra P1/P2 |
| `/policies/identitySecurityDefaultsEnforcementPolicy` | `Policy.Read.All` | Global Reader |
| `/identity/conditionalAccess/policies` | `Policy.Read.All` | Global Reader + Entra P1/P2 |
| `/policies/authorizationPolicy` | `Policy.Read.All` | Global Reader |

> **Source of this table.** The role column is derived from Microsoft's published role/permission documentation. Regardless of role, the tool cannot change anything — every scope is read-only and every call is a `GET`.

### Confirm least privilege in your own tenant

The tool verifies access at runtime, so you never have to take the table on faith:

1. After admin consent, run `cloudlocksmith assess` with a **Global Reader** account (no other roles) on a tenant **with** Entra ID P1/P2.
2. Confirm no control reports a **permission/authorization SKIP**. If the signed-in role lacks a specific read, that control is reported SKIPPED with the exact reason (e.g. `Authorization_RequestDenied`) — nothing fails silently and nothing else is affected.
3. On a tenant **without** P1/P2, expect MFA, `signInActivity` (dormant/stale), and Conditional Access controls to report SKIPPED for licensing reasons; the remaining controls still run.

If you find that Global Reader is insufficient for a specific endpoint in your environment, please open an issue with the reported error so we can refine this table.
