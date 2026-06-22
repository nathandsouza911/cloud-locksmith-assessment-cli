from __future__ import annotations
import json
import logging
import pathlib
from datetime import datetime, timezone

import typer

from auth.device_code import acquire_token
from findings.admin_mfa import AdminMFAFinder
from findings.disabled_licenses import DisabledLicensedFinder
from findings.dormant_users import DormantUserFinder
from findings.global_admins import GlobalAdminFinder
from findings.insurance_readiness import evaluate_readiness
from findings.unassigned_licenses import UnassignedLicenseFinder
from graph.client import GraphClient
from graph.roles import GLOBAL_ADMIN_TEMPLATE_ID
from reports.executive_summary import print_summary
from reports.markdown_report import write_markdown
from reports.pdf_report import write_pdf

app = typer.Typer(help="Cloud Locksmith — local-first Microsoft 365 security assessment CLI")
logging.basicConfig(level=logging.WARNING)

_OUTPUT = pathlib.Path("output")
_ASSESSMENT_VERSION = "1.0.0"


@app.command()
def login() -> None:
    """Verify Device Code authentication (does not run assessment)."""
    typer.echo("Starting Microsoft Device Code authentication...")
    acquire_token()
    typer.echo("✓ Authentication successful.")


@app.command()
def assess() -> None:
    """Authenticate and run a full Microsoft 365 security assessment."""
    typer.echo("Starting Microsoft Device Code authentication...")
    token = acquire_token()
    typer.echo("✓ Authenticated. Running assessment...\n")

    client = GraphClient(token)
    _OUTPUT.mkdir(exist_ok=True)

    typer.echo("  [1/5] Fetching Global Administrators...")
    admin_users = client.get_role_members(GLOBAL_ADMIN_TEMPLATE_ID)

    typer.echo("  [2/5] Analyzing license waste...")
    license_waste = UnassignedLicenseFinder(client).run()

    typer.echo("  [3/5] Checking user account status...")
    disabled = DisabledLicensedFinder(client).run()
    dormant = DormantUserFinder(client).run()

    typer.echo("  [4/5] Evaluating global admin count...")
    admins = GlobalAdminFinder(client).run()

    typer.echo("  [5/5] Evaluating MFA coverage for privileged users...")
    mfa = AdminMFAFinder(client, admin_users).run()

    readiness = evaluate_readiness(mfa, admins, dormant, disabled)

    print_summary(license_waste, dormant, disabled, admins, mfa, readiness)

    now = datetime.now(timezone.utc).isoformat()
    result = {
        "generated_at": now,
        "assessment_version": _ASSESSMENT_VERSION,
        "license_waste": json.loads(license_waste.model_dump_json()),
        "dormant_users": json.loads(dormant.model_dump_json()),
        "disabled_licensed_users": json.loads(disabled.model_dump_json()),
        "global_admins": json.loads(admins.model_dump_json()),
        "mfa_coverage": json.loads(mfa.model_dump_json()),
        "insurance_readiness": json.loads(readiness.model_dump_json()),
        "metadata": {
            "assessment_version": _ASSESSMENT_VERSION,
            "authentication": "Microsoft Device Code Flow",
            "permissions": "Read-only delegated",
            "data_handling": "No data transmitted to Cloud Locksmith.",
            "token_handling": "Tokens discarded after assessment.",
        },
    }
    json_path = _OUTPUT / "assessment_results.json"
    json_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    typer.echo(f"  ✓ JSON  → {json_path}")

    md_path = _OUTPUT / "assessment_report.md"
    write_markdown(license_waste, dormant, disabled, admins, mfa, readiness, md_path)
    typer.echo(f"  ✓ MD    → {md_path}")

    pdf_path = _OUTPUT / "assessment_report.pdf"
    write_pdf(license_waste, dormant, disabled, admins, mfa, readiness, pdf_path)
    typer.echo(f"  ✓ PDF   → {pdf_path}")

    typer.echo("\nAssessment complete.")


if __name__ == "__main__":
    app()
