# Sample reports

These files let you see exactly what the CLI produces **before** you grant any Microsoft Graph permissions. Two scenarios are included.

## Scenario 1 — tenant *with* Entra ID P1/P2 (mixed findings)

A realistic tenant where all controls evaluate, with a mix of PASS/WARNING/FAIL (grade: **Fair**).

| File | Description |
|---|---|
| [sample_assessment_report.md](sample_assessment_report.md) | Full Markdown report |
| [sample_assessment_report.pdf](sample_assessment_report.pdf) | Four-page executive PDF |
| [sample_assessment_results.json](sample_assessment_results.json) | Structured JSON output |

## Scenario 2 — tenant *without* Entra ID P1/P2 (SKIPPED behavior)

A small tenant where MFA reporting, sign-in activity, and Conditional Access are unavailable, so those controls are **SKIPPED** and the grade is **capped** because a required control could not be evaluated (grade: **Good**, computed over only 3 controls). This shows how the tool degrades honestly instead of guessing.

| File | Description |
|---|---|
| [sample_no_premium_report.md](sample_no_premium_report.md) | Markdown report with SKIPPED controls |
| [sample_no_premium_report.pdf](sample_no_premium_report.pdf) | PDF with SKIPPED controls |
| [sample_no_premium_results.json](sample_no_premium_results.json) | JSON with SKIPPED statuses |

## They are 100% synthetic

Every value in these samples is invented ("Contoso"). They contain **no real tenant information, user data, or secrets**. They are generated deterministically by:

```bash
uv run python scripts/generate_samples.py
```

from the fixed synthetic data in [`scripts/generate_samples.py`](../../scripts/generate_samples.py). Regenerate them after changing any report format so the committed samples never drift from the real output.
