"""
KLIQ Growth Marketing & Activation Dashboard UI Kit
Based on KLIQ Brand Guidelines V1 (2023)
Typography: Sora Semibold (headings) / Sora Regular (body)
"""

# ── Brand Colours ──
GREEN = "#1C3838"
DARK = "#021111"
IVORY = "#FFFDFA"
TANGERINE = "#FF9F88"
LIME = "#DEFE9C"
ALPINE = "#9CF0FF"

TANGERINE_70 = "#FFC5B8"
TANGERINE_30 = "#FFECE7"
LIME_70 = "#EBFEC4"
LIME_30 = "#F8FFEB"
ALPINE_70 = "#C4F6FF"
ALPINE_30 = "#EBFCFF"

ERROR = "#E85D4A"
NEUTRAL = "#6B7F7F"

CHART_SEQUENCE = [
    GREEN,
    TANGERINE,
    LIME,
    ALPINE,
    DARK,
    TANGERINE_70,
    LIME_70,
    ALPINE_70,
]

# ── Plotly Template ──
PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": IVORY,
        "plot_bgcolor": IVORY,
        "font": {
            "family": "Sora, Inter, Helvetica Neue, Arial, sans-serif",
            "color": DARK,
            "size": 14,
        },
        "title": {
            "font": {"size": 18, "color": DARK},
            "x": 0,
            "xanchor": "left",
            "pad": {"l": 0, "t": 10},
        },
        "colorway": CHART_SEQUENCE,
        "xaxis": {
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "tickfont": {"size": 12, "color": NEUTRAL},
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": "#E8EBE8",
            "gridwidth": 0.6,
            "showline": False,
            "zeroline": False,
            "tickfont": {"size": 12, "color": NEUTRAL},
        },
        "legend": {
            "orientation": "h",
            "yanchor": "top",
            "y": -0.15,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 11},
        },
        "margin": {"l": 48, "r": 24, "t": 64, "b": 80},
        "hoverlabel": {
            "bgcolor": DARK,
            "font_color": IVORY,
            "font_size": 14,
            "bordercolor": "rgba(0,0,0,0)",
        },
    }
}


def register_plotly_template():
    """Register 'kliq' as a named Plotly template."""
    import plotly.io as pio

    pio.templates["kliq"] = PLOTLY_TEMPLATE
    pio.templates.default = "kliq"


def inject_css():
    """Inject KLIQ brand CSS into Streamlit."""
    import streamlit as st

    st.markdown(
        '<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""<style>
/* ── KLIQ Brand CSS ── */
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap');

/* Global */
html, body, [class*="css"] {{
    font-family: 'Sora', sans-serif !important;
    color: {DARK};
}}

.stApp {{
    background-color: #F4F5F0;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: {GREEN} !important;
}}
[data-testid="stSidebar"] * {{
    color: {IVORY} !important;
}}
[data-testid="stSidebar"] .stRadio label {{
    color: rgba(255,253,250,0.75) !important;
    font-size: 14px;
}}
[data-testid="stSidebar"] .stRadio label:hover {{
    color: {IVORY} !important;
}}
[data-testid="stSidebar"] h2 {{
    color: {IVORY} !important;
    font-weight: 600;
    letter-spacing: 0.5px;
}}

/* Page title */
h1 {{
    font-weight: 700 !important;
    color: {DARK} !important;
    letter-spacing: -0.5px;
}}

/* Subheaders */
h2, h3 {{
    font-weight: 600 !important;
    color: {DARK} !important;
}}

/* KPI Metric Cards */
[data-testid="stMetric"] {{
    background: {IVORY};
    border-radius: 12px;
    padding: 20px 16px;
    box-shadow: 0 2px 8px rgba(2,17,17,0.05);
    border-top: 3px solid {GREEN};
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}}
[data-testid="stMetric"]:hover {{
    box-shadow: 0 4px 16px rgba(2,17,17,0.10);
    transform: translateY(-1px);
}}

[data-testid="stMetric"] label {{
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
    color: {NEUTRAL} !important;
}}

[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    font-size: 28px !important;
    font-weight: 700 !important;
    color: {DARK} !important;
}}

[data-testid="stMetric"] [data-testid="stMetricDelta"] {{
    font-size: 13px !important;
    font-weight: 600 !important;
}}

/* Dataframes */
[data-testid="stDataFrame"] {{
    background: {IVORY};
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(2,17,17,0.05);
    overflow: hidden;
}}

/* Chart containers */
[data-testid="stPlotlyChart"] {{
    background: {IVORY};
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(2,17,17,0.05);
    padding: 8px;
}}

/* Dividers */
hr {{
    border: none !important;
    border-top: 1px solid #E8EBE8 !important;
    margin: 24px 0 !important;
}}

/* Info/warning boxes */
.stAlert {{
    border-radius: 10px;
    font-size: 14px;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: #F4F5F0;
    padding: 4px;
    border-radius: 10px;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 8px;
    font-weight: 600;
    font-size: 14px;
    padding: 8px 16px;
}}
.stTabs [aria-selected="true"] {{
    background: {IVORY} !important;
    box-shadow: 0 1px 3px rgba(2,17,17,0.06);
}}

/* Spinner */
.stSpinner > div {{
    border-top-color: {GREEN} !important;
}}

/* Scrollbar */
::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}
::-webkit-scrollbar-thumb {{
    background: {NEUTRAL};
    border-radius: 3px;
}}
::-webkit-scrollbar-track {{
    background: transparent;
}}
</style>""",
        unsafe_allow_html=True,
    )
