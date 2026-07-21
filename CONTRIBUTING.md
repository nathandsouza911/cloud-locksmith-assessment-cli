# Contributing

Thanks for your interest in improving the Cloud Locksmith Assessment CLI. This is an open-source, read-only Microsoft 365 posture tool, and contributions that keep it fast, trustworthy, and low-friction are very welcome.

## Scope of this project

This CLI is intentionally focused: **detect, explain, export, and teach**, locally and read-only. To keep the trust model simple, some things are deliberately **out of scope** here and belong to the paid Cloud Locksmith platform:

- Remediation, verification, or rollback of any kind.
- Scheduling, alerting, or long-running daemons.
- Cross-tenant aggregation, fleet dashboards, or historical databases.
- Anything requiring **application (app-only) permissions** or **write** scopes.

New controls must work under the existing **delegated, read-only** authentication model. If a control would require broader or scarier permissions, it does not belong in this CLI (see the Exchange forwarding-rule discussion in the launch notes for an example of a control deliberately excluded on these grounds).

## Development setup

```bash
uv sync
uv run pytest tests/ -v
```

## Adding a control

The architecture is designed to make this clean:

1. Add any new Graph shape to `models/graph.py` and a finding model to `models/findings.py`.
2. If it needs a new endpoint, add a `get_*` method to `graph/client.py` and the `GraphDataProvider` Protocol in `graph/provider.py`, plus the stub in `tests/conftest.py`.
3. Write a finder in `findings/` that returns a finding with a `status` of `SUCCESS` / `SKIPPED` / `ERROR`. Degrade gracefully — a missing permission or premium-license requirement should produce `SKIPPED` with a clear reason, never a crash.
4. Add the finding to `AssessmentResult` (`models/assessment.py`) and wire it into all four outputs (`reports/executive_summary.py`, `reports/markdown_report.py`, `reports/pdf_report.py`, and the JSON in `cli.py`).
5. If it should affect the score, add it to `findings/posture_score.py` and document the thresholds in `docs/METHODOLOGY.md`.
6. Add tests. Run `uv run python scripts/generate_samples.py` to refresh the synthetic samples.

## Guidelines

- **Read-only only.** Every Graph call must be a `GET`. No write scopes, no app-only auth.
- **Accurate claims.** User-facing text must be defensible against the actual implementation. Avoid marketing language ("continuous monitoring", "prevents breaches", etc.).
- **No secrets, no real tenant data.** Never commit tokens, client secrets, or real tenant output. Samples must be synthetic.
- **Keep it fast and low-config.** The value of this tool is running in a few minutes with minimal setup.

## Reporting bugs and ideas

Please use GitHub Issues for bugs and feature requests, and GitHub Discussions for questions, methodology debate, and "should this be a control?" conversations. For anything security-sensitive, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
