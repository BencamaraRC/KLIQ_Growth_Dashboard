"""
KLIQ Growth Dashboard · Dash UI Kit v1.0
Adapted from kliq_ui_kit.py (Streamlit version).
Provides colour tokens, Plotly template, and reusable Dash components.
"""

import plotly.io as pio
from dash import html, dcc
import dash_bootstrap_components as dbc

# ═══════════════════════════════════════════════════════════════════
#  COLOUR TOKENS
# ═══════════════════════════════════════════════════════════════════

GREEN = "#1C3838"
DARK = "#021111"
IVORY = "#FFFDFA"
TANGERINE = "#FF9F88"
LIME = "#DEFE9C"
ALPINE = "#9CF0FF"

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

BG_PAGE = "#F2F3EE"
BG_CARD = "#FFFFFF"
BG_SIDEBAR = GREEN
BORDER = "#E6E8E2"
BORDER_LIGHT = "#F0F1EC"

POSITIVE = "#15803D"
POSITIVE_BG = "#DCFCE7"
NEGATIVE = "#DC2626"
NEGATIVE_BG = "#FEE2E2"
ERROR = "#E85D4A"
NEUTRAL = "#8A9494"
CHART_LINE = "#4A7D9C"

CHART_SEQUENCE = [GREEN, TANGERINE, ALPINE, LIME, DARK, CHART_LINE, TANGERINE_70, LIME_70]

CARD_RADIUS = 16
SHADOW_CARD = "0 1px 3px rgba(2,17,17,0.04), 0 4px 16px rgba(2,17,17,0.06)"
SHADOW_CARD_HOVER = "0 2px 6px rgba(2,17,17,0.06), 0 8px 28px rgba(2,17,17,0.09)"

APPLE_COLOR = "#007AFF"
GOOGLE_COLOR = "#34A853"

# ═══════════════════════════════════════════════════════════════════
#  PLOTLY TEMPLATE
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
            "font": {"size": 14, "color": DARK},
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
    pio.templates["kliq"] = PLOTLY_TEMPLATE
    pio.templates.default = "kliq"


register_plotly_template()


# ═══════════════════════════════════════════════════════════════════
#  REUSABLE DASH COMPONENTS
# ═══════════════════════════════════════════════════════════════════


def kpi_card(label, value, subtitle="", color=None):
    """Return a styled KPI metric card as a Dash component."""
    bg = color or BG_CARD
    fg = IVORY if color else DARK
    label_color = "rgba(255,253,250,0.7)" if color else NEUTRAL

    return html.Div(
        [
            html.P(label, style={
                "margin": "0", "fontSize": "12px", "fontWeight": "600",
                "letterSpacing": "0.04em", "textTransform": "uppercase",
                "color": label_color,
            }),
            html.H2(value, style={
                "margin": "8px 0 4px", "fontSize": "1.75rem", "fontWeight": "700",
                "lineHeight": "1.1", "color": fg,
            }),
            html.P(subtitle, style={
                "margin": "0", "fontSize": "12px",
                "color": "rgba(255,253,250,0.6)" if color else NEUTRAL,
            }) if subtitle else None,
        ],
        style={
            "background": bg, "padding": "22px 24px 16px",
            "borderRadius": f"{CARD_RADIUS}px", "boxShadow": SHADOW_CARD,
            "border": "1px solid transparent",
            "transition": "all 0.25s cubic-bezier(0.4,0,0.2,1)",
        },
    )


def metric_card(label, value, subtitle=""):
    """Simple white metric card."""
    return kpi_card(label, value, subtitle)


def section_header(title, subtitle=""):
    """Section header component."""
    children = [
        html.H2(title, style={
            "fontSize": "17px", "fontWeight": "700", "color": DARK,
            "margin": "0", "lineHeight": "1.2",
        }),
    ]
    if subtitle:
        children.append(html.P(subtitle, style={
            "fontSize": "13px", "color": NEUTRAL, "margin": "4px 0 0",
        }))
    return html.Div(children, style={"margin": "24px 0 16px"})


def card_wrapper(children, **style_overrides):
    """Wrap content in a styled card."""
    style = {
        "background": BG_CARD,
        "borderRadius": f"{CARD_RADIUS}px",
        "boxShadow": SHADOW_CARD,
        "padding": "16px",
        "border": f"1px solid {BORDER}",
        "marginBottom": "16px",
    }
    style.update(style_overrides)
    return html.Div(children, style=style)


def chart_card(graph_component):
    """Wrap a dcc.Graph in a styled card."""
    return html.Div(
        graph_component,
        style={
            "background": BG_CARD,
            "borderRadius": f"{CARD_RADIUS}px",
            "boxShadow": SHADOW_CARD,
            "padding": "12px",
            "border": "1px solid transparent",
            "marginBottom": "16px",
        },
    )
