"""
Page 1 — Acquisition
Signups, new customers, country breakdown, website traffic by channel,
GA4 sessions, signup funnel with drop-offs, device breakdown.
"""

import dash
from dash import html, dcc, callback, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kliq_ui import (
    GREEN, DARK, NEUTRAL, CHART_SEQUENCE, BG_CARD, CARD_RADIUS, SHADOW_CARD,
    metric_card, section_header, chart_card, card_wrapper,
)
from data import (
    load_growth_metrics, load_ga4_acquisition, load_ga4_traffic,
    load_ga4_funnel, load_device_type, load_onboarding_funnel,
    load_engagement_funnel,
)

dash.register_page(__name__, path="/acquisition", name="Acquisition", title="Acquisition — KLIQ")

DAYS_OPTIONS = [
    {"label": "Last 7 days", "value": 7},
    {"label": "Last 14 days", "value": 14},
    {"label": "Last 30 days", "value": 30},
    {"label": "Last 90 days", "value": 90},
    {"label": "All Time", "value": 9999},
]


def _filter_by_date(df, days_back, date_col="date"):
    if df.empty or date_col not in df.columns:
        return df
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    cutoff = datetime.now() - timedelta(days=days_back)
    return df[df[date_col] >= cutoff]


layout = html.Div([
    html.H1("Acquisition", style={"fontSize": "20px", "fontWeight": "700", "color": DARK}),
    html.Hr(),

    # Date filter
    dbc.Row([
        dbc.Col([
            dbc.Label("Date Range", style={"fontWeight": "600", "fontSize": "13px"}),
            dcc.Dropdown(
                id="acq-date-range",
                options=DAYS_OPTIONS,
                value=30,
                clearable=False,
                style={"fontSize": "13px"},
            ),
        ], md=3),
    ], className="mb-4"),

    # KPI cards
    dbc.Row(id="acq-kpi-row", className="mb-4"),

    html.Hr(),

    # Signups by Country
    section_header("🌍 Signups by Country"),
    dbc.Row([
        dbc.Col(chart_card(dcc.Graph(id="acq-country-chart")), md=8),
        dbc.Col(card_wrapper(html.Div(id="acq-country-table")), md=4),
    ]),

    html.Hr(),

    # Website Traffic by Channel
    section_header("📊 Website Traffic by Channel"),
    chart_card(dcc.Graph(id="acq-traffic-chart")),

    dbc.Row([
        dbc.Col(chart_card(dcc.Graph(id="acq-device-pie")), md=6),
        dbc.Col(chart_card(dcc.Graph(id="acq-country-sessions")), md=6),
    ]),

    html.Hr(),

    # Acquisition Sources
    section_header("🔗 Acquisition Sources"),
    dbc.Row([
        dbc.Col(chart_card(dcc.Graph(id="acq-source-chart")), md=6),
        dbc.Col(chart_card(dcc.Graph(id="acq-medium-pie")), md=6),
    ]),

    html.Hr(),

    # Sign-up Funnel
    section_header("🔽 Sign-up Funnel", "Started Sign-up → Created Account → Added Payment → Completed Payment"),
    dbc.Row([
        dbc.Col(chart_card(dcc.Graph(id="acq-signup-funnel")), md=8),
        dbc.Col(card_wrapper(html.Div(id="acq-signup-dropoff")), md=4),
    ]),

    html.Hr(),

    # Engagement Funnel
    section_header("⚡ Engagement Funnel", "Uploaded Profile → Created Livestream → Previewed App → Copied URL"),
    dbc.Row([
        dbc.Col(chart_card(dcc.Graph(id="acq-engagement-funnel")), md=8),
        dbc.Col(card_wrapper(html.Div(id="acq-engagement-dropoff")), md=4),
    ]),

    html.Hr(),

    # Device Breakdown
    section_header("📱 Device Breakdown"),
    chart_card(dcc.Graph(id="acq-device-breakdown")),
])


@callback(
    Output("acq-kpi-row", "children"),
    Output("acq-country-chart", "figure"),
    Output("acq-country-table", "children"),
    Output("acq-traffic-chart", "figure"),
    Output("acq-device-pie", "figure"),
    Output("acq-country-sessions", "figure"),
    Output("acq-source-chart", "figure"),
    Output("acq-medium-pie", "figure"),
    Output("acq-signup-funnel", "figure"),
    Output("acq-signup-dropoff", "children"),
    Output("acq-engagement-funnel", "figure"),
    Output("acq-engagement-dropoff", "children"),
    Output("acq-device-breakdown", "figure"),
    Input("acq-date-range", "value"),
)
def update_acquisition(days_back):
    import plotly.graph_objects as go

    empty_fig = go.Figure()
    empty_fig.update_layout(
        annotations=[{"text": "No data available", "xref": "paper", "yref": "paper",
                       "x": 0.5, "y": 0.5, "showarrow": False, "font": {"size": 14, "color": NEUTRAL}}],
        height=350,
    )

    # Load data
    growth = _filter_by_date(load_growth_metrics(), days_back, "week_start")
    acquisition = _filter_by_date(load_ga4_acquisition(), days_back)
    traffic = _filter_by_date(load_ga4_traffic(), days_back)
    devices = _filter_by_date(load_device_type(), days_back)
    onboarding = _filter_by_date(load_onboarding_funnel(), days_back)
    engagement = _filter_by_date(load_engagement_funnel(), days_back)

    # ── KPI Cards ──
    kpi_children = []

    # Signups
    if not growth.empty and "metric" in growth.columns and "value" in growth.columns:
        signups = growth[growth["metric"].str.contains("signup|sign_up|self_serve", case=False, na=False)]
        total_signups = int(signups["value"].sum()) if not signups.empty else 0
        kpi_children.append(dbc.Col(metric_card("Total Signups", f"{total_signups:,}"), md=3))
    else:
        kpi_children.append(dbc.Col(metric_card("Total Signups", "N/A"), md=3))

    # Customers
    if not growth.empty and "metric" in growth.columns:
        customers = growth[growth["metric"].str.contains("customer|upgrade|paid|convert", case=False, na=False)]
        total_customers = int(customers["value"].sum()) if not customers.empty else 0
        kpi_children.append(dbc.Col(metric_card("New Customers", f"{total_customers:,}" if total_customers > 0 else "N/A"), md=3))
    else:
        kpi_children.append(dbc.Col(metric_card("New Customers", "N/A"), md=3))

    # Sessions
    if not traffic.empty and "sessions" in traffic.columns:
        kpi_children.append(dbc.Col(metric_card("Website Sessions", f"{int(traffic['sessions'].sum()):,}"), md=3))
    else:
        kpi_children.append(dbc.Col(metric_card("Website Sessions", "N/A"), md=3))

    # Countries
    if not acquisition.empty and "country" in acquisition.columns:
        kpi_children.append(dbc.Col(metric_card("Countries", f"{acquisition['country'].nunique()}"), md=3))
    else:
        kpi_children.append(dbc.Col(metric_card("Countries", "N/A"), md=3))

    # ── Country Chart ──
    fig_country = empty_fig
    country_table = html.P("No data", style={"color": NEUTRAL})
    if not acquisition.empty and "country" in acquisition.columns and "unique_users" in acquisition.columns:
        country_agg = acquisition.groupby("country")["unique_users"].sum().nlargest(20).reset_index()
        fig_country = px.bar(
            country_agg, x="country", y="unique_users",
            title="Top 20 Countries by Unique Users",
            labels={"unique_users": "Users", "country": "Country"},
            color="unique_users",
            color_continuous_scale=[[0, "#9CF0FF"], [0.5, "#1C3838"], [1, "#021111"]],
        )
        fig_country.update_layout(height=400, xaxis_tickangle=-45)
        country_table = dash_table.DataTable(
            data=country_agg.to_dict("records"),
            columns=[{"name": c, "id": c} for c in country_agg.columns],
            style_table={"overflowX": "auto"},
            style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            page_size=20,
        )

    # ── Traffic Chart ──
    fig_traffic = empty_fig
    fig_device_pie = empty_fig
    fig_country_sessions = empty_fig
    if not traffic.empty and "channel" in traffic.columns and "sessions" in traffic.columns:
        traffic_c = traffic.copy()
        traffic_c["week"] = traffic_c["date"].dt.to_period("W").dt.start_time
        weekly = traffic_c.groupby(["week", "channel"])["sessions"].sum().reset_index()
        fig_traffic = px.line(
            weekly, x="week", y="sessions", color="channel",
            title="Weekly Sessions by Channel",
            labels={"sessions": "Sessions", "week": "Week"},
        )
        fig_traffic.update_layout(height=450)

        if "device_type" in traffic.columns:
            dev_agg = traffic.groupby("device_type")["sessions"].sum().reset_index()
            fig_device_pie = px.pie(dev_agg, names="device_type", values="sessions", title="Sessions by Device")
            fig_device_pie.update_layout(height=350)

        if "country" in traffic.columns:
            cs = traffic.groupby("country")["sessions"].sum().nlargest(15).reset_index()
            fig_country_sessions = px.bar(cs, x="country", y="sessions", title="Top 15 Countries by Sessions")
            fig_country_sessions.update_layout(height=350, xaxis_tickangle=-45)

    # ── Source Chart ──
    fig_source = empty_fig
    fig_medium = empty_fig
    if not acquisition.empty and "source" in acquisition.columns and "unique_users" in acquisition.columns:
        source_agg = acquisition.groupby("source")["unique_users"].sum().nlargest(15).reset_index()
        fig_source = px.bar(
            source_agg, x="source", y="unique_users",
            title="Top 15 Sources", labels={"unique_users": "Users", "source": "Source"},
        )
        fig_source.update_layout(height=400, xaxis_tickangle=-45)

        if "medium" in acquisition.columns:
            medium_agg = acquisition.groupby("medium")["unique_users"].sum().reset_index()
            fig_medium = px.pie(medium_agg, names="medium", values="unique_users", title="Users by Medium")
            fig_medium.update_layout(height=400)

    # ── Sign-up Funnel ──
    fig_signup = empty_fig
    signup_dropoff = html.P("No data", style={"color": NEUTRAL})
    if not onboarding.empty and "funnel_step" in onboarding.columns and "value" in onboarding.columns:
        ob_agg = onboarding.groupby(["funnel_step", "step_order"])["value"].sum().reset_index().sort_values("step_order")
        fig_signup = px.funnel(ob_agg, x="value", y="funnel_step", title="Sign-up Funnel")
        fig_signup.update_layout(height=400)

        ob_agg = ob_agg.reset_index(drop=True)
        ob_agg["drop_off"] = ob_agg["value"].diff(-1).fillna(0).astype(int)
        ob_agg["drop_off_pct"] = (ob_agg["drop_off"] / ob_agg["value"] * 100).round(1)
        signup_dropoff = [
            html.H6("Drop-off between steps:", style={"fontWeight": "600", "marginBottom": "8px"}),
            dash_table.DataTable(
                data=ob_agg[["funnel_step", "value", "drop_off", "drop_off_pct"]].rename(
                    columns={"funnel_step": "Step", "value": "Users", "drop_off": "Drop-off", "drop_off_pct": "Drop-off %"}
                ).to_dict("records"),
                columns=[{"name": c, "id": c} for c in ["Step", "Users", "Drop-off", "Drop-off %"]],
                style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            ),
        ]

    # ── Engagement Funnel ──
    fig_engagement = empty_fig
    engagement_dropoff = html.P("No data", style={"color": NEUTRAL})
    if not engagement.empty and "funnel_step" in engagement.columns and "value" in engagement.columns:
        eng_agg = engagement.groupby(["funnel_step", "step_order"])["value"].sum().reset_index().sort_values("step_order")
        fig_engagement = px.funnel(eng_agg, x="value", y="funnel_step", title="Engagement Funnel")
        fig_engagement.update_layout(height=400)

        eng_agg = eng_agg.reset_index(drop=True)
        eng_agg["drop_off"] = eng_agg["value"].diff(-1).fillna(0).astype(int)
        eng_agg["drop_off_pct"] = (eng_agg["drop_off"] / eng_agg["value"] * 100).round(1)
        engagement_dropoff = [
            html.H6("Drop-off between steps:", style={"fontWeight": "600", "marginBottom": "8px"}),
            dash_table.DataTable(
                data=eng_agg[["funnel_step", "value", "drop_off", "drop_off_pct"]].rename(
                    columns={"funnel_step": "Step", "value": "Users", "drop_off": "Drop-off", "drop_off_pct": "Drop-off %"}
                ).to_dict("records"),
                columns=[{"name": c, "id": c} for c in ["Step", "Users", "Drop-off", "Drop-off %"]],
                style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            ),
        ]

    # ── Device Breakdown ──
    fig_device = empty_fig
    if not devices.empty and "device_type" in devices.columns and "value" in devices.columns:
        dev_totals = devices.groupby("device_type")["value"].sum().reset_index()
        dev_totals = dev_totals[dev_totals["value"] > 0]
        fig_device = px.pie(dev_totals, names="device_type", values="value", title="Signups by Device Type")
        fig_device.update_layout(height=350)

    return (
        kpi_children, fig_country, country_table,
        fig_traffic, fig_device_pie, fig_country_sessions,
        fig_source, fig_medium,
        fig_signup, signup_dropoff,
        fig_engagement, engagement_dropoff,
        fig_device,
    )
