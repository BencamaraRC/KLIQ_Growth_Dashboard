"""
Page 4 — Coach Deep Dive
Growth stages, top coaches by GMV, GMV timeline, retention curve, feature impact.
"""

import dash
from dash import html, dcc, callback, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kliq_ui import (
    GREEN,
    DARK,
    TANGERINE,
    ALPINE,
    NEUTRAL,
    CHART_SEQUENCE,
    metric_card,
    section_header,
    chart_card,
    card_wrapper,
)
from data import (
    load_coach_growth_stages,
    load_coach_gmv_timeline,
    load_unified_revenue,
    load_coach_retention_curve,
    load_feature_retention_impact,
    load_firstweek_retention,
    load_app_health_score,
)

dash.register_page(
    __name__,
    path="/coach-deep-dive",
    name="Coach Deep Dive",
    title="Coach Deep Dive — KLIQ",
)


def _empty_fig(msg="No data available"):
    fig = go.Figure()
    fig.update_layout(
        annotations=[
            {
                "text": msg,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": NEUTRAL},
            }
        ],
        height=350,
    )
    return fig


layout = html.Div(
    [
        html.H1(
            "Coach Deep Dive",
            style={"fontSize": "20px", "fontWeight": "700", "color": DARK},
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Date Range",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dcc.Dropdown(
                            id="dd-date-range",
                            options=[
                                {"label": "Last 7 days", "value": 7},
                                {"label": "Last 14 days", "value": 14},
                                {"label": "Last 30 days", "value": 30},
                                {"label": "Last 90 days", "value": 90},
                                {"label": "All Time", "value": 99999},
                            ],
                            value=30,
                            clearable=False,
                            style={"fontSize": "13px"},
                        ),
                    ],
                    md=3,
                ),
            ],
            className="mb-4",
        ),
        # KPI cards
        dbc.Row(id="dd-kpi-row", className="mb-3"),
        html.Hr(),
        # Growth Stages
        section_header("📊 Coach Growth Stages"),
        dbc.Row(
            [
                dbc.Col(card_wrapper(html.Div(id="dd-stage-table")), md=4),
                dbc.Col(chart_card(dcc.Graph(id="dd-stage-pie")), md=8),
            ]
        ),
        html.Hr(),
        # Top Coaches
        section_header("🏆 Top Coaches by GMV"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Number of coaches",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dcc.Slider(
                            id="dd-top-n",
                            min=10,
                            max=50,
                            step=5,
                            value=20,
                            marks={i: str(i) for i in range(10, 55, 10)},
                        ),
                    ],
                    md=4,
                ),
            ],
            className="mb-3",
        ),
        chart_card(dcc.Graph(id="dd-top-chart")),
        card_wrapper(html.Div(id="dd-top-table")),
        html.Hr(),
        # GMV Timeline
        section_header("📈 GMV Timeline"),
        chart_card(dcc.Graph(id="dd-gmv-timeline")),
        html.Hr(),
        # Retention Curve
        section_header("📉 Coach Retention Curve"),
        chart_card(dcc.Graph(id="dd-retention-curve")),
        html.Hr(),
        # Feature Impact
        section_header("⚡ Feature Impact on Retention"),
        dbc.Tabs(
            [
                dbc.Tab(
                    label="Feature Retention Lift",
                    children=[
                        chart_card(dcc.Graph(id="dd-feature-impact")),
                        card_wrapper(html.Div(id="dd-feature-table")),
                    ],
                ),
                dbc.Tab(
                    label="First Week Activity",
                    children=[
                        chart_card(dcc.Graph(id="dd-firstweek")),
                    ],
                ),
            ]
        ),
        html.Hr(),
        # Health Scores
        section_header("🏥 App Health Scores"),
        card_wrapper(html.Div(id="dd-health-table")),
        # Hidden trigger for initial load
        dcc.Store(id="dd-trigger", data=True),
    ]
)


@callback(
    Output("dd-kpi-row", "children"),
    Output("dd-stage-table", "children"),
    Output("dd-stage-pie", "figure"),
    Output("dd-top-chart", "figure"),
    Output("dd-top-table", "children"),
    Output("dd-gmv-timeline", "figure"),
    Output("dd-retention-curve", "figure"),
    Output("dd-feature-impact", "figure"),
    Output("dd-feature-table", "children"),
    Output("dd-firstweek", "figure"),
    Output("dd-health-table", "children"),
    Input("dd-top-n", "value"),
    Input("dd-date-range", "value"),
    Input("dd-trigger", "data"),
)
def update_deep_dive(top_n, days_back, _):
    stages = load_coach_growth_stages()
    gmv_timeline = load_coach_gmv_timeline()
    unified_rev = load_unified_revenue()

    # Apply date range filter
    if days_back and days_back < 99999:
        cutoff_month = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m")
        if not gmv_timeline.empty and "month" in gmv_timeline.columns:
            gmv_timeline = gmv_timeline[gmv_timeline["month"] >= cutoff_month].copy()
        if not unified_rev.empty and "month" in unified_rev.columns:
            unified_rev = unified_rev[unified_rev["month"] >= cutoff_month].copy()

    total_gmv = (
        unified_rev["revenue"].sum()
        if not unified_rev.empty and "revenue" in unified_rev.columns
        else 0
    )

    # KPIs
    kpi = [
        dbc.Col(
            metric_card(
                "Total Coaches", f"{len(stages):,}" if not stages.empty else "0"
            ),
            md=3,
        ),
        dbc.Col(metric_card("Total GMV", f"${total_gmv:,.0f}"), md=3),
        dbc.Col(
            metric_card(
                "With Revenue",
                (
                    f"{len(stages[stages['total_gmv'] > 0]):,}"
                    if not stages.empty and "total_gmv" in stages.columns
                    else "N/A"
                ),
            ),
            md=3,
        ),
        dbc.Col(
            metric_card(
                "Total MRR",
                (
                    f"${stages['mrr'].sum():,.0f}"
                    if not stages.empty and "mrr" in stages.columns
                    else "N/A"
                ),
            ),
            md=3,
        ),
    ]

    # Growth Stages
    stage_table = html.P("No data", style={"color": NEUTRAL})
    fig_stage = _empty_fig("No stage data")
    if not stages.empty and "growth_stage" in stages.columns:
        sc = stages["growth_stage"].value_counts().reset_index()
        sc.columns = ["Stage", "Count"]
        stage_table = dash_table.DataTable(
            data=sc.to_dict("records"),
            columns=[{"name": c, "id": c} for c in sc.columns],
            style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
        )
        fig_stage = px.pie(
            sc,
            names="Stage",
            values="Count",
            title="Coach Distribution by Growth Stage",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_stage.update_layout(height=350)

    # Top Coaches
    fig_top = _empty_fig("No GMV data")
    top_table = html.P("No data", style={"color": NEUTRAL})
    if (
        not stages.empty
        and "total_gmv" in stages.columns
        and "application_name" in stages.columns
    ):
        top = stages.nlargest(top_n or 20, "total_gmv")
        fig_top = px.bar(
            top,
            x="application_name",
            y="total_gmv",
            title=f"Top {top_n or 20} Coaches by Total GMV",
            labels={"total_gmv": "GMV ($)", "application_name": "Coach"},
            color="total_gmv",
            color_continuous_scale=[[0, "#9CF0FF"], [0.5, "#1C3838"], [1, "#021111"]],
        )
        fig_top.update_layout(height=500, xaxis_tickangle=-45)
        display_cols = [
            "application_name",
            "total_gmv",
            "mrr",
            "total_subs",
            "growth_stage",
            "active_months",
        ]
        available = [c for c in display_cols if c in top.columns]
        top_table = dash_table.DataTable(
            data=top[available].to_dict("records"),
            columns=[{"name": c, "id": c} for c in available],
            style_cell={
                "fontSize": "12px",
                "padding": "6px",
                "fontFamily": "Sora",
                "textAlign": "left",
            },
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            sort_action="native",
        )

    # GMV Timeline
    fig_gmv = _empty_fig("No timeline data")
    if not gmv_timeline.empty and "application_name" in gmv_timeline.columns:
        gmv_col = next(
            (
                c
                for c in ["monthly_gmv", "gmv", "total_gmv"]
                if c in gmv_timeline.columns
            ),
            None,
        )
        if gmv_col:
            top_coaches = (
                gmv_timeline.groupby("application_name")[gmv_col]
                .sum()
                .nlargest(10)
                .index.tolist()
            )
            filtered = gmv_timeline[gmv_timeline["application_name"].isin(top_coaches)]
            if not filtered.empty:
                fig_gmv = px.line(
                    filtered,
                    x="month",
                    y=gmv_col,
                    color="application_name",
                    title="Monthly GMV — Top 10 Coaches",
                    labels={gmv_col: "GMV ($)", "month": "Month"},
                )
                fig_gmv.update_layout(height=500)

    # Retention Curve
    fig_ret = _empty_fig("No retention data")
    try:
        curve = load_coach_retention_curve()
        if not curve.empty and "period" in curve.columns and "pct" in curve.columns:
            fig_ret = px.line(
                curve,
                x="period",
                y="pct",
                title="Coach Retention Curve",
                markers=True,
                labels={"pct": "Retention %", "period": "Period"},
            )
            fig_ret.update_layout(height=400)
    except Exception as _e:
        print(f"[coach_deep_dive] chart error: {_e}")

    # Feature Impact
    fig_impact = _empty_fig("No feature impact data")
    feature_table = html.P("No data", style={"color": NEUTRAL})
    try:
        impact = load_feature_retention_impact()
        if (
            not impact.empty
            and "feature" in impact.columns
            and "lift_pp" in impact.columns
        ):
            agg = (
                impact.groupby("feature")
                .agg(
                    avg_lift=("lift_pp", "mean"),
                    avg_retention_used=("retention_if_used", "mean"),
                    avg_retention_not_used=("retention_if_not_used", "mean"),
                )
                .reset_index()
                .sort_values("avg_lift", ascending=False)
            )
            fig_impact = px.bar(
                agg,
                x="feature",
                y="avg_lift",
                title="Average Retention Lift by Feature (pp)",
                labels={"avg_lift": "Lift (pp)", "feature": "Feature"},
                color="avg_lift",
                color_continuous_scale="RdYlGn",
            )
            fig_impact.update_layout(height=400)
            feature_table = dash_table.DataTable(
                data=agg.round(1).to_dict("records"),
                columns=[{"name": c, "id": c} for c in agg.columns],
                style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            )
    except Exception as _e:
        print(f"[coach_deep_dive] chart error: {_e}")

    # First Week
    fig_fw = _empty_fig("No first-week data")
    try:
        fw = load_firstweek_retention()
        if not fw.empty and "active_days_first_week" in fw.columns:
            agg_fw = (
                fw.groupby("active_days_first_week")
                .agg(
                    avg_retention=("retention_30d_pct", "mean"),
                    total_users=("users", "sum"),
                )
                .reset_index()
            )
            fig_fw = px.bar(
                agg_fw,
                x="active_days_first_week",
                y="avg_retention",
                title="Active Days in Week 1 → 30-Day Retention",
                labels={
                    "avg_retention": "Retention %",
                    "active_days_first_week": "Active Days",
                },
                text="total_users",
            )
            fig_fw.update_layout(height=350)
    except Exception as _e:
        print(f"[coach_deep_dive] chart error: {_e}")

    # Health Scores
    health_table = html.P("No data", style={"color": NEUTRAL})
    try:
        health = load_app_health_score()
        if not health.empty:
            health_table = dash_table.DataTable(
                data=health.to_dict("records"),
                columns=[{"name": c, "id": c} for c in health.columns],
                style_table={"overflowX": "auto"},
                style_cell={
                    "fontSize": "12px",
                    "padding": "6px",
                    "fontFamily": "Sora",
                    "textAlign": "left",
                },
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
                page_size=25,
                sort_action="native",
                filter_action="native",
            )
    except Exception as _e:
        print(f"[coach_deep_dive] chart error: {_e}")

    return (
        kpi,
        stage_table,
        fig_stage,
        fig_top,
        top_table,
        fig_gmv,
        fig_ret,
        fig_impact,
        feature_table,
        fig_fw,
        health_table,
    )
