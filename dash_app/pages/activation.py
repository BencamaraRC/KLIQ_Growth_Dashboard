"""
Page 2 — Activation
Coach activation score: measures whether new apps complete key setup actions
in their first 30 days. Predicts churn risk based on data-driven weights.
"""

import dash
from dash import html, dcc, callback, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kliq_ui import (
    GREEN,
    DARK,
    TANGERINE,
    ALPINE,
    ERROR,
    NEUTRAL,
    CHART_SEQUENCE,
    BG_CARD,
    CARD_RADIUS,
    SHADOW_CARD,
    POSITIVE,
    POSITIVE_BG,
    NEGATIVE,
    NEGATIVE_BG,
    metric_card,
    section_header,
    chart_card,
    card_wrapper,
)
from data import (
    load_activation_score,
    load_coach_onboarding_funnel,
    load_coach_retention_curve,
    load_cohort_retention,
    load_churn_analysis,
    load_app_lookup,
    load_coach_types,
)

dash.register_page(
    __name__, path="/activation", name="Activation", title="Activation — KLIQ"
)

ACTION_CONFIG = {
    "added_profile_image": {"label": "Profile Image", "weight": 10, "icon": "🖼️"},
    "created_module": {"label": "Created Module", "weight": 10, "icon": "📦"},
    "created_livestream": {"label": "Created Livestream", "weight": 10, "icon": "🎥"},
    "created_program": {"label": "Created Program", "weight": 10, "icon": "📋"},
    "previewed_app": {"label": "Previewed App", "weight": 15, "icon": "👁️"},
    "published_app": {"label": "Published App", "weight": 10, "icon": "🚀"},
    "added_blog_content": {"label": "Blog Content", "weight": 10, "icon": "📝"},
    "added_nutrition": {"label": "Nutrition Content", "weight": 10, "icon": "🥗"},
    "posted_community": {"label": "Community Post", "weight": 5, "icon": "💬"},
    "copied_url": {"label": "Copied URL", "weight": 5, "icon": "🔗"},
    "created_1to1": {"label": "1-to-1 Booking", "weight": 5, "icon": "📅"},
}
ACTION_COLS = list(ACTION_CONFIG.keys())

# ── Key Readiness Actions (equal weight, 1 pt each, max 4) ──
READINESS_ACTIONS = [
    "added_profile_image",  # Profile Image
    "previewed_app",  # Clicked Preview
    "copied_url",  # Copied URL
    "created_1to1",  # Created 1-to-1
]

TIME_OPTIONS = [
    {"label": "Last 7 days", "value": 7},
    {"label": "Last 14 days", "value": 14},
    {"label": "Last 30 days", "value": 30},
    {"label": "Last 90 days", "value": 90},
    {"label": "All Time", "value": 99999},
]

layout = html.Div(
    [
        html.H1(
            "Activation & Churn Prediction",
            style={"fontSize": "20px", "fontWeight": "700", "color": DARK},
        ),
        html.Hr(),
        # Filters
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Filter by App",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dcc.Dropdown(
                            id="act-app-filter",
                            options=[],
                            value="All Apps",
                            clearable=False,
                            style={"fontSize": "13px"},
                        ),
                    ],
                    md=3,
                ),
                dbc.Col(
                    [
                        dbc.Label(
                            "New Apps Time Filter",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dcc.Dropdown(
                            id="act-time-filter",
                            options=TIME_OPTIONS,
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
        dbc.Row(id="act-kpi-row", className="mb-3"),
        html.Hr(),
        # Coach Type Breakdown
        section_header(
            "🎯 Coach Type Breakdown", "What type of coach signed up during onboarding"
        ),
        chart_card(dcc.Graph(id="act-coach-type-chart")),
        html.Hr(),
        # Activation Score vs Retention
        section_header(
            "📊 Activation Score vs Retention",
            "Apps that complete more setup actions in their first 30 days are far more likely to stay active",
        ),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="act-score-dist")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="act-retention-by-score")), md=6),
            ]
        ),
        html.Hr(),
        # Action Impact
        section_header(
            "⚡ Action Impact on Retention",
            "Each action's retention lift: how much more likely an app is to stay active if the coach did this action",
        ),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="act-impact-chart")), md=8),
                dbc.Col(card_wrapper(html.Div(id="act-impact-table")), md=4),
            ]
        ),
        html.Hr(),
        # Action Completion Rates
        section_header("✅ Action Completion Rates (First 30 Days)"),
        chart_card(dcc.Graph(id="act-completion-chart")),
        html.Hr(),
        # Risk Breakdown
        section_header("🚦 Risk Level Breakdown"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="act-risk-pie")), md=6),
                dbc.Col(card_wrapper(html.Div(id="act-risk-table")), md=6),
            ]
        ),
        html.Hr(),
        # New Apps Detail
        section_header("📋 New Apps Detail"),
        dbc.Row(id="act-new-apps-kpi", className="mb-3"),
        section_header(
            "🎯 Readiness Score (4 Key Actions)",
            "Profile Image, Click Preview, Copy URL, Create 1-to-1 — 1 point each (max 4). "
            "Avg readiness for new apps in the selected time period.",
        ),
        dbc.Row(id="act-readiness-kpi", className="mb-3"),
        chart_card(dcc.Graph(id="act-readiness-timeseries")),
        card_wrapper(html.Div(id="act-new-apps-table")),
        html.Hr(),
        # Cohort Retention
        section_header("📊 Cohort Retention"),
        chart_card(dcc.Graph(id="act-cohort-heatmap")),
        html.Hr(),
        # Retention Curve
        section_header("📉 Coach Retention Curve"),
        chart_card(dcc.Graph(id="act-retention-curve")),
    ]
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


@callback(
    Output("act-app-filter", "options"),
    Input("act-app-filter", "value"),  # trigger on load
)
def populate_app_filter(_):
    apps = load_app_lookup()
    names = []
    if not apps.empty and "application_name" in apps.columns:
        names = sorted([n for n in apps["application_name"].dropna().unique() if n])
    return [{"label": "All Apps", "value": "All Apps"}] + [
        {"label": n, "value": n} for n in names
    ]


@callback(
    Output("act-kpi-row", "children"),
    Output("act-coach-type-chart", "figure"),
    Output("act-readiness-kpi", "children"),
    Output("act-readiness-timeseries", "figure"),
    Output("act-score-dist", "figure"),
    Output("act-retention-by-score", "figure"),
    Output("act-impact-chart", "figure"),
    Output("act-impact-table", "children"),
    Output("act-completion-chart", "figure"),
    Output("act-risk-pie", "figure"),
    Output("act-risk-table", "children"),
    Output("act-new-apps-kpi", "children"),
    Output("act-new-apps-table", "children"),
    Output("act-cohort-heatmap", "figure"),
    Output("act-retention-curve", "figure"),
    Input("act-app-filter", "value"),
    Input("act-time-filter", "value"),
)
def update_activation(selected_app, time_days):
    score_df = load_activation_score()

    # Filter by app
    df = score_df.copy()
    if (
        selected_app
        and selected_app != "All Apps"
        and not df.empty
        and "application_name" in df.columns
    ):
        df = df[df["application_name"] == selected_app]

    if df.empty:
        empty = _empty_fig("No activation data available")
        no_data = html.P("No data available.", style={"color": NEUTRAL})
        return (
            [],
            empty,
            [],
            empty,
            empty,
            empty,
            empty,
            no_data,
            empty,
            empty,
            no_data,
            [],
            no_data,
            empty,
            empty,
        )

    # ── KPI Cards ──
    total_apps = len(df)
    active_apps = int(df["is_active"].sum()) if "is_active" in df.columns else 0
    churned_apps = total_apps - active_apps
    avg_score = df["activation_score"].mean() if "activation_score" in df.columns else 0
    avg_actions = (
        df["actions_completed"].mean() if "actions_completed" in df.columns else 0
    )

    kpi_children = [
        dbc.Col(metric_card("Total Apps", f"{total_apps:,}"), md=2),
        dbc.Col(
            metric_card(
                "Active (90d)", f"{active_apps:,}", f"{active_apps/total_apps*100:.1f}%"
            ),
            md=2,
        ),
        dbc.Col(
            metric_card(
                "Churned", f"{churned_apps:,}", f"{churned_apps/total_apps*100:.1f}%"
            ),
            md=2,
        ),
        dbc.Col(metric_card("Avg Score", f"{avg_score:.0f}/100"), md=3),
        dbc.Col(metric_card("Avg Actions", f"{avg_actions:.1f}/11"), md=3),
    ]

    # ── Coach Type ──
    fig_ct = _empty_fig("No coach type data")
    try:
        ct_raw = load_coach_types()
        if not ct_raw.empty:
            ct_df = ct_raw.copy()
            ct_df["event_date"] = pd.to_datetime(ct_df["event_date"])
            ct_df = ct_df[
                ct_df["coach_type"].notna()
                & (ct_df["coach_type"] != "")
                & (ct_df["coach_type"].str.lower() != "test")
            ]
            cutoff = datetime.now() - timedelta(days=time_days)
            ct_filtered = ct_df[ct_df["event_date"] >= cutoff]
            if not ct_filtered.empty:
                cat_counts = (
                    ct_filtered.groupby("coach_type")
                    .size()
                    .reset_index(name="count")
                    .sort_values("count", ascending=False)
                )
                fig_ct = px.bar(
                    cat_counts,
                    x="coach_type",
                    y="count",
                    color="coach_type",
                    color_discrete_sequence=CHART_SEQUENCE,
                    labels={"coach_type": "Coach Type", "count": "Sign-ups"},
                    title="Coach Types at Onboarding",
                    text="count",
                )
                fig_ct.update_traces(texttemplate="%{text:,}", textposition="outside")
                fig_ct.update_layout(height=400, showlegend=False)
    except Exception as _e:
        print(f"[activation] chart error: {_e}")

    # Readiness defaults (computed later in New Apps Detail with time filter)
    readiness_kpi = []
    fig_readiness = _empty_fig("No readiness data")

    # ── Score Distribution ──
    score_bins = pd.cut(
        df["activation_score"],
        bins=[-1, 0, 10, 25, 50, 75, 100],
        labels=["0", "1-10", "11-25", "26-50", "51-75", "76-100"],
    )
    df_binned = df.copy()
    df_binned["score_bin"] = score_bins
    df_binned["status"] = df_binned["is_active"].map({1: "Active", 0: "Churned"})

    bin_counts = (
        df_binned.groupby(["score_bin", "status"]).size().reset_index(name="count")
    )
    fig_dist = px.bar(
        bin_counts,
        x="score_bin",
        y="count",
        color="status",
        title="Score Distribution: Active vs Churned",
        labels={"score_bin": "Activation Score", "count": "Apps"},
        barmode="group",
        color_discrete_map={"Active": GREEN, "Churned": ERROR},
    )
    fig_dist.update_layout(height=400)

    # Retention by score
    ret_by_score = (
        df_binned.groupby("score_bin")
        .agg(total=("is_active", "count"), active=("is_active", "sum"))
        .reset_index()
    )
    ret_by_score["retention_pct"] = (
        ret_by_score["active"] / ret_by_score["total"] * 100
    ).round(1)
    fig_ret = px.bar(
        ret_by_score,
        x="score_bin",
        y="retention_pct",
        title="Retention Rate by Activation Score",
        labels={"score_bin": "Activation Score", "retention_pct": "Retention %"},
        text="retention_pct",
    )
    fig_ret.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside", marker_color=GREEN
    )
    fig_ret.update_layout(height=400, yaxis_range=[0, 105])

    # ── Action Impact ──
    impact_data = []
    for col, cfg in ACTION_CONFIG.items():
        if col in df.columns:
            did = df[df[col] == 1]
            didnt = df[df[col] == 0]
            did_rate = did["is_active"].mean() * 100 if len(did) > 0 else 0
            didnt_rate = didnt["is_active"].mean() * 100 if len(didnt) > 0 else 0
            lift = did_rate - didnt_rate
            impact_data.append(
                {
                    "Action": f"{cfg['icon']} {cfg['label']}",
                    "Weight": cfg["weight"],
                    "Apps Did It": len(did),
                    "Retention If Done": f"{did_rate:.1f}%",
                    "Retention If Not": f"{didnt_rate:.1f}%",
                    "Lift": f"+{lift:.1f}pp",
                    "lift_val": lift,
                }
            )
    impact_df = pd.DataFrame(impact_data).sort_values("lift_val", ascending=True)
    fig_impact = px.bar(
        impact_df,
        x="lift_val",
        y="Action",
        orientation="h",
        title="Retention Lift by Action (percentage points)",
        labels={"lift_val": "Retention Lift (pp)", "Action": ""},
        text="lift_val",
    )
    fig_impact.update_traces(
        texttemplate="+%{text:.1f}pp", textposition="outside", marker_color=GREEN
    )
    fig_impact.update_layout(height=450)

    impact_table = dash_table.DataTable(
        data=impact_df[["Action", "Weight", "Apps Did It", "Retention If Done", "Lift"]]
        .sort_values("Weight", ascending=False)
        .to_dict("records"),
        columns=[
            {"name": c, "id": c}
            for c in ["Action", "Weight", "Apps Did It", "Retention If Done", "Lift"]
        ],
        style_cell={
            "fontSize": "12px",
            "padding": "6px",
            "fontFamily": "Sora",
            "textAlign": "left",
        },
        style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
    )

    # ── Completion Rates ──
    comp_data = []
    for col, cfg in ACTION_CONFIG.items():
        if col in df.columns:
            rate = df[col].mean() * 100
            comp_data.append({"Action": cfg["label"], "Completion %": round(rate, 1)})
    comp_df = pd.DataFrame(comp_data).sort_values("Completion %", ascending=True)
    fig_comp = px.bar(
        comp_df,
        x="Completion %",
        y="Action",
        orientation="h",
        title="% of Apps Completing Each Action in First 30 Days",
        text="Completion %",
    )
    fig_comp.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside", marker_color=TANGERINE
    )
    fig_comp.update_layout(height=400, xaxis_range=[0, 105])

    # ── Risk Breakdown ──
    risk_order = ["Critical", "High Risk", "Medium Risk", "Low Risk"]
    fig_risk = _empty_fig("No risk data")
    risk_table_content = html.P("No risk data", style={"color": NEUTRAL})
    if "risk_level" in df.columns:
        risk_counts = (
            df["risk_level"]
            .value_counts()
            .reindex(risk_order, fill_value=0)
            .reset_index()
        )
        risk_counts.columns = ["Risk Level", "Apps"]
        fig_risk = px.pie(
            risk_counts,
            names="Risk Level",
            values="Apps",
            title="Apps by Risk Level",
            color="Risk Level",
            color_discrete_map={
                "Critical": ERROR,
                "High Risk": TANGERINE,
                "Medium Risk": ALPINE,
                "Low Risk": GREEN,
            },
        )
        fig_risk.update_layout(height=400)

        risk_ret = (
            df.groupby("risk_level")
            .agg(
                total=("is_active", "count"),
                active=("is_active", "sum"),
                avg_score=("activation_score", "mean"),
            )
            .reindex(risk_order)
            .reset_index()
        )
        risk_ret["retention_pct"] = (
            risk_ret["active"] / risk_ret["total"] * 100
        ).round(1)
        risk_ret["avg_score"] = risk_ret["avg_score"].round(0)
        risk_ret.columns = ["Risk Level", "Total", "Active", "Avg Score", "Retention %"]
        risk_table_content = [
            html.H6("Risk Level Summary", style={"fontWeight": "600"}),
            dash_table.DataTable(
                data=risk_ret.to_dict("records"),
                columns=[{"name": c, "id": c} for c in risk_ret.columns],
                style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            ),
            html.Div(
                [
                    html.P(html.Strong("Interpretation:"), style={"marginTop": "12px"}),
                    html.Ul(
                        [
                            html.Li(
                                [
                                    html.Strong("Critical"),
                                    " (0 actions): Almost certain to churn",
                                ]
                            ),
                            html.Li(
                                [
                                    html.Strong("High Risk"),
                                    " (1-3 actions): Very likely to churn",
                                ]
                            ),
                            html.Li(
                                [
                                    html.Strong("Medium Risk"),
                                    " (4-6 actions): Needs nudging",
                                ]
                            ),
                            html.Li(
                                [
                                    html.Strong("Low Risk"),
                                    " (7+ actions): Healthy activation",
                                ]
                            ),
                        ],
                        style={"fontSize": "12px", "color": NEUTRAL},
                    ),
                ]
            ),
        ]

    # ── New Apps Detail ──
    time_filtered = (
        df[df["app_age_days"] <= time_days].copy()
        if "app_age_days" in df.columns
        else pd.DataFrame()
    )
    new_apps_kpi = []
    new_apps_table = html.P("No new apps in this period.", style={"color": NEUTRAL})

    if not time_filtered.empty:
        time_filtered = time_filtered.sort_values("created_date", ascending=False)
        n_new = len(time_filtered)
        crit = (
            len(time_filtered[time_filtered["risk_level"] == "Critical"])
            if "risk_level" in time_filtered.columns
            else 0
        )
        high = (
            len(time_filtered[time_filtered["risk_level"] == "High Risk"])
            if "risk_level" in time_filtered.columns
            else 0
        )
        avg_s = (
            time_filtered["activation_score"].mean()
            if "activation_score" in time_filtered.columns
            else 0
        )

        # Compute previous period avg score for comparison
        prev_period = (
            df[(df["app_age_days"] > time_days) & (df["app_age_days"] <= time_days * 2)]
            if "app_age_days" in df.columns
            else pd.DataFrame()
        )
        prev_avg = (
            prev_period["activation_score"].mean()
            if (not prev_period.empty and "activation_score" in prev_period.columns)
            else None
        )

        # Build score change indicator
        if prev_avg is not None and prev_avg > 0:
            score_delta = avg_s - prev_avg
            pct_change = (score_delta / prev_avg) * 100
            is_up = score_delta >= 0
            arrow = "▲" if is_up else "▼"
            color = POSITIVE if is_up else NEGATIVE
            badge_bg = POSITIVE_BG if is_up else NEGATIVE_BG
            period_label = {7: "7d", 14: "14d", 30: "30d", 90: "90d"}.get(
                time_days, f"{time_days}d"
            )
            change_badge = html.Div(
                [
                    html.Span(
                        f"{arrow} {abs(pct_change):.1f}%",
                        style={
                            "color": color,
                            "fontWeight": "700",
                            "fontSize": "14px",
                            "marginRight": "6px",
                        },
                    ),
                    html.Span(
                        f"vs prev {period_label}",
                        style={
                            "color": NEUTRAL,
                            "fontSize": "11px",
                            "fontWeight": "500",
                        },
                    ),
                ],
                style={
                    "display": "inline-flex",
                    "alignItems": "center",
                    "background": badge_bg,
                    "padding": "4px 10px",
                    "borderRadius": "8px",
                    "marginTop": "6px",
                },
            )
            score_subtitle_parts = [
                html.Span(f"{prev_avg:.0f}", style={"fontWeight": "600"}),
                html.Span(" → ", style={"color": NEUTRAL}),
                html.Span(f"{avg_s:.0f}", style={"fontWeight": "600", "color": color}),
            ]
        else:
            change_badge = None
            score_subtitle_parts = None

        # Custom Avg Score card with change indicator
        score_card_children = [
            html.P(
                "AVG SCORE",
                style={
                    "margin": "0",
                    "fontSize": "11px",
                    "fontWeight": "600",
                    "letterSpacing": "0.05em",
                    "color": NEUTRAL,
                },
            ),
            html.H3(
                f"{avg_s:.0f}/100",
                style={
                    "margin": "6px 0 2px",
                    "fontSize": "1.6rem",
                    "fontWeight": "700",
                    "color": DARK,
                    "lineHeight": "1.1",
                },
            ),
        ]
        if score_subtitle_parts:
            score_card_children.append(
                html.P(
                    score_subtitle_parts,
                    style={"margin": "2px 0 0", "fontSize": "12px"},
                )
            )
        if change_badge:
            score_card_children.append(change_badge)

        avg_score_card = html.Div(
            score_card_children,
            style={
                "background": BG_CARD,
                "padding": "22px 24px 16px",
                "borderRadius": f"{CARD_RADIUS}px",
                "boxShadow": SHADOW_CARD,
                "border": "1px solid transparent",
                "textAlign": "center",
            },
        )

        new_apps_kpi = [
            dbc.Col(metric_card("New Apps", f"{n_new:,}"), md=3),
            dbc.Col(metric_card("Critical Risk", f"{crit:,}"), md=3),
            dbc.Col(metric_card("High Risk", f"{high:,}"), md=3),
            dbc.Col(avg_score_card, md=3),
        ]

        # ── Readiness Score for this time period ──
        try:
            avail = [c for c in READINESS_ACTIONS if c in time_filtered.columns]
            rdf = time_filtered.copy()
            rdf["readiness_score"] = rdf[avail].sum(axis=1)
            rdf["readiness_pct"] = (
                rdf["readiness_score"] / len(READINESS_ACTIONS) * 100
            ).round(1)

            curr_avg = rdf["readiness_pct"].mean()
            fully_ready = int((rdf["readiness_score"] == len(READINESS_ACTIONS)).sum())
            zero_ready = int((rdf["readiness_score"] == 0).sum())

            # Previous period readiness for comparison
            prev_rdf = prev_period.copy() if not prev_period.empty else pd.DataFrame()
            prev_readiness_avg = None
            prev_fully = 0
            if not prev_rdf.empty:
                p_avail = [c for c in READINESS_ACTIONS if c in prev_rdf.columns]
                prev_rdf["readiness_score"] = prev_rdf[p_avail].sum(axis=1)
                prev_rdf["readiness_pct"] = (
                    prev_rdf["readiness_score"] / len(READINESS_ACTIONS) * 100
                ).round(1)
                prev_readiness_avg = prev_rdf["readiness_pct"].mean()
                prev_fully = int(
                    (prev_rdf["readiness_score"] == len(READINESS_ACTIONS)).sum()
                )

            # Build readiness change badge
            r_period_label = {7: "7d", 14: "14d", 30: "30d", 90: "90d"}.get(
                time_days, f"{time_days}d"
            )
            if prev_readiness_avg is not None and prev_readiness_avg > 0:
                r_delta = curr_avg - prev_readiness_avg
                r_pct_change = (r_delta / prev_readiness_avg) * 100
                r_is_up = r_delta >= 0
                r_arrow = "▲" if r_is_up else "▼"
                r_color = POSITIVE if r_is_up else NEGATIVE
                r_badge_bg = POSITIVE_BG if r_is_up else NEGATIVE_BG
                readiness_badge = html.Div(
                    [
                        html.Span(
                            f"{r_arrow} {abs(r_pct_change):.1f}%",
                            style={
                                "color": r_color,
                                "fontWeight": "700",
                                "fontSize": "13px",
                                "marginRight": "6px",
                            },
                        ),
                        html.Span(
                            f"vs prev {r_period_label} ({prev_readiness_avg:.0f}%)",
                            style={
                                "color": NEUTRAL,
                                "fontSize": "11px",
                                "fontWeight": "500",
                            },
                        ),
                    ],
                    style={
                        "display": "inline-flex",
                        "alignItems": "center",
                        "background": r_badge_bg,
                        "padding": "4px 10px",
                        "borderRadius": "8px",
                        "marginTop": "4px",
                    },
                )
                readiness_subtitle = [
                    html.Span(
                        f"{prev_readiness_avg:.0f}%", style={"fontWeight": "600"}
                    ),
                    html.Span(" → ", style={"color": NEUTRAL}),
                    html.Span(
                        f"{curr_avg:.0f}%",
                        style={"fontWeight": "600", "color": r_color},
                    ),
                ]
            else:
                readiness_badge = None
                readiness_subtitle = None

            # Custom avg readiness card with change indicator
            r_card_children = [
                html.P(
                    "AVG READINESS",
                    style={
                        "margin": "0",
                        "fontSize": "11px",
                        "fontWeight": "600",
                        "letterSpacing": "0.05em",
                        "color": NEUTRAL,
                    },
                ),
                html.H3(
                    f"{curr_avg:.0f}%",
                    style={
                        "margin": "6px 0 2px",
                        "fontSize": "1.6rem",
                        "fontWeight": "700",
                        "color": DARK,
                        "lineHeight": "1.1",
                    },
                ),
            ]
            if readiness_subtitle:
                r_card_children.append(
                    html.P(
                        readiness_subtitle,
                        style={"margin": "2px 0 0", "fontSize": "12px"},
                    )
                )
            if readiness_badge:
                r_card_children.append(readiness_badge)

            avg_readiness_card = html.Div(
                r_card_children,
                style={
                    "background": BG_CARD,
                    "padding": "22px 24px 16px",
                    "borderRadius": f"{CARD_RADIUS}px",
                    "boxShadow": SHADOW_CARD,
                    "border": "1px solid transparent",
                    "textAlign": "center",
                },
            )

            readiness_kpi = [
                dbc.Col(avg_readiness_card, md=3),
                dbc.Col(
                    metric_card(
                        "Fully Ready (4/4)",
                        f"{fully_ready:,}",
                        f"prev: {prev_fully}" if not prev_period.empty else None,
                    ),
                    md=3,
                ),
                dbc.Col(metric_card("Zero Actions (0/4)", f"{zero_ready:,}"), md=3),
                dbc.Col(
                    metric_card(
                        "Apps Scored",
                        f"{len(rdf):,}",
                        f"4 of {len(ACTION_CONFIG)} actions",
                    ),
                    md=3,
                ),
            ]

            # Weekly cohort time-series (full dataset for trend context)
            rdf_all = df.copy()
            rdf_all_avail = [c for c in READINESS_ACTIONS if c in rdf_all.columns]
            rdf_all["readiness_score"] = rdf_all[rdf_all_avail].sum(axis=1)
            rdf_all["readiness_pct"] = (
                rdf_all["readiness_score"] / len(READINESS_ACTIONS) * 100
            ).round(1)
            if "created_date" in rdf_all.columns:
                rdf_all["created_date"] = pd.to_datetime(
                    rdf_all["created_date"], errors="coerce"
                )
                rdf_all = rdf_all.dropna(subset=["created_date"])
                rdf_all["cohort_week"] = (
                    rdf_all["created_date"].dt.to_period("W").dt.start_time
                )

                weekly = (
                    rdf_all.groupby("cohort_week")
                    .agg(
                        apps=("readiness_score", "size"),
                        avg_pct=("readiness_pct", "mean"),
                        fully_ready=(
                            "readiness_score",
                            lambda s: int((s == len(READINESS_ACTIONS)).sum()),
                        ),
                    )
                    .reset_index()
                )
                weekly["avg_pct"] = weekly["avg_pct"].round(1)
                weekly["full_pct"] = (
                    weekly["fully_ready"] / weekly["apps"] * 100
                ).round(1)
                weekly = weekly[weekly["apps"] >= 2].copy()

                if not weekly.empty:
                    fig_readiness = go.Figure()
                    fig_readiness.add_trace(
                        go.Scatter(
                            x=weekly["cohort_week"],
                            y=weekly["avg_pct"],
                            mode="lines+markers",
                            name="Avg Readiness %",
                            line=dict(color=GREEN, width=3),
                            marker=dict(size=6),
                            hovertemplate="Week of %{x|%b %d}<br>Avg: %{y:.1f}%<extra></extra>",
                        )
                    )
                    fig_readiness.add_trace(
                        go.Scatter(
                            x=weekly["cohort_week"],
                            y=weekly["full_pct"],
                            mode="lines+markers",
                            name="Fully Ready (4/4) %",
                            line=dict(color=TANGERINE, width=2, dash="dot"),
                            marker=dict(size=5),
                            hovertemplate="Week of %{x|%b %d}<br>4/4: %{y:.1f}%<extra></extra>",
                        )
                    )
                    fig_readiness.add_trace(
                        go.Bar(
                            x=weekly["cohort_week"],
                            y=weekly["apps"],
                            name="Sign-ups",
                            marker_color="rgba(200,200,200,0.3)",
                            yaxis="y2",
                            hovertemplate="Week of %{x|%b %d}<br>Apps: %{y}<extra></extra>",
                        )
                    )
                    fig_readiness.update_layout(
                        title="Readiness Score by Sign-up Cohort (Weekly)",
                        xaxis_title="Sign-up Week",
                        yaxis=dict(title="Readiness %", range=[0, 105]),
                        yaxis2=dict(
                            title="Sign-ups",
                            overlaying="y",
                            side="right",
                            showgrid=False,
                        ),
                        height=450,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                        ),
                        hovermode="x unified",
                    )
        except Exception as _e:
            print(f"[activation] readiness error: {_e}")

        display = time_filtered.copy()
        for col_name, cfg in ACTION_CONFIG.items():
            if col_name in display.columns:
                display[cfg["label"]] = display[col_name].map({1: "✅", 0: "❌"})

        base_cols = [
            "application_name",
            "coach_email",
            "created_date",
            "activation_score",
            "actions_completed",
            "risk_level",
            "is_active",
        ]
        action_labels = [cfg["label"] for cfg in ACTION_CONFIG.values()]
        show_cols = [c for c in base_cols if c in display.columns] + [
            lbl for lbl in action_labels if lbl in display.columns
        ]
        rename_map = {
            "application_name": "App Name",
            "coach_email": "Coach Email",
            "created_date": "Created",
            "activation_score": "Score",
            "actions_completed": "Actions Done",
            "risk_level": "Risk Level",
            "is_active": "Active?",
        }
        disp_df = display[show_cols].rename(columns=rename_map)
        new_apps_table = dash_table.DataTable(
            data=disp_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in disp_df.columns],
            fixed_columns={"headers": True, "data": 1},
            style_table={"overflowX": "auto", "minWidth": "100%"},
            style_cell={
                "fontSize": "12px",
                "padding": "6px",
                "fontFamily": "Sora",
                "textAlign": "left",
                "minWidth": "120px",
                "maxWidth": "200px",
            },
            style_cell_conditional=[
                {
                    "if": {"column_id": "App Name"},
                    "minWidth": "180px",
                    "maxWidth": "250px",
                    "position": "sticky",
                    "left": 0,
                    "backgroundColor": "#FFFFFF",
                    "zIndex": 1,
                },
            ],
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            page_size=25,
            sort_action="native",
            filter_action="native",
        )

    # ── Cohort Retention ──
    fig_cohort = _empty_fig("No cohort data")
    try:
        cohort = load_cohort_retention()
        if (
            not cohort.empty
            and "cohort" in cohort.columns
            and "months_since_join" in cohort.columns
        ):
            pivot = cohort.pivot_table(
                index="cohort",
                columns="months_since_join",
                values="retention_rate",
                aggfunc="mean",
            )
            fig_cohort = px.imshow(
                pivot.values,
                x=[f"M{int(c)}" for c in pivot.columns],
                y=[str(r) for r in pivot.index],
                color_continuous_scale="RdYlGn",
                title="Retention Rate by Cohort (%)",
                labels={"color": "Retention %"},
                aspect="auto",
                text_auto=".0f",
            )
            fig_cohort.update_layout(height=500)
    except Exception as _e:
        print(f"[activation] chart error: {_e}")

    # ── Retention Curve ──
    fig_curve = _empty_fig("No retention curve data")
    try:
        curve = load_coach_retention_curve()
        if not curve.empty and "period" in curve.columns and "pct" in curve.columns:
            fig_curve = px.line(
                curve,
                x="period",
                y="pct",
                title="Coach Retention Curve",
                markers=True,
                labels={"pct": "Retention %", "period": "Period"},
            )
            fig_curve.update_layout(height=400)
    except Exception as _e:
        print(f"[activation] chart error: {_e}")

    return (
        kpi_children,
        fig_ct,
        readiness_kpi,
        fig_readiness,
        fig_dist,
        fig_ret,
        fig_impact,
        impact_table,
        fig_comp,
        fig_risk,
        risk_table_content,
        new_apps_kpi,
        new_apps_table,
        fig_cohort,
        fig_curve,
    )
