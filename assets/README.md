# Screenshot assets (optional)

The README links the synthetic [sample reports](../docs/samples/) as the primary "see the output first" artifacts, so screenshots are optional.

If you want to add a terminal screenshot to the README, capture the output of `uv run cloudlocksmith assess` against a tenant with at least one finding. A good capture shows:

- the Cloud Locksmith header panel,
- the **SECURITY POSTURE SCORE** section with the control table,
- the IDENTITY, EXTERNAL/GUEST, TENANT POLICY, and LICENSE OPTIMIZATION sections.

**Capture on Windows:** use the Snipping Tool (`Win + Shift + S`); size the terminal to ~100 columns first. Never include a real tenant's data in a committed screenshot — use a test tenant or redact identifiers.
