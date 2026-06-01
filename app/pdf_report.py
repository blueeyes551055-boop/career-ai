"""
PDF report generation for a completed test attempt, using ReportLab.

Produces an in-memory PDF (BytesIO) so it can be streamed straight to the
browser as a download — no temp files left behind.
"""
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

PRIMARY = colors.HexColor("#1f3a5f")
ACCENT = colors.HexColor("#d98c3f")
LIGHT = colors.HexColor("#eef2f7")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"],
        textColor=PRIMARY, fontSize=22, spaceAfter=4))
    styles.add(ParagraphStyle(
        name="Sub", parent=styles["Normal"], textColor=colors.grey, fontSize=10))
    styles.add(ParagraphStyle(
        name="H2", parent=styles["Heading2"], textColor=PRIMARY, fontSize=13,
        spaceBefore=14, spaceAfter=6))
    styles.add(ParagraphStyle(
        name="Body", parent=styles["Normal"], fontSize=10, leading=15))
    return styles


def build_report(user, attempt) -> BytesIO:
    """Return a BytesIO containing the PDF for the given user + TestAttempt."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
        title="Career Counselling Report",
    )
    s = _styles()
    flow = []

    # --- header -----------------------------------------------------------
    flow.append(Paragraph("Career Counselling Report", s["ReportTitle"]))
    flow.append(Paragraph(
        "AI-Based Career Counselling System", s["Sub"]))
    flow.append(Spacer(1, 10))

    info = [
        ["Student", user.full_name],
        ["Email", user.email],
        ["Date", attempt.created_at.strftime("%d %b %Y, %H:%M")],
        ["Overall aptitude", f"{attempt.overall_score:.0f}%"],
    ]
    t = Table(info, colWidths=[40 * mm, 120 * mm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LIGHT),
    ]))
    flow.append(t)

    # --- aptitude scores --------------------------------------------------
    flow.append(Paragraph("Aptitude Scores", s["H2"]))
    apt_rows = [["Category", "Score"]]
    apt_rows += [
        ["Logical Reasoning", f"{attempt.logical_score:.0f}%"],
        ["Analytical Thinking", f"{attempt.analytical_score:.0f}%"],
        ["Verbal Ability", f"{attempt.verbal_score:.0f}%"],
    ]
    at = Table(apt_rows, colWidths=[80 * mm, 80 * mm])
    at.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, LIGHT),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(at)

    # --- interest areas ---------------------------------------------------
    interest = attempt.interest or {}
    if interest:
        flow.append(Paragraph("Interest Profile", s["H2"]))
        ir = [["Interest Area", "Score"]]
        for area, val in sorted(interest.items(), key=lambda kv: kv[1], reverse=True):
            ir.append([area.capitalize(), f"{val:.0f}%"])
        it = Table(ir, colWidths=[80 * mm, 80 * mm])
        it.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.4, LIGHT),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        flow.append(it)

    # --- recommended careers ---------------------------------------------
    flow.append(Paragraph("Recommended Careers", s["H2"]))
    for rec in attempt.recommendations:
        flow.append(Paragraph(
            f"<b>{rec['name']}</b> &nbsp;—&nbsp; {rec['match']:.0f}% match",
            s["Body"]))
        flow.append(Paragraph(
            f"{rec.get('description','')} <i>{rec.get('reason','')}</i>", s["Body"]))
        flow.append(Spacer(1, 6))

    # --- recommended programs --------------------------------------------
    programs = attempt.programs
    if programs:
        flow.append(Paragraph("Suggested University Programs", s["H2"]))
        for p in programs:
            line = f"<b>{p['name']}</b>"
            if p.get("degree_level") or p.get("duration"):
                line += f" ({p.get('degree_level','')}, {p.get('duration','')})"
            flow.append(Paragraph(line, s["Body"]))
            if p.get("universities"):
                flow.append(Paragraph(
                    f"<font color='#666666'>Universities: {p['universities']}</font>",
                    s["Body"]))
            flow.append(Spacer(1, 5))

    flow.append(Spacer(1, 16))
    flow.append(Paragraph(
        "<font size=8 color='#999999'>This report is generated automatically as "
        "study guidance and is not a substitute for professional career counselling."
        "</font>", s["Body"]))

    doc.build(flow)
    buffer.seek(0)
    return buffer


