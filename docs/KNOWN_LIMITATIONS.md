# Known limitations

We would rather you read this before a skeptical reviewer writes it for us. These are honest, current limitations — not bugs, and not things we are hiding.

## Scope of the score

- **The Identity Security Posture Score covers identity/access only.** It evaluates a focused set of Microsoft 365 identity and tenant-policy controls. It does **not** assess endpoint, network, data-protection, email-security, application-security, or process/physical controls. A "Strong" grade means the *evaluated identity controls* look healthy — not that the organization is secure overall.
- **The score is a transparent point ratio, not a predictive model.** It does not estimate breach likelihood, compliance, or insurance outcomes. See [METHODOLOGY.md](METHODOLOGY.md).
- **Thresholds are opinionated heuristics.** For example, "≤3 Global Admins = PASS" reflects common guidance, not a universal truth. The per-control detail is always shown so you can disagree with the roll-up.

## Coverage and depth

- **It is not ScubaGear or Maester.** This is a fast, narrow, read-only snapshot. It does not implement CISA SCuBA baselines or a Pester test framework, and it evaluates far fewer controls than those tools. If you need exhaustive, standards-mapped coverage, use them (see the README comparison).
- **Conditional Access is inventoried, not evaluated.** The tool reports how many CA policies exist and are enabled; it does **not** analyze whether those policies are actually effective, correctly scoped, or free of gaps.
- **MFA "registration" ≠ "enforcement".** Coverage reflects whether users have *registered* MFA methods (from `userRegistrationDetails`). A registered user may still have sign-ins that don't require MFA if enforcement policy is weak.

## Licensing dependencies

- **Several controls require Entra ID P1/P2.** Without premium licensing, MFA reporting, `signInActivity` (dormant/stale), and Conditional Access inventory are reported as **SKIPPED**. On a bare tenant, the score may be computed over as few as ~3 controls. The report always states how many controls were evaluated.

## Cost estimates

- **License dollar figures are estimates.** They use approximate public list prices (or your override file), not your actual EA/CSP/contract pricing, which may differ materially. Unassigned seats are *potentially reclaimable*, not proven waste, and the tool never tells you to remove a specific license.

## Authentication and roles

- **The Global-Reader-can-run guidance is based on Microsoft's role documentation.** The tool self-verifies at runtime (a denied read becomes a SKIPPED control with the exact reason, never a silent pass), and [PERMISSIONS.md](PERMISSIONS.md#confirm-least-privilege-in-your-own-tenant) shows how to confirm it in your own tenant with a single run. Role behavior can vary with custom roles and tenant configuration, so validate before a broad rollout.
- **BYO App Registration is required for the first release.** There is intentionally no shared Cloud Locksmith client ID yet; see [AUTH_RECOMMENDATION.md](AUTH_RECOMMENDATION.md) for why and what would gate one.

## Data and sampling

- **Reports include up to 3 example accounts per finding** (display name + UPN) to make findings actionable. Review reports before sharing them externally. The `output/` directory is gitignored by default.

## Not in the free CLI (by design)

Scheduling, alerting, historical tracking, cross-tenant aggregation, remediation/verification/rollback, and fleet dashboards are **not** in this CLI. They are the paid Cloud Locksmith platform's job. This is a deliberate product boundary, not a missing feature — see the README.

---

If you hit a limitation not listed here, please open an issue. We would rather expand this list than pretend it doesn't exist.
