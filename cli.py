from __future__ import annotations
import json
import logging
import pathlib
from typing import Optional

import typer

from auth.device_code import acquire_token
from findings.admin_mfa import AdminMFAFinder
from findings.conditional_access import ConditionalAccessFinder
from findings.disabled_licenses import DisabledLicensedFinder
from findings.dormant_users import DormantUserFinder
from findings.global_admins import GlobalAdminFinder
from findings.guest_users import GuestUsersFinder
from findings.posture_score import evaluate_posture
from findings.privileged_roles import PrivilegedRolesFinder
from findings.security_defaults import SecurityDefaultsFinder
from findings.stale_guests import StaleGuestsFinder
from findings.tenant_mfa import TenantMFAFinder
from findings.unassigned_licenses import UnassignedLicenseFinder
from findings.user_consent import UserConsentFinder
from graph.client import GraphClient
from graph.roles import GLOBAL_ADMIN_TEMPLATE_ID
from models.assessment import AssessmentResult
from reports.executive_summary import print_summary, print_next_steps
from reports.markdown_report import write_markdown
from reports.pdf_report import write_pdf

app = typer.Typer(help="Cloud Locksmith - local-first Microsoft 365 security assessment CLI")
logging.basicConfig(level=logging.WARNING)

# Documented exit codes (see docs/EXIT_CODES.md):
EXIT_OK = 0            # Assessment completed. In non-strict mode this is returned even
                       # when the scan surfaces findings — findings are not a run failure.
EXIT_FINDINGS = 2      # --strict only: completed with one or more FAIL-level controls.
EXIT_AUTH = 3          # Authentication or configuration failure (e.g. no client ID).
EXIT_RUNTIME = 4       # Unexpected runtime failure.


_CLIENT_ID_OPTION = typer.Option(
    None, "--client-id", "-c",
    help="Azure App Registration client ID. Overrides CLOUDLOCKSMITH_CLIENT_ID.",
)


@app.command()
def login(client_id: Optional[str] = _CLIENT_ID_OPTION) -> None:
    """Verify Device Code authentication (does not run assessment)."""
    typer.echo("Starting Microsoft Device Code authentication...")
    try:
        acquire_token(client_id)
    except RuntimeError as exc:
        typer.echo(f"Authentication failed: {exc}", err=True)
        raise typer.Exit(EXIT_AUTH)
    typer.echo("Authentication successful.")


@app.command()
def assess(
    output_dir: pathlib.Path = typer.Option(
        pathlib.Path("output"), "--output-dir", "-o",
        help="Directory for the JSON, Markdown, and PDF reports.",
    ),
    strict: bool = typer.Option(
        False, "--strict", "-s",
        help=f"Return exit code {EXIT_FINDINGS} if any control FAILs (for CI/automation).",
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q",
        help="Suppress the terminal summary; still writes report files.",
    ),
    client_id: Optional[str] = _CLIENT_ID_OPTION,
) -> None:
    """Authenticate and run a full Microsoft 365 security assessment."""
    typer.echo("Starting Microsoft Device Code authentication...")
    try:
        token = acquire_token(client_id)
    except RuntimeError as exc:
        typer.echo(f"Authentication failed: {exc}", err=True)
        raise typer.Exit(EXIT_AUTH)

    typer.echo("Authenticated. Running assessment...\n")

    try:
        result = _run_assessment(token)
    except Exception as exc:  # noqa: BLE001 — surface any unexpected failure with a clean code
        typer.echo(f"Assessment failed unexpectedly: {exc}", err=True)
        raise typer.Exit(EXIT_RUNTIME)

    if not quiet:
        print_summary(result)

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "assessment_results.json"
    md_path = output_dir / "assessment_report.md"
    pdf_path = output_dir / "assessment_report.pdf"

    json_path.write_text(
        json.dumps(json.loads(result.model_dump_json()), indent=2, default=str),
        encoding="utf-8",
    )
    write_markdown(result, md_path)
    write_pdf(result, pdf_path)

    typer.echo("Assessment complete.\n")
    typer.echo("Reports saved to:")
    typer.echo(f"  - {json_path}")
    typer.echo(f"  - {md_path}")
    typer.echo(f"  - {pdf_path}\n")

    if not quiet:
        print_next_steps()

    if strict and result.has_failures():
        raise typer.Exit(EXIT_FINDINGS)
    raise typer.Exit(EXIT_OK)


def _run_assessment(token: dict) -> AssessmentResult:
    client = GraphClient(token)

    typer.echo("  [1/7] Fetching privileged directory roles...")
    admin_users = client.get_role_members(GLOBAL_ADMIN_TEMPLATE_ID)
    admins = GlobalAdminFinder(client).run()
    privileged_roles = PrivilegedRolesFinder(client).run()

    typer.echo("  [2/7] Evaluating MFA registration...")
    privileged_mfa = AdminMFAFinder(client, admin_users).run()
    tenant_mfa = TenantMFAFinder(client).run()

    typer.echo("  [3/7] Checking account hygiene...")
    dormant = DormantUserFinder(client).run()
    disabled = DisabledLicensedFinder(client).run()

    typer.echo("  [4/7] Reviewing external/guest collaboration...")
    guests = GuestUsersFinder(client).run()
    stale_guests = StaleGuestsFinder(client).run()

    typer.echo("  [5/7] Reading tenant policy (Security Defaults, CA, consent)...")
    security_defaults = SecurityDefaultsFinder(client).run()
    conditional_access = ConditionalAccessFinder(client).run()
    user_consent = UserConsentFinder(client).run()

    typer.echo("  [6/7] Analyzing license optimization...")
    license_waste = UnassignedLicenseFinder(client).run()

    typer.echo("  [7/7] Computing Identity Security Posture Score...\n")
    posture = evaluate_posture(
        privileged_mfa, admins, dormant, tenant_mfa,
        security_defaults, conditional_access, user_consent, stale_guests,
    )

    return AssessmentResult(
        license_waste=license_waste,
        global_admins=admins,
        privileged_mfa=privileged_mfa,
        tenant_mfa=tenant_mfa,
        privileged_roles=privileged_roles,
        dormant_users=dormant,
        disabled_licensed_users=disabled,
        guest_users=guests,
        stale_guests=stale_guests,
        security_defaults=security_defaults,
        conditional_access=conditional_access,
        user_consent=user_consent,
        posture=posture,
    )


if __name__ == "__main__":
    app()
