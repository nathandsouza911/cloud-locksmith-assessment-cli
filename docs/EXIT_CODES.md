# Exit codes

The `cloudlocksmith` CLI uses exit codes designed for automation. The guiding principle: **a scan that successfully finds security issues is not a process failure.** Finding problems is the tool working correctly.

| Code | Name | Meaning |
|---|---|---|
| `0` | OK | The assessment ran to completion. Returned even when the scan surfaces findings, **unless** `--strict` is set. |
| `2` | FINDINGS | `--strict` only: the assessment completed and at least one scored control is `FAIL`. |
| `3` | AUTH | Authentication or configuration failure — e.g. `CLOUDLOCKSMITH_CLIENT_ID` not set, device-code sign-in failed. |
| `4` | RUNTIME | An unexpected error occurred while running the assessment. |

## Default vs. `--strict`

By default the CLI exits `0` on any successful run so it does not break naive pipelines that only check for a non-zero status. Individual finding statuses are always available in the JSON output and reports.

Use `--strict` when you want the process status to reflect posture — for example, to fail a CI job when a control is `FAIL`:

```bash
uv run cloudlocksmith assess --strict --quiet
echo "exit: $?"   # 0 = no FAIL controls, 2 = at least one FAIL control
```

Note that `WARNING` controls do **not** trigger exit code `2`; only `FAIL` does. `SKIPPED` controls (data unavailable) never affect the exit code.

## Distinguishing the three outcomes you usually care about

- **Completed, nothing significant:** exit `0`, and (in `--strict`) no `FAIL` controls.
- **Completed, significant findings:** exit `0` by default, or exit `2` with `--strict`.
- **Could not run (auth/config/runtime):** exit `3` or `4` — always non-zero regardless of flags.
