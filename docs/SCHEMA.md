# Output schema and versioning

The `assess` command writes `assessment_results.json` to the output directory. Its shape is a direct serialization of the `AssessmentResult` model ([`models/assessment.py`](../models/assessment.py)).

## Two independent version numbers

| Version | Where | Meaning |
|---|---|---|
| **Package version** | `pyproject.toml` | Software release version. Standard semver. |
| **Schema version** | `schema_version` in the JSON | Version of the control set and JSON/report shape. |

These change independently: a packaging or dependency patch does not bump the schema, and a change to controls does not necessarily bump the package's major version.

The current schema version is **`2.0.0`** (defined as `SCHEMA_VERSION` in `models/assessment.py`).

## Compatibility expectations

Schema versioning follows semver semantics:

- **Patch** (`2.0.x`) — wording/detail changes; no field added or removed.
- **Minor** (`2.x.0`) — **new fields added** (e.g. a new control). Consumers should ignore unknown fields; existing fields keep their meaning.
- **Major** (`x.0.0`) — a field is **renamed, removed, or changes meaning/type**. Scripts pinned to a major version may need updates.

If you parse the JSON in automation, branch on `schema_version` and treat unknown fields as additive.

## Top-level shape

```jsonc
{
  "generated_at": "2026-01-15T09:00:00+00:00",
  "schema_version": "2.0.0",
  "license_waste": { "status": "...", "unassigned_units": 14, ... },
  "global_admins": { "status": "...", "count": 4, "risk_level": "Moderate" },
  "privileged_mfa": { "status": "...", "coverage_pct": 100.0, ... },
  "tenant_mfa": { "status": "...", "coverage_pct": 82.0, ... },
  "privileged_roles": { "status": "...", "distinct_privileged_users": 7, "roles": [...] },
  "dormant_users": { "status": "...", "total_count": 6, "examples": [...] },
  "disabled_licensed_users": { "status": "...", "total_count": 2, ... },
  "guest_users": { "status": "...", "total_count": 14, ... },
  "stale_guests": { "status": "...", "total_count": 5, ... },
  "security_defaults": { "status": "...", "enabled": false },
  "conditional_access": { "status": "...", "policy_count": 5, "enabled_count": 3, ... },
  "user_consent": { "status": "...", "users_can_consent": true, ... },
  "posture": { "grade": "Fair", "score_pct": 56.0, "controls": [...], ... }
}
```

Each finding carries a `status` of `SUCCESS`, `SKIPPED`, or `ERROR`. `SKIPPED`/`ERROR` findings include a `skipped_reason`.

A byte-stable example generated from synthetic data lives at [samples/sample_assessment_results.json](samples/sample_assessment_results.json).
