# cloud-locksmith-assessment-cli

A local-first Microsoft 365 security assessment CLI. All analysis runs on your
machine. No data is transmitted externally. Authentication tokens are discarded
after each run.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A Microsoft Azure App Registration with Device Code flow enabled

## Azure App Registration

1. Go to **Azure Portal → Azure Active Directory → App registrations → New registration**
2. Name: `Cloud Locksmith Assessment CLI`
3. Supported account types: **Accounts in any organizational directory**
4. No redirect URI needed (Device Code flow is public)
5. Under **Authentication**: enable **Allow public client flows**
6. Under **API permissions**, add delegated permissions:
   - `User.Read`
   - `Directory.Read.All` (requires admin consent)
   - `Reports.Read.All` (requires admin consent)
   - `Organization.Read.All`
   - `AuditLog.Read.All` (requires admin consent; needed for sign-in activity)
7. Grant admin consent for your tenant
8. Copy the **Application (client) ID**

> **Note:** The user running `cloudlocksmith assess` must be a Global Administrator
> or have admin consent pre-granted for `Reports.Read.All` and `AuditLog.Read.All`.

## Setup

```bash
uv sync
export CLOUDLOCKSMITH_CLIENT_ID="your-app-client-id-here"
```

## Usage

```bash
# Verify authentication
uv run cloudlocksmith login

# Run full assessment (generates reports in output/)
uv run cloudlocksmith assess
```

## Output

After `assess` completes, the `output/` directory contains:

- `assessment_report.md` — Markdown report
- `assessment_report.pdf` — Executive PDF report (4 pages)
- `assessment_results.json` — Structured JSON output

## Privacy

- No data is transmitted to Cloud Locksmith or any external service
- Authentication tokens are held in memory only and discarded on process exit
- The `output/` directory is gitignored — reports stay local

## Running Tests

```bash
uv run pytest tests/ -v
```
