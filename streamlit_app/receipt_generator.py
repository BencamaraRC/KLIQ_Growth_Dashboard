"""
IAP Payout Receipt Generator
Generates branded PDF receipts for in-app purchase payouts.
Based on Template LWC_In-App Purchase App_Jan26_Updated.
"""

import io
import hashlib
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

# ── KLIQ Brand Colours ──
KLIQ_DARK = colors.HexColor("#1C3838")
KLIQ_GREEN = colors.HexColor("#2D6A4F")
KLIQ_IVORY = colors.HexColor("#FFFFF0")
KLIQ_LIME = colors.HexColor("#B7E4C7")
KLIQ_TANGERINE = colors.HexColor("#F4845F")
KLIQ_LIGHT_BG = colors.HexColor("#F9FFED")
KLIQ_BORDER = colors.HexColor("#D5D5D5")
APPLE_BLUE = colors.HexColor("#007AFF")
GOOGLE_GREEN = colors.HexColor("#34A853")

# ── Company Details ──
COMPANY_NAME = "KLIQ Technologies Ltd"
COMPANY_ADDRESS = "71-75 Shelton Street\nCovent Garden, London\nWC2H 9JQ"
COMPANY_EMAIL = "support@joinkliq.io"
COMPANY_WEB = "joinkliq.io"


def _generate_invoice_number(app_name, month):
    """Generate a deterministic invoice number from app name + month."""
    seed = f"{app_name}_{month}"
    h = hashlib.md5(seed.encode()).hexdigest()[:6].upper()
    month_code = month.replace("-", "")
    return f"{month_code}{h}"


def generate_receipt_pdf(
    app_name,
    month,
    apple_sales=0.0,
    apple_fee=0.0,
    apple_kliq_fee=0.0,
    apple_payout=0.0,
    google_sales=0.0,
    google_fee=0.0,
    google_kliq_fee=0.0,
    google_payout=0.0,
    kliq_fee_pct=0.0,
    payment_date=None,
):
    """Generate a branded PDF receipt. Returns bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=25 * mm,
        rightMargin=25 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        "KLIQTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=28,
        textColor=KLIQ_DARK,
        spaceAfter=2,
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        "KLIQSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=KLIQ_GREEN,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "CompanyInfo",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#666666"),
        leading=13,
    ))
    styles.add(ParagraphStyle(
        "FieldLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.HexColor("#888888"),
        spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        "FieldValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=KLIQ_DARK,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "SectionHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=KLIQ_DARK,
        spaceBefore=12,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "FooterText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#999999"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "RightAligned",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#666666"),
        alignment=TA_RIGHT,
    ))

    elements = []

    # ── Header: KLIQ branding + company info ──
    invoice_num = _generate_invoice_number(app_name, month)
    if not payment_date:
        payment_date = f"10th of month following {month}"

    # Two-column header
    header_data = [
        [
            Paragraph("KLIQ", styles["KLIQTitle"]),
            Paragraph(
                f"{COMPANY_NAME}<br/>{COMPANY_ADDRESS.replace(chr(10), '<br/>')}<br/>"
                f"{COMPANY_EMAIL}",
                styles["CompanyInfo"],
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[90 * mm, 70 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4 * mm))

    # Divider
    elements.append(HRFlowable(
        width="100%", thickness=2, color=KLIQ_DARK, spaceAfter=8
    ))

    # ── Invoice Details ──
    elements.append(Paragraph("IN-APP PURCHASE PAYOUT RECEIPT", styles["SectionHeader"]))

    detail_data = [
        [
            Paragraph("App Name", styles["FieldLabel"]),
            Paragraph("Invoice #", styles["FieldLabel"]),
            Paragraph("Period", styles["FieldLabel"]),
            Paragraph("Payment Date", styles["FieldLabel"]),
        ],
        [
            Paragraph(app_name, styles["FieldValue"]),
            Paragraph(invoice_num, styles["FieldValue"]),
            Paragraph(month, styles["FieldValue"]),
            Paragraph(str(payment_date), styles["FieldValue"]),
        ],
    ]
    detail_table = Table(detail_data, colWidths=[45 * mm, 35 * mm, 35 * mm, 45 * mm])
    detail_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Line Items Table ──
    total_sales = apple_sales + google_sales
    total_kliq_fee = apple_kliq_fee + google_kliq_fee
    total_payout = apple_payout + google_payout

    def fmt(v):
        return f"${v:,.2f}"

    # Table header
    line_items = [
        ["Platform", "Total Sales", "Platform Fee (30%)", f"KLIQ Fee ({kliq_fee_pct:.1f}%)", "Coach Payout"],
    ]

    if apple_sales > 0:
        line_items.append([
            "Apple App Store",
            fmt(apple_sales),
            fmt(apple_fee),
            fmt(apple_kliq_fee),
            fmt(apple_payout),
        ])

    if google_sales > 0:
        line_items.append([
            "Google Play Store",
            fmt(google_sales),
            fmt(google_fee),
            fmt(google_kliq_fee),
            fmt(google_payout),
        ])

    # Subtotal / totals
    line_items.append(["", "", "", "", ""])
    line_items.append(["", "", "", "Subtotal", fmt(total_sales)])
    line_items.append(["", "", "", f"KLIQ Fee ({kliq_fee_pct:.1f}% of Gross)", fmt(total_kliq_fee)])
    line_items.append(["", "", "", "Platform Fees (30%)", fmt(apple_fee + google_fee)])
    line_items.append(["", "", "", "TOTAL PAYOUT", fmt(total_payout)])

    col_widths = [38 * mm, 30 * mm, 32 * mm, 35 * mm, 30 * mm]
    items_table = Table(line_items, colWidths=col_widths)

    # Style the table
    style_cmds = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), KLIQ_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Data rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        # Alignment
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        # Grid
        ("GRID", (0, 0), (-1, 0), 0.5, KLIQ_DARK),
        ("LINEBELOW", (0, 0), (-1, 0), 1, KLIQ_DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    # Alternate row backgrounds for data rows
    num_data_rows = 0
    if apple_sales > 0:
        num_data_rows += 1
    if google_sales > 0:
        num_data_rows += 1

    for i in range(1, 1 + num_data_rows):
        bg = KLIQ_LIGHT_BG if i % 2 == 1 else colors.white
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))
        style_cmds.append(("LINEBELOW", (0, i), (-1, i), 0.5, KLIQ_BORDER))

    # Total row styling (last row)
    total_row_idx = len(line_items) - 1
    style_cmds.extend([
        ("BACKGROUND", (3, total_row_idx), (-1, total_row_idx), KLIQ_DARK),
        ("TEXTCOLOR", (3, total_row_idx), (-1, total_row_idx), colors.white),
        ("FONTNAME", (3, total_row_idx), (-1, total_row_idx), "Helvetica-Bold"),
        ("FONTSIZE", (3, total_row_idx), (-1, total_row_idx), 11),
        ("TOPPADDING", (0, total_row_idx), (-1, total_row_idx), 10),
        ("BOTTOMPADDING", (0, total_row_idx), (-1, total_row_idx), 10),
    ])

    # Subtotal rows styling
    for i in range(total_row_idx - 3, total_row_idx):
        style_cmds.append(("FONTNAME", (3, i), (-1, i), "Helvetica-Bold"))
        style_cmds.append(("FONTSIZE", (3, i), (-1, i), 9))
        if i == total_row_idx - 3:
            style_cmds.append(("LINEABOVE", (3, i), (-1, i), 1, KLIQ_BORDER))

    items_table.setStyle(TableStyle(style_cmds))
    elements.append(items_table)

    elements.append(Spacer(1, 10 * mm))

    # ── Payment Notes ──
    elements.append(HRFlowable(
        width="100%", thickness=0.5, color=KLIQ_BORDER, spaceAfter=6
    ))

    notes_style = ParagraphStyle(
        "Notes",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#888888"),
        leading=12,
    )
    elements.append(Paragraph(
        "<b>Payment Schedule:</b> Payouts are processed on the 10th of each month. "
        "Apple pays out ~33 days after fiscal month end. "
        "Google pays out on the 15th of the following month.",
        notes_style,
    ))
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(
        "<b>Fee Breakdown:</b> Platform fees (Apple/Google 30%) are deducted by the platform before proceeds. "
        f"KLIQ fee ({kliq_fee_pct:.1f}%) is calculated on gross sales.",
        notes_style,
    ))

    elements.append(Spacer(1, 15 * mm))

    # ── Footer ──
    elements.append(HRFlowable(
        width="100%", thickness=1, color=KLIQ_DARK, spaceAfter=6
    ))
    elements.append(Paragraph(
        f"{COMPANY_NAME} · {COMPANY_ADDRESS.replace(chr(10), ' · ')} · {COMPANY_EMAIL} · {COMPANY_WEB}",
        styles["FooterText"],
    ))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()
