from __future__ import annotations
import pathlib
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)
from models.findings import (
    LicenseWasteFinding, DormantUsersFinding, DisabledLicensedFinding,
    GlobalAdminsFinding, MFACoverageFinding, FindingStatus,
)
from models.readiness import InsuranceReadiness

ASSESSMENT_VERSION = "1.0.0"
_FOOTER = "Generated locally. No data sent to Cloud Locksmith. Assessment only. Not a remediation tool."
_ESTIMATE_DISCLAIMER = (
    "This simplified estimate is based on a limited set of Microsoft 365 controls "
    "and is not an underwriting decision."
)

_DARK_BLUE = colors.HexColor("#1a3a5c")
_LIGHT_GRAY = colors.HexColor("#f5f5f5")
_GREEN = colors.HexColor("#2e7d32")
_AMBER = colors.HexColor("#f57f17")
_RED = colors.HexColor("#c62828")
_SKIP = colors.HexColor("#9e9e9e")

_STATUS_COLORS = {"PASS": _GREEN, "WARNING": _AMBER, "FAIL": _RED, "SKIPPED": _SKIP}
_TIER_COLORS = {"Strong": _GREEN, "Good": _GREEN, "Fair": _AMBER, "Poor": _RED}


def write_pdf(
    license_waste: LicenseWasteFinding,
    dormant: DormantUsersFinding,
    disabled: DisabledLicensedFinding,
    admins: GlobalAdminsFinding,
    mfa: MFACoverageFinding,
    readiness: InsuranceReadiness,
    output_path: pathlib.Path,
) -> None:
    doc = SimpleDocTemplate(
        str(output_path), pagesize=letter,
        rightMargin=0.75 * inch, leftMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=_DARK_BLUE, fontSize=20)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=_DARK_BLUE, fontSize=14)
    body = styles["Normal"]
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor=colors.gray)
    story = []

    def footer() -> Paragraph:
        return Paragraph(_FOOTER, small)

    # ── Page 1: Executive Summary ──────────────────────────────────────────
    story += [Paragraph("Microsoft 365 Assessment", h1), Paragraph("Executive Summary", h2),
              Spacer(1, 0.1 * inch)]
    tier_style = ParagraphStyle("tier", parent=styles["Normal"], fontSize=16,
                                textColor=_TIER_COLORS.get(readiness.tier, _DARK_BLUE))
    story.append(Paragraph(f"Insurance Readiness Estimate: <b>{readiness.tier.upper()}</b>", tier_style))
    story.append(Spacer(1, 0.1 * inch))
    exec_rows = [["Metric", "Value"]]
    if license_waste.status == FindingStatus.SUCCESS:
        exec_rows += [
            ["Estimated Annual License Waste", f"${license_waste.estimated_annual_waste_usd:,.2f}"],
            ["Unassigned Licenses", str(license_waste.unassigned_units)],
        ]
    exec_rows += [
        ["Insurance Readiness Tier", readiness.tier],
        ["Readiness Score", f"{readiness.total_score}/{readiness.max_possible_score} ({readiness.score_pct:.0f}%)"],
    ]
    story += [_tbl(exec_rows), Spacer(1, 0.2 * inch), footer(), PageBreak()]

    # ── Page 2: Financial Findings ─────────────────────────────────────────
    story += [Paragraph("Financial Findings", h1), Spacer(1, 0.1 * inch)]
    if license_waste.status == FindingStatus.SUCCESS:
        rows = [
            ["Metric", "Value"],
            ["Active Units", str(license_waste.active_units)],
            ["Consumed Units", str(license_waste.consumed_units)],
            ["Unassigned Units", str(license_waste.unassigned_units)],
            ["Estimated Annual Waste (USD)", f"${license_waste.estimated_annual_waste_usd:,.2f}"],
        ]
        story.append(_tbl(rows))
    else:
        story.append(Paragraph(f"License data unavailable: {license_waste.skipped_reason}", body))
    story += [Spacer(1, 0.2 * inch), footer(), PageBreak()]

    # ── Page 3: Security Findings ──────────────────────────────────────────
    story += [Paragraph("Security Findings", h1), Spacer(1, 0.1 * inch)]
    sec_rows = [["Finding", "Status", "Detail"]]
    sec_rows.append([
        "Global Administrators", admins.status.value,
        f"{admins.count} admins — {admins.risk_level} risk" if admins.status == FindingStatus.SUCCESS else (admins.skipped_reason or ""),
    ])
    sec_rows.append([
        "MFA Coverage (Privileged)", mfa.status.value,
        f"{mfa.coverage_pct:.0f}% ({mfa.mfa_registered_count}/{mfa.privileged_user_count})" if mfa.status == FindingStatus.SUCCESS else (mfa.skipped_reason or ""),
    ])
    sec_rows.append([
        "Dormant Licensed Users", dormant.status.value,
        f"{dormant.total_count} users" if dormant.status == FindingStatus.SUCCESS else (dormant.skipped_reason or ""),
    ])
    sec_rows.append([
        "Disabled Licensed Users", disabled.status.value,
        f"{disabled.total_count} users" if disabled.status == FindingStatus.SUCCESS else (disabled.skipped_reason or ""),
    ])
    story += [_tbl(sec_rows, status_col=1), Spacer(1, 0.2 * inch), footer(), PageBreak()]

    # ── Page 4: Insurance Readiness Estimate ──────────────────────────────
    story += [Paragraph("Insurance Readiness Estimate", h1), Spacer(1, 0.1 * inch)]
    evaluated = len(readiness.controls) - len(readiness.skipped_controls)
    story.append(Paragraph(
        f"<b>Tier: {readiness.tier}</b> — Score: {readiness.total_score}/{readiness.max_possible_score} ({readiness.score_pct:.0f}%) — {evaluated} of {len(readiness.controls)} controls evaluated",
        body,
    ))
    story.append(Spacer(1, 0.1 * inch))
    ctrl_rows = [["Control", "Status", "Pts", "Detail"]]
    for ctrl in readiness.controls:
        ctrl_rows.append([ctrl.name, ctrl.status, str(ctrl.points), ctrl.detail])
    story.append(_tbl(ctrl_rows, status_col=1))
    if readiness.skipped_controls:
        story += [Spacer(1, 0.08 * inch),
                  Paragraph(f"Skipped: {', '.join(readiness.skipped_controls)}", body)]
    story += [Spacer(1, 0.12 * inch), Paragraph(_ESTIMATE_DISCLAIMER, small)]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta_rows = [
        ["Field", "Value"],
        ["Generated", now],
        ["Assessment Version", ASSESSMENT_VERSION],
        ["Authentication", "Microsoft Device Code Flow"],
        ["Permissions", "Read-only delegated"],
        ["Data Handling", "No data transmitted to Cloud Locksmith."],
        ["Token Handling", "Tokens discarded after assessment."],
    ]
    story += [Spacer(1, 0.2 * inch), Paragraph("Assessment Metadata", h2),
              _tbl(meta_rows), Spacer(1, 0.2 * inch), footer()]

    doc.build(story)


def _tbl(data: list[list], status_col: int | None = None) -> Table:
    t = Table(data, hAlign="LEFT", repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), _DARK_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    if status_col is not None:
        for i, row in enumerate(data[1:], start=1):
            val = row[status_col] if status_col < len(row) else None
            c = _STATUS_COLORS.get(val, colors.black)
            style += [
                ("TEXTCOLOR", (status_col, i), (status_col, i), c),
                ("FONTNAME", (status_col, i), (status_col, i), "Helvetica-Bold"),
            ]
    t.setStyle(TableStyle(style))
    return t
