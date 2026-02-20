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
    apple_units=0,
    google_sales=0.0,
    google_units=0,
    kliq_fee_pct=0.0,
    total_payout=0.0,
    payment_date=None,
    apple_refunds=0.0,
    google_refunds=0.0,
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
    styles.add(
        ParagraphStyle(
            "KLIQTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            textColor=KLIQ_DARK,
            spaceAfter=2,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            "CompanyInfo",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#666666"),
            leading=13,
        )
    )
    styles.add(
        ParagraphStyle(
            "FieldLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=colors.HexColor("#888888"),
            spaceAfter=1,
        )
    )
    styles.add(
        ParagraphStyle(
            "FieldValue",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=KLIQ_DARK,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            "SectionHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=KLIQ_DARK,
            spaceBefore=12,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            "FooterText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#999999"),
            alignment=TA_CENTER,
        )
    )

    elements = []

    # ── Compute values ──
    subtotal = apple_sales + google_sales
    kliq_fee = round(subtotal * kliq_fee_pct / 100, 2)
    total_refunds = round(apple_refunds + google_refunds, 2)
    apple_platform_fee = round(apple_sales * 0.30, 2)
    google_platform_fee = round(google_sales * 0.15, 2)
    # total_payout comes from the table (after platform fees + KLIQ fee + refunds)

    invoice_num = _generate_invoice_number(app_name, month)
    if not payment_date:
        payment_date = f"10th of month following {month}"

    # ── Header: KLIQ branding + company info ──
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
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 4 * mm))

    # Divider
    elements.append(
        HRFlowable(width="100%", thickness=2, color=KLIQ_DARK, spaceAfter=8)
    )

    # ── Invoice Details ──
    elements.append(
        Paragraph("IN-APP PURCHASE PAYOUT RECEIPT", styles["SectionHeader"])
    )

    detail_data = [
        [
            Paragraph("App Name", styles["FieldLabel"]),
            Paragraph("Invoice #", styles["FieldLabel"]),
            Paragraph("Payment Date Range", styles["FieldLabel"]),
            Paragraph("Due Date", styles["FieldLabel"]),
        ],
        [
            Paragraph(app_name, styles["FieldValue"]),
            Paragraph(invoice_num, styles["FieldValue"]),
            Paragraph(month, styles["FieldValue"]),
            Paragraph(str(payment_date), styles["FieldValue"]),
        ],
    ]
    detail_table = Table(detail_data, colWidths=[45 * mm, 35 * mm, 40 * mm, 40 * mm])
    detail_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 1), (-1, 1), 0),
            ]
        )
    )
    elements.append(detail_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Line Items Table (matches reference PDF format) ──
    def fmt(v):
        return f"${v:,.2f}"

    line_items = [
        ["Description", "Total Sales", "Unit Price", "Total Price"],
    ]

    # Always show both platforms (show $0.00 if no sales, like the reference)
    apple_unit_price = round(apple_sales / apple_units, 2) if apple_units > 0 else 0.0
    google_unit_price = (
        round(google_sales / google_units, 2) if google_units > 0 else 0.0
    )

    line_items.append(
        [
            "Google Playstore",
            str(int(google_units)),
            fmt(google_unit_price),
            fmt(google_sales),
        ]
    )
    line_items.append(
        [
            "Apple Appstore",
            str(int(apple_units)),
            fmt(apple_unit_price),
            fmt(apple_sales),
        ]
    )

    # Blank separator row
    line_items.append(["", "", "", ""])

    # Subtotal (gross sales)
    line_items.append(["", "", "Subtotal", fmt(subtotal)])

    # Platform Fees — Apple 30%, Google 15%
    line_items.append(
        ["", "", "Apple Platform Fee (30%)", f"-{fmt(apple_platform_fee)}"]
    )
    line_items.append(
        ["", "", "Google Platform Fee (15%)", f"-{fmt(google_platform_fee)}"]
    )

    # KLIQ Fee
    line_items.append(
        ["", "", f"KLIQ Fee - *Gross Sales {kliq_fee_pct:.1f}%", f"-{fmt(kliq_fee)}"]
    )

    # Refunds (only show if > 0)
    if total_refunds > 0:
        line_items.append(["", "", "Refunds", f"-{fmt(total_refunds)}"])

    # Total Payout (passed from the table, after all deductions)
    line_items.append(["", "", "Total Payout", fmt(total_payout)])

    col_widths = [45 * mm, 30 * mm, 45 * mm, 40 * mm]
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
        # Grid on header
        ("GRID", (0, 0), (-1, 0), 0.5, KLIQ_DARK),
        ("LINEBELOW", (0, 0), (-1, 0), 1, KLIQ_DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Data row backgrounds
        ("BACKGROUND", (0, 1), (-1, 1), KLIQ_LIGHT_BG),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, KLIQ_BORDER),
        ("BACKGROUND", (0, 2), (-1, 2), colors.white),
        ("LINEBELOW", (0, 2), (-1, 2), 0.5, KLIQ_BORDER),
    ]

    total_row_idx = len(line_items) - 1
    # Walk backwards to find subtotal row (first row after blank separator)
    subtotal_row_idx = None
    for ri in range(total_row_idx - 1, 0, -1):
        if line_items[ri][2] == "Subtotal":
            subtotal_row_idx = ri
            break
    if subtotal_row_idx is None:
        subtotal_row_idx = total_row_idx - 4

    # Subtotal line above
    style_cmds.append(
        ("LINEABOVE", (2, subtotal_row_idx), (-1, subtotal_row_idx), 1, KLIQ_BORDER)
    )
    style_cmds.append(
        ("FONTNAME", (2, subtotal_row_idx), (-1, subtotal_row_idx), "Helvetica-Bold")
    )

    # Style deduction rows (between subtotal and total) as smaller text
    for di in range(subtotal_row_idx + 1, total_row_idx):
        style_cmds.append(("FONTNAME", (2, di), (-1, di), "Helvetica"))
        style_cmds.append(("FONTSIZE", (2, di), (-1, di), 9))
        # Highlight refund row in red if present
        if line_items[di][2] == "Refunds":
            style_cmds.append(
                ("TEXTCOLOR", (2, di), (-1, di), colors.HexColor("#C0392B"))
            )

    # Total row - bold and highlighted
    style_cmds.extend(
        [
            ("BACKGROUND", (2, total_row_idx), (-1, total_row_idx), KLIQ_DARK),
            ("TEXTCOLOR", (2, total_row_idx), (-1, total_row_idx), colors.white),
            ("FONTNAME", (2, total_row_idx), (-1, total_row_idx), "Helvetica-Bold"),
            ("FONTSIZE", (2, total_row_idx), (-1, total_row_idx), 11),
            ("TOPPADDING", (0, total_row_idx), (-1, total_row_idx), 10),
            ("BOTTOMPADDING", (0, total_row_idx), (-1, total_row_idx), 10),
        ]
    )

    items_table.setStyle(TableStyle(style_cmds))
    elements.append(items_table)

    elements.append(Spacer(1, 10 * mm))

    # ── Fee Note ──
    elements.append(
        HRFlowable(width="100%", thickness=0.5, color=KLIQ_BORDER, spaceAfter=6)
    )

    notes_style = ParagraphStyle(
        "Notes",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#888888"),
        leading=12,
    )
    elements.append(
        Paragraph(
            f"<b>*Gross Sales</b> — KLIQ fee ({kliq_fee_pct:.1f}%) is calculated on gross sales "
            f"(total customer price before any platform deductions).",
            notes_style,
        )
    )

    elements.append(Spacer(1, 15 * mm))

    # ── Footer ──
    elements.append(
        HRFlowable(width="100%", thickness=1, color=KLIQ_DARK, spaceAfter=6)
    )
    elements.append(
        Paragraph(
            f"{COMPANY_NAME} · {COMPANY_ADDRESS.replace(chr(10), ' · ')} · {COMPANY_EMAIL} · {COMPANY_WEB}",
            styles["FooterText"],
        )
    )

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()
