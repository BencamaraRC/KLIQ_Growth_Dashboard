"""
Dynamic cheat sheet PDF generator.
Creates a personalized "First 100 Paying Subscribers" guide using the
KLIQ brand template (warm cream bg, dark green accents, neo-brutalist cards).
Includes Trustpilot social proof and a Calendly book-a-call CTA.
"""

import os
import io
import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from config import CHEAT_SHEET_OUTPUT_DIR


# ── KLIQ brand colours (from email template) ──
CREAM_BG = HexColor("#FFFAF1")
DARK_GREEN = HexColor("#1C3838")
CARD_GREEN = HexColor("#F9FFED")
CARD_PINK = HexColor("#F9DAD1")
CARD_BLUE = HexColor("#DEF8FE")
TEXT_DARK = HexColor("#1a1e25")
WHITE = HexColor("#FFFFFF")
LINK_TEAL = HexColor("#007593")

CALENDLY_URL = "calendly.com/joinkliq/kliq-pp-shortlist"
TRUSTPILOT_IMG_URL = "https://cdn.prod.website-files.com/65647c3f98f6814022ad8f6e/69457c876dacc720ac11b4dd_TrustPilot-43%2023.png"
KLIQ_BANNER_URL = "https://mcusercontent.com/db158da9fc81badbb3bb42c71/images/7d87a295-7a71-06d0-8043-43ff17d0fa7a.png"
KLIQ_FOOTER_URL = "https://mcusercontent.com/db158da9fc81badbb3bb42c71/images/324f5680-1bb7-7432-bc0e-cc86b6793f9d.png"

# ── Niche hero images (extracted from KLIQ brand deck) ──
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "niche_images")
NICHE_IMAGES = {
    "Fitness": os.path.join(ASSETS_DIR, "fitness.jpg"),
    "Business": os.path.join(ASSETS_DIR, "business.png"),
    "Lifestyle": os.path.join(ASSETS_DIR, "lifestyle.png"),
    "Executive": os.path.join(ASSETS_DIR, "executive.jpg"),
    "Healthcare": os.path.join(ASSETS_DIR, "healthcare.jpg"),
}
DEFAULT_NICHE_IMAGE = os.path.join(ASSETS_DIR, "default.jpg")


# ── Niche-specific tips ──
NICHE_TIPS = {
    "Fitness": {
        "title": "Fitness Coach",
        "hook": "Transform bodies AND your business",
        "tips": [
            (
                "Launch a 30-Day Challenge Program",
                "Create a structured program with daily workouts. Offer it free for the first 10 sign-ups to build social proof, then charge £29/month.",
            ),
            (
                "Go Live 3x Per Week",
                "Live sessions create urgency and community. Schedule consistent times so subscribers know when to show up.",
            ),
            (
                "Build a Recipe Collection",
                "Pair your workouts with nutrition content. Coaches who add recipes see 40% higher retention.",
            ),
            (
                "Create a Community Space",
                "Post daily tips, celebrate member wins, and run weekly Q&As. Community is the #1 retention driver.",
            ),
            (
                "Offer 1-to-1 Premium Coaching",
                "Charge £99-199/month for personalised plans. Even 10 premium clients = £1,000-2,000/month.",
            ),
        ],
    },
    "Business": {
        "title": "Business Coach",
        "hook": "Scale your expertise into recurring revenue",
        "tips": [
            (
                "Create a Signature eCourse",
                "Package your methodology into 6-8 modules. Price at £97-297 for self-paced access.",
            ),
            (
                "Host Weekly Live Masterminds",
                "Live group coaching sessions create high perceived value. Charge £49-99/month for access.",
            ),
            (
                "Build a Resource Library",
                "Upload templates, worksheets, and frameworks. This passive content keeps subscribers engaged between live sessions.",
            ),
            (
                "Launch a Community Forum",
                "Peer-to-peer networking is incredibly valuable for business coaches. Members stay for the connections.",
            ),
            (
                "Offer VIP 1-to-1 Strategy Calls",
                "Premium tier at £299-499/month. Position as 'direct access to you' — your most profitable offering.",
            ),
        ],
    },
    "Executive": {
        "title": "Executive Coach",
        "hook": "Premium positioning for premium clients",
        "tips": [
            (
                "Create a Leadership Assessment Program",
                "Build a structured 12-week program with weekly modules. Price at £197-497 for the program.",
            ),
            (
                "Host Exclusive Live Roundtables",
                "Monthly live sessions with Q&A. Executive clients value exclusivity and direct access.",
            ),
            (
                "Build a Frameworks Library",
                "Decision-making templates, leadership models, and strategic planning tools. High-value passive content.",
            ),
            (
                "Launch a Private Community",
                "Curated peer groups for executives. The networking value alone justifies £99-199/month.",
            ),
            (
                "Offer Retainer Coaching",
                "Monthly retainer at £500-1,500. Executives expect premium pricing — don't undersell.",
            ),
        ],
    },
    "Lifestyle": {
        "title": "Lifestyle Coach",
        "hook": "Turn your passion into a thriving membership",
        "tips": [
            (
                "Launch a Step-by-Step Program",
                "Break your expertise into a beginner-friendly program. 4-6 weeks works perfectly for lifestyle niches.",
            ),
            (
                "Go Live Weekly",
                "Show your process in real-time. Live content feels authentic and builds trust faster than pre-recorded.",
            ),
            (
                "Create a Blog Series",
                "Write about your journey, tips, and behind-the-scenes. Blog content drives organic discovery.",
            ),
            (
                "Build a Community Around Your Niche",
                "People join for the content but stay for the community. Make it a welcoming space.",
            ),
            (
                "Offer Personalised Consultations",
                "1-to-1 sessions at £49-99 each. Even a few per week adds up significantly.",
            ),
        ],
    },
    "Healthcare": {
        "title": "Healthcare Coach",
        "hook": "Evidence-based coaching at scale",
        "tips": [
            (
                "Create Structured Wellness Programs",
                "Build programs around specific health goals (stress, sleep, nutrition). 8-12 week programs work well.",
            ),
            (
                "Host Live Q&A Sessions",
                "Weekly live sessions build trust and allow you to address individual concerns in a group setting.",
            ),
            (
                "Build an Educational Library",
                "Upload guides, infographics, and explainer videos. Educational content positions you as an authority.",
            ),
            (
                "Launch a Support Community",
                "Peer support is powerful in healthcare. Create a safe, moderated space for members.",
            ),
            (
                "Offer 1-to-1 Consultations",
                "Premium personalised sessions at £79-149. Healthcare clients value individual attention.",
            ),
        ],
    },
}

DEFAULT_TIPS = NICHE_TIPS["Fitness"]

# Card colours cycle for the 5 steps
CARD_COLOURS = [CARD_GREEN, CARD_BLUE, CARD_PINK, CARD_GREEN, CARD_BLUE]


def _download_image(url, max_width=None, max_height=None):
    """Download an image from URL and return as a ReportLab Image object."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        img_data = io.BytesIO(resp.content)
        img = Image(img_data)
        iw, ih = img.drawWidth, img.drawHeight
        if max_width and iw > max_width:
            ratio = max_width / iw
            img.drawWidth = max_width
            img.drawHeight = ih * ratio
        if max_height and img.drawHeight > max_height:
            ratio = max_height / img.drawHeight
            img.drawHeight = max_height
            img.drawWidth = img.drawWidth * ratio
        return img
    except Exception as e:
        print(f"[PDF] Could not download image {url}: {e}")
        return None


def _make_card(content_elements, bg_color, card_width):
    """Wrap content in a neo-brutalist card (thick bottom/right border)."""
    inner = Table(
        [[e] for e in content_elements],
        colWidths=[card_width - 24],
    )
    inner.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    card = Table([[inner]], colWidths=[card_width - 24])
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                ("BOX", (0, 0), (-1, -1), 1.5, black),
                ("LINEAFTER", (0, 0), (-1, -1), 3, black),
                ("LINEBELOW", (0, 0), (-1, -1), 5, black),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ]
        )
    )
    return card


def generate_cheat_sheet(prospect, output_path=None):
    """
    Generate a personalised cheat sheet PDF for a prospect.
    Uses the KLIQ brand template with Trustpilot social proof and Calendly CTA.

    Returns:
        Path to the generated PDF.
    """
    name = prospect.get("name", "Coach")
    first_name = prospect.get("first_name") or (name.split()[0] if name else "Coach")
    coach_type = prospect.get("coach_type", "Fitness")
    app_name = prospect.get("app_name", "your app")
    app_id = prospect.get("application_id", "unknown")

    niche = NICHE_TIPS.get(coach_type, DEFAULT_TIPS)

    if output_path is None:
        output_path = os.path.join(CHEAT_SHEET_OUTPUT_DIR, f"cheatsheet_{app_id}.pdf")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    page_width = A4[0] - 4 * cm  # usable width
    styles = getSampleStyleSheet()

    # ── Custom styles ──
    title_style = ParagraphStyle(
        "CheatTitle",
        parent=styles["Title"],
        fontSize=26,
        textColor=DARK_GREEN,
        spaceAfter=4 * mm,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "CheatSubtitle",
        parent=styles["Normal"],
        fontSize=13,
        textColor=TEXT_DARK,
        spaceAfter=8 * mm,
        alignment=TA_CENTER,
        leading=18,
    )
    heading_style = ParagraphStyle(
        "CheatHeading",
        parent=styles["Heading2"],
        fontSize=16,
        textColor=DARK_GREEN,
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "CheatBody",
        parent=styles["Normal"],
        fontSize=11,
        textColor=TEXT_DARK,
        spaceAfter=3 * mm,
        leading=16,
    )
    step_title_style = ParagraphStyle(
        "StepTitle",
        parent=styles["Normal"],
        fontSize=13,
        textColor=DARK_GREEN,
        spaceAfter=2 * mm,
        fontName="Helvetica-Bold",
    )
    step_body_style = ParagraphStyle(
        "StepBody",
        parent=styles["Normal"],
        fontSize=10.5,
        textColor=TEXT_DARK,
        leading=15,
    )
    cta_style = ParagraphStyle(
        "CTA",
        parent=styles["Normal"],
        fontSize=14,
        textColor=WHITE,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        spaceAfter=0,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=9,
        textColor=HexColor("#888888"),
        alignment=TA_CENTER,
        spaceBefore=8 * mm,
    )

    elements = []

    # ── KLIQ Banner ──
    banner = _download_image(KLIQ_BANNER_URL, max_width=page_width)
    if banner:
        banner.hAlign = "CENTER"
        elements.append(banner)
        elements.append(Spacer(1, 8 * mm))

    # ── Niche Hero Image ──
    niche_img_path = NICHE_IMAGES.get(coach_type, DEFAULT_NICHE_IMAGE)
    if os.path.exists(niche_img_path):
        niche_img = Image(niche_img_path)
        iw, ih = niche_img.drawWidth, niche_img.drawHeight
        ratio = page_width / iw
        niche_img.drawWidth = page_width
        niche_img.drawHeight = ih * ratio
        # Cap height so it doesn't dominate the page
        max_h = 180
        if niche_img.drawHeight > max_h:
            ratio2 = max_h / niche_img.drawHeight
            niche_img.drawHeight = max_h
            niche_img.drawWidth = niche_img.drawWidth * ratio2
        niche_img.hAlign = "CENTER"
        elements.append(niche_img)
        elements.append(Spacer(1, 6 * mm))

    # ── Title ──
    elements.append(Paragraph("Your First 100 Paying Subscribers", title_style))
    elements.append(
        Paragraph(
            f"A personalised guide for <b>{first_name}</b> — {niche['title']}",
            subtitle_style,
        )
    )
    elements.append(HRFlowable(width="100%", thickness=2, color=DARK_GREEN))
    elements.append(Spacer(1, 6 * mm))

    # ── Intro ──
    elements.append(Paragraph(f"Hey {first_name},", heading_style))
    elements.append(
        Paragraph(
            f"Welcome to KLIQ. You've taken the first step by setting up <b>{app_name}</b>. "
            f"As a {niche['title'].lower()}, here's your roadmap to "
            f"{niche['hook'].lower()}.",
            body_style,
        )
    )
    elements.append(Spacer(1, 4 * mm))

    # ── 5-Step Roadmap (neo-brutalist cards) ──
    elements.append(Paragraph("Your 5-Step Roadmap", heading_style))

    for i, (tip_title, tip_body) in enumerate(niche["tips"], 1):
        card_content = [
            Paragraph(f"Step {i}: {tip_title}", step_title_style),
            Paragraph(tip_body, step_body_style),
        ]
        card = _make_card(card_content, CARD_COLOURS[i - 1], page_width)
        elements.append(KeepTogether([card, Spacer(1, 4 * mm)]))

    elements.append(Spacer(1, 4 * mm))

    # ── Trustpilot social proof ──
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor("#DDDDDD")))
    elements.append(Spacer(1, 4 * mm))

    tp_img = _download_image(TRUSTPILOT_IMG_URL, max_width=page_width * 0.7)
    if tp_img:
        tp_img.hAlign = "CENTER"
        elements.append(tp_img)
        elements.append(Spacer(1, 2 * mm))

    elements.append(
        Paragraph(
            "Trusted by 100s of coaches worldwide",
            ParagraphStyle(
                "TPCaption",
                parent=styles["Normal"],
                fontSize=11,
                textColor=TEXT_DARK,
                alignment=TA_CENTER,
                spaceAfter=6 * mm,
            ),
        )
    )

    # ── Book a Call CTA ──
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph("Ready to fast-track your growth?", heading_style))
    elements.append(
        Paragraph(
            "We offer a <b>white-glove setup service</b> where our team builds out your app, "
            "creates your first program, and gets you launch-ready in 48 hours.",
            body_style,
        )
    )

    # CTA button as a styled table
    cta_text = Paragraph(
        f'<a href="https://{CALENDLY_URL}" color="white">Book a Free Setup Call</a>',
        cta_style,
    )
    cta_table = Table([[cta_text]], colWidths=[page_width * 0.6])
    cta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), DARK_GREEN),
                ("ROUNDEDCORNERS", [8, 8, 8, 8]),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    cta_table.hAlign = "CENTER"
    elements.append(Spacer(1, 3 * mm))
    elements.append(cta_table)

    elements.append(Spacer(1, 3 * mm))
    elements.append(
        Paragraph(
            f"Or visit: <b>{CALENDLY_URL}</b>",
            ParagraphStyle(
                "CTALink",
                parent=styles["Normal"],
                fontSize=10,
                textColor=LINK_TEAL,
                alignment=TA_CENTER,
            ),
        )
    )

    # ── Footer ──
    elements.append(Spacer(1, 10 * mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor("#DDDDDD")))

    footer_logo = _download_image(KLIQ_FOOTER_URL, max_width=page_width * 0.5)
    if footer_logo:
        footer_logo.hAlign = "CENTER"
        elements.append(Spacer(1, 4 * mm))
        elements.append(footer_logo)

    elements.append(
        Paragraph(
            "KLIQ — The all-in-one platform for coaches | joinkliq.io",
            footer_style,
        )
    )

    doc.build(elements)
    print(f"[PDF] Generated cheat sheet: {output_path}")
    return output_path


if __name__ == "__main__":
    test_prospect = {
        "name": "Britteny La'Shay",
        "first_name": "Britteny",
        "email": "thewfhbaddie@gmail.com",
        "coach_type": "Business",
        "app_name": "Britteny La'Shay",
        "application_id": "test_123",
    }
    path = generate_cheat_sheet(test_prospect)
    print(f"Test PDF saved to: {path}")
