"""
KLIQ Growth Dashboard · Python UI Kit v2.0
Source: KLIQ Brand Guidelines V1 2023 · Digital Design System
Layout: Control Center Dashboard
Stack: Plotly · Streamlit
"""

# ═══════════════════════════════════════════════════════════════════
#  COLOUR TOKENS
# ═══════════════════════════════════════════════════════════════════

# ── Primary ──
GREEN = "#1C3838"
DARK = "#021111"
IVORY = "#FFFDFA"

# ── Secondary ──
TANGERINE = "#FF9F88"
LIME = "#DEFE9C"
ALPINE = "#9CF0FF"

# ── Tint Scales ──
TANGERINE_90 = "#FFB2A0"
TANGERINE_70 = "#FFC5B8"
TANGERINE_50 = "#FFD9CF"
TANGERINE_30 = "#FFECE7"
TANGERINE_10 = "#FFF5F3"
LIME_90 = "#E5FEB0"
LIME_70 = "#EBFEC4"
LIME_50 = "#F2FFD7"
LIME_30 = "#F8FFEB"
LIME_10 = "#FCFFF5"
ALPINE_90 = "#B0F3FF"
ALPINE_70 = "#C4F6FF"
ALPINE_50 = "#D7F9FF"
ALPINE_30 = "#EBFCFF"
ALPINE_10 = "#F5FEFF"

# ── Dashboard Surfaces ──
BG_PAGE = "#F2F3EE"
BG_CARD = "#FFFFFF"
BG_SIDEBAR = "#FFFFFF"
BORDER = "#E6E8E2"
BORDER_LIGHT = "#F0F1EC"

# ── Semantic ──
POSITIVE = "#15803D"
POSITIVE_BG = "#DCFCE7"
NEGATIVE = "#DC2626"
NEGATIVE_BG = "#FEE2E2"
ERROR = "#E85D4A"
NEUTRAL = "#8A9494"
CHART_LINE = "#4A7D9C"
PAYMENT = "#15803D"
CANCEL = "#8A9494"

# ── Chart Colour Sequences ──
CHART_SEQUENCE = [
    GREEN,
    TANGERINE,
    ALPINE,
    LIME,
    DARK,
    CHART_LINE,
    TANGERINE_70,
    LIME_70,
]
CHART_MONO_GREEN = [
    "#021111",
    "#1C3838",
    "#2E5454",
    "#4A7272",
    "#6B9090",
    "#8FB0B0",
    "#B5CDCD",
    "#DAEAEA",
]
CHART_DIVERGING = [
    "#E8574A",
    "#FF9F88",
    "#FFD9CF",
    "#F2F3EE",
    "#DEFE9C",
    "#8FCF5C",
    "#1C3838",
]

# ═══════════════════════════════════════════════════════════════════
#  SPACING TOKENS
# ═══════════════════════════════════════════════════════════════════
CARD_RADIUS = 16
CARD_PAD_T = 22
CARD_PAD_X = 24
CARD_PAD_B = 16
GRID_GAP = 16
TOPBAR_HEIGHT = 56
CONTENT_PAD = 24

# ═══════════════════════════════════════════════════════════════════
#  SHADOW TOKENS
# ═══════════════════════════════════════════════════════════════════
SHADOW_CARD = "0 1px 3px rgba(2,17,17,0.04), 0 4px 16px rgba(2,17,17,0.06)"
SHADOW_CARD_HOVER = "0 2px 6px rgba(2,17,17,0.06), 0 8px 28px rgba(2,17,17,0.09)"
SHADOW_SM = "0 1px 2px rgba(2,17,17,0.04)"

# ═══════════════════════════════════════════════════════════════════
#  PLOTLY TEMPLATE (v2.0)
# ═══════════════════════════════════════════════════════════════════
PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": BG_PAGE,
        "plot_bgcolor": BG_PAGE,
        "font": {
            "family": "Sora, Verdana, Segoe UI, system-ui, sans-serif",
            "color": DARK,
            "size": 13,
        },
        "title": {
            "font": {"size": 14, "color": DARK, "weight": 500},
            "x": 0,
            "xanchor": "left",
            "pad": {"l": 0, "t": 8},
        },
        "colorway": CHART_SEQUENCE,
        "xaxis": {
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "tickfont": {"size": 11, "color": NEUTRAL},
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": "#E8EBE8",
            "gridwidth": 0.6,
            "showline": False,
            "zeroline": False,
            "tickfont": {"size": 11, "color": NEUTRAL},
            "automargin": True,
        },
        "legend": {
            "orientation": "h",
            "yanchor": "top",
            "y": -0.15,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 11},
        },
        "margin": {"l": 48, "r": 16, "t": 48, "b": 80},
        "hoverlabel": {
            "bgcolor": DARK,
            "font_color": IVORY,
            "font_size": 13,
            "bordercolor": "rgba(0,0,0,0)",
        },
    }
}


def register_plotly_template():
    """Register 'kliq' as the default Plotly template."""
    import plotly.io as pio

    pio.templates["kliq"] = PLOTLY_TEMPLATE
    pio.templates.default = "kliq"


# ═══════════════════════════════════════════════════════════════════
#  STREAMLIT CSS INJECTION (v2.0)
# ═══════════════════════════════════════════════════════════════════


def inject_css():
    """Inject KLIQ v2.0 brand CSS into Streamlit."""
    import streamlit as st

    st.markdown(
        '<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""<style>
/* ═══════════════════════════════════════════════════════════════════
   KLIQ CONTROL CENTER · v2.0
   Source: KLIQ Brand Guidelines V1 2023 + Digital Design System
   ═══════════════════════════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&display=swap');

/* ── CSS VARIABLES ───────────────────────────────────────────────── */
:root {{
    --green: {GREEN};
    --dark: {DARK};
    --ivory: {IVORY};
    --tangerine: {TANGERINE};
    --lime: {LIME};
    --alpine: {ALPINE};
    --bg-page: {BG_PAGE};
    --bg-card: {BG_CARD};
    --border: {BORDER};
    --border-light: {BORDER_LIGHT};
    --positive: {POSITIVE};
    --negative: {NEGATIVE};
    --neutral: {NEUTRAL};
    --shadow-card: {SHADOW_CARD};
    --shadow-card-hover: {SHADOW_CARD_HOVER};
    --card-radius: {CARD_RADIUS}px;
    --grid-gap: {GRID_GAP}px;
}}

/* ── GLOBAL RESET ────────────────────────────────────────────────── */
html, body, [class*="css"] {{
    font-family: 'Sora', sans-serif !important;
    color: var(--dark);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}

.stApp {{
    background-color: var(--bg-page);
}}

/* ── SCROLLBAR ───────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 10px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--neutral); }}

/* ── SIDEBAR ─────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background: var(--green) !important;
    border-right: none !important;
}}
[data-testid="stSidebar"] * {{
    color: var(--ivory) !important;
}}
[data-testid="stSidebar"] .stRadio label {{
    color: rgba(255,253,250,0.7) !important;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.005em;
    padding: 6px 0;
    transition: color 0.15s ease;
}}
[data-testid="stSidebar"] .stRadio label:hover {{
    color: var(--ivory) !important;
}}
[data-testid="stSidebar"] h2 {{
    color: var(--ivory) !important;
    font-weight: 600;
    font-size: 13px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 8px;
}}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label {{
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}}

/* ── PAGE TITLE ──────────────────────────────────────────────────── */
h1 {{
    font-size: 20px !important;
    font-weight: 700 !important;
    color: var(--dark) !important;
    letter-spacing: 0 !important;
    line-height: 1.2 !important;
}}

/* ── SUBHEADERS ──────────────────────────────────────────────────── */
h2 {{
    font-size: 17px !important;
    font-weight: 700 !important;
    color: var(--dark) !important;
    line-height: 1.2 !important;
}}
h3 {{
    font-size: 14px !important;
    font-weight: 600 !important;
    color: var(--dark) !important;
}}

/* ── KPI METRIC CARDS ────────────────────────────────────────────── */
[data-testid="stMetric"] {{
    background: var(--bg-card);
    border-radius: var(--card-radius);
    padding: {CARD_PAD_T}px {CARD_PAD_X}px {CARD_PAD_B}px;
    box-shadow: var(--shadow-card);
    border: 1px solid transparent;
    border-top: none;
    transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}}
[data-testid="stMetric"]:hover {{
    box-shadow: var(--shadow-card-hover);
    border-color: rgba(28,56,56,0.08);
    transform: translateY(-2px);
}}
[data-testid="stMetric"] label {{
    font-size: 13px !important;
    font-weight: 500 !important;
    letter-spacing: 0.005em !important;
    color: var(--neutral) !important;
    text-transform: none !important;
}}
[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    font-size: 28px !important;
    font-weight: 700 !important;
    color: var(--dark) !important;
    letter-spacing: -0.01em !important;
    line-height: 1.1 !important;
}}
[data-testid="stMetric"] [data-testid="stMetricDelta"] {{
    font-size: 13px !important;
    font-weight: 600 !important;
}}
[data-testid="stMetric"] [data-testid="stMetricDelta"][style*="color: green"],
[data-testid="stMetric"] [data-testid="stMetricDelta"] svg[style*="fill: green"] ~ span {{
    color: var(--positive) !important;
}}

/* ── CHART CONTAINERS ────────────────────────────────────────────── */
[data-testid="stPlotlyChart"] {{
    background: var(--bg-card);
    border-radius: var(--card-radius);
    box-shadow: var(--shadow-card);
    padding: 12px;
    border: 1px solid transparent;
    transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}}
[data-testid="stPlotlyChart"]:hover {{
    box-shadow: var(--shadow-card-hover);
    border-color: rgba(28,56,56,0.08);
}}

/* ── DATAFRAMES ──────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    background: var(--bg-card);
    border-radius: var(--card-radius);
    box-shadow: var(--shadow-card);
    overflow: hidden;
    border: 1px solid var(--border);
}}

/* ── DIVIDERS ────────────────────────────────────────────────────── */
hr {{
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 24px 0 !important;
}}

/* ── INFO / WARNING BOXES ────────────────────────────────────────── */
.stAlert {{
    border-radius: 12px;
    font-size: 13px;
    font-weight: 500;
}}

/* ── TABS ────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 2px;
    background: var(--border-light);
    padding: 4px;
    border-radius: 10px;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    padding: 8px 16px;
    color: var(--neutral);
    transition: all 0.15s ease;
}}
.stTabs [aria-selected="true"] {{
    background: var(--bg-card) !important;
    color: var(--dark) !important;
    box-shadow: {SHADOW_SM};
}}

/* ── BUTTONS ─────────────────────────────────────────────────────── */
.stButton > button {{
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 8px 24px !important;
    font-size: 13px !important;
    transition: all 0.2s ease !important;
    border: none !important;
    background: var(--green) !important;
    color: var(--ivory) !important;
}}
.stButton > button:hover {{
    background: var(--dark) !important;
    transform: translateY(-1px);
    box-shadow: {SHADOW_CARD};
}}
.stButton > button:active {{
    transform: translateY(0);
}}

/* ── FORM INPUTS ─────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stMultiSelect > div > div {{
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: border-color 0.15s ease !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: var(--green) !important;
    box-shadow: 0 0 0 2px rgba(28,56,56,0.1) !important;
}}

/* ── EXPANDER ────────────────────────────────────────────────────── */
.streamlit-expanderHeader {{
    font-size: 14px !important;
    font-weight: 600 !important;
    color: var(--dark) !important;
    background: var(--bg-card) !important;
    border-radius: 12px !important;
}}

/* ── SPINNER ─────────────────────────────────────────────────────── */
.stSpinner > div {{
    border-top-color: var(--green) !important;
}}

/* ── DELTA PILL (custom component) ───────────────────────────────── */
.kliq-delta {{
    display: inline-flex; align-items: center; gap: 3px;
    font-size: 13px; font-weight: 600;
    padding: 3px 10px; border-radius: 20px;
    font-family: 'Sora', sans-serif;
}}
.kliq-delta.positive {{ color: var(--positive); background: {POSITIVE_BG}; }}
.kliq-delta.negative {{ color: var(--negative); background: {NEGATIVE_BG}; }}

/* ── BADGE ───────────────────────────────────────────────────────── */
.kliq-badge {{
    display: inline-block; padding: 2px 10px;
    border-radius: 20px; font-size: 11px;
    font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.04em; font-family: 'Sora', sans-serif;
}}
.kliq-badge-active   {{ background: {LIME_30}; color: var(--green); }}
.kliq-badge-paused   {{ background: {TANGERINE_30}; color: #B35A3A; }}
.kliq-badge-inactive {{ background: var(--border-light); color: var(--neutral); }}
.kliq-badge-new      {{ background: {ALPINE_30}; color: #2A7D8E; }}

/* ── ANIMATIONS ──────────────────────────────────────────────────── */
@keyframes fadeSlideUp {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}

/* ── CARD ANIMATION ──────────────────────────────────────────────── */
[data-testid="stMetric"],
[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {{
    animation: fadeSlideUp 0.45s ease both;
}}

/* ── RESPONSIVE ──────────────────────────────────────────────────── */
@media (max-width: 768px) {{
    h1 {{ font-size: 18px !important; }}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        font-size: 22px !important;
    }}
}}
</style>""",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
#  HELPER: KPI Card HTML (for custom metric cards)
# ═══════════════════════════════════════════════════════════════════


def kpi_card(
    label: str, value: str, delta: str = "", delta_pct: float = 0, prev: str = ""
) -> str:
    """Return HTML for a KLIQ-styled KPI metric card."""
    delta_class = "positive" if delta_pct >= 0 else "negative"
    arrow = "↑" if delta_pct >= 0 else "↓"
    delta_html = ""
    if delta:
        delta_html = f'<span class="kliq-delta {delta_class}"><span style="font-size:11px">{arrow}</span> {delta}</span>'
    prev_html = (
        f'<span style="font-size:12px;color:{NEUTRAL};margin-left:8px;">from {prev}</span>'
        if prev
        else ""
    )

    return f"""
    <div style="
        background:{BG_CARD};
        border-radius:{CARD_RADIUS}px;
        padding:{CARD_PAD_T}px {CARD_PAD_X}px {CARD_PAD_B}px;
        box-shadow:{SHADOW_CARD};
        border:1px solid transparent;
        transition:all 0.25s cubic-bezier(0.4,0,0.2,1);
        display:flex; flex-direction:column; gap:8px;
    ">
        <div style="font-size:13px;font-weight:500;color:{NEUTRAL};letter-spacing:0.005em;">{label}</div>
        <div style="display:flex;align-items:baseline;justify-content:space-between;">
            <div>
                <span style="font-size:28px;font-weight:700;color:{DARK};letter-spacing:-0.01em;">{value}</span>
                {prev_html}
            </div>
            {delta_html}
        </div>
    </div>
    """


def section_header(title: str, subtitle: str = "") -> str:
    """Return HTML for a section header."""
    sub = (
        f'<p style="font-size:13px;color:{NEUTRAL};margin:4px 0 0;">{subtitle}</p>'
        if subtitle
        else ""
    )
    return f"""
    <div style="margin:24px 0 16px;">
        <h2 style="font-size:17px;font-weight:700;color:{DARK};margin:0;line-height:1.2;">{title}</h2>
        {sub}
    </div>
    """
