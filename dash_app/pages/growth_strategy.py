"""
Page 9 — Coach Growth Strategy
Clusters, retention, LTV, paid ad ROI model, and growth ladder.
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
    IVORY,
    TANGERINE,
    LIME,
    ALPINE,
    ERROR,
    NEUTRAL,
    POSITIVE,
    NEGATIVE,
    BG_CARD,
    SHADOW_CARD,
    CARD_RADIUS,
    metric_card,
    section_header,
    chart_card,
    card_wrapper,
)
from data import load_growth_strategy_app_stats, load_growth_strategy_monthly

dash.register_page(
    __name__,
    path="/growth-strategy",
    name="Growth Strategy",
    title="Growth Strategy — KLIQ",
)

CLUSTER_COLORS = {
    "PRIME": "#15803D",
    "GROWTH": "#2563EB",
    "EMERGING": "#D97706",
    "EARLY": "#8A9494",
    "INACTIVE": "#D1D5DB",
}
CLUSTER_EMOJI = {
    "PRIME": "🟢",
    "GROWTH": "🔵",
    "EMERGING": "🟠",
    "EARLY": "⚪",
    "INACTIVE": "⬜",
}
CLUSTER_ORDER = ["PRIME", "GROWTH", "EMERGING", "EARLY", "INACTIVE"]


def _empty_fig(msg="No data"):
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


def _assign_cluster(row):
    if (
        row["iap_revenue"] >= 5000
        and row["renewal_ratio"] >= 1.5
        and row["active_months"] >= 6
    ):
        return "PRIME"
    elif row["iap_revenue"] >= 1000 and row["active_months"] >= 3:
        return "GROWTH"
    elif row["iap_revenue"] >= 100 and row["active_months"] >= 3:
        return "EMERGING"
    elif row["iap_revenue"] > 0:
        return "EARLY"
    return "INACTIVE"


layout = html.Div(
    [
        html.H1(
            "Coach Growth Strategy",
            style={"fontSize": "20px", "fontWeight": "700", "color": DARK},
        ),
        html.P(
            "Clusters · Retention · LTV · Paid Ad ROI · Growth Ladder",
            style={"color": NEUTRAL, "fontSize": "13px"},
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
                            id="gs-date-range",
                            options=[
                                {"label": "Last 3 months", "value": 90},
                                {"label": "Last 6 months", "value": 180},
                                {"label": "Last 12 months", "value": 365},
                                {"label": "All Time", "value": 99999},
                            ],
                            value=99999,
                            clearable=False,
                            style={"fontSize": "13px"},
                        ),
                    ],
                    md=3,
                ),
            ],
            className="mb-4",
        ),
        # KPIs
        dbc.Row(id="gs-kpi-row", className="mb-3"),
        html.Hr(),
        # Clusters
        section_header("Strategic Clusters"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="gs-cluster-pie")), md=5),
                dbc.Col(card_wrapper(html.Div(id="gs-cluster-table")), md=7),
            ]
        ),
        # Strategy cards
        html.Div(id="gs-strategy-cards", className="mb-3"),
        html.Hr(),
        # App Portfolio
        section_header("App Portfolio"),
        card_wrapper(html.Div(id="gs-portfolio-table")),
        html.Hr(),
        # LTV & Unit Economics
        section_header("Unit Economics & LTV"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="gs-ltv-chart")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="gs-renew-scatter")), md=6),
            ]
        ),
        dbc.Row(id="gs-ue-kpi", className="mb-3"),
        html.Hr(),
        # Engagement Patterns
        section_header("Engagement Patterns"),
        chart_card(dcc.Graph(id="gs-engagement")),
        html.Hr(),
        # Subscriber Retention
        section_header("Subscriber Retention"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="gs-sub-flow")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="gs-cum-net")), md=6),
            ]
        ),
        html.Hr(),
        # ROI Simulator
        section_header("Paid Ad ROI Simulator"),
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.P(
                            [
                                html.B("How it works:"),
                                " KLIQ manages Meta/TikTok ads on behalf of coaches. "
                                "KLIQ charges £49/month base + £5 per new subscriber acquired.",
                            ],
                            style={
                                "fontSize": "13px",
                                "color": "#333",
                                "background": "#F0FDF4",
                                "padding": "12px",
                                "borderRadius": "8px",
                                "borderLeft": "4px solid #15803D",
                            },
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label("Monthly Ad Spend (£)"),
                                        dcc.Slider(
                                            id="gs-ad-spend",
                                            min=200,
                                            max=5000,
                                            step=100,
                                            value=1000,
                                            marks={
                                                i: f"£{i:,}"
                                                for i in [200, 1000, 2000, 3000, 5000]
                                            },
                                        ),
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Cost per Subscriber (£)"),
                                        dcc.Slider(
                                            id="gs-cpa",
                                            min=2,
                                            max=25,
                                            step=1,
                                            value=8,
                                            marks={
                                                i: f"£{i}"
                                                for i in [2, 5, 8, 12, 15, 20, 25]
                                            },
                                        ),
                                    ],
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("KLIQ Total Take (%)"),
                                        dcc.Slider(
                                            id="gs-kliq-pct",
                                            min=5,
                                            max=30,
                                            step=1,
                                            value=15,
                                            marks={
                                                i: f"{i}%"
                                                for i in [5, 10, 15, 20, 25, 30]
                                            },
                                        ),
                                    ],
                                    md=4,
                                ),
                            ],
                            className="mb-3",
                        ),
                        dbc.Row(id="gs-roi-kpi", className="mb-3"),
                        card_wrapper(html.Div(id="gs-roi-breakdown")),
                        chart_card(dcc.Graph(id="gs-scenario-chart")),
                    ]
                ),
            ],
            className="mb-3",
        ),
        html.Hr(),
        # Growth Ladder
        section_header("Growth Ladder"),
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                "STAGE 4: SCALE (1,000+ subs)",
                                                style={"color": "#15803D"},
                                            ),
                                            html.Ul(
                                                [
                                                    html.Li(
                                                        "White-label content licensing"
                                                    ),
                                                    html.Li("Premium brand deals"),
                                                    html.Li("Cross-promotion network"),
                                                    html.Li("KLIQ Creator Fund"),
                                                ],
                                                style={"fontSize": "13px"},
                                            ),
                                        ]
                                    )
                                ],
                                style={
                                    "border": "2px solid #15803D",
                                    "background": "#F0FDF4",
                                },
                            ),
                            md=6,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                "STAGE 3: MONETISE (250+ subs)",
                                                style={"color": "#2563EB"},
                                            ),
                                            html.Ul(
                                                [
                                                    html.Li(
                                                        "KLIQ Affiliate Marketplace"
                                                    ),
                                                    html.Li("Content licensing deals"),
                                                    html.Li("Brand partnerships"),
                                                    html.Li("Premium Coach Badge"),
                                                ],
                                                style={"fontSize": "13px"},
                                            ),
                                        ]
                                    )
                                ],
                                style={
                                    "border": "2px solid #2563EB",
                                    "background": "#DBEAFE",
                                },
                            ),
                            md=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                "STAGE 2: GROW (50–250 subs)",
                                                style={"color": "#D97706"},
                                            ),
                                            html.Ul(
                                                [
                                                    html.Li(
                                                        "KLIQ Managed PPC (£49/mo + £5/sub)"
                                                    ),
                                                    html.Li("Social media toolkit"),
                                                    html.Li("Referral program"),
                                                    html.Li(
                                                        "Target: 250 = Brand Ready"
                                                    ),
                                                ],
                                                style={"fontSize": "13px"},
                                            ),
                                        ]
                                    )
                                ],
                                style={
                                    "border": "2px solid #D97706",
                                    "background": "#FEF3C7",
                                },
                            ),
                            md=6,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                "STAGE 1: LAUNCH (0–50 subs)",
                                                style={"color": "#6B7280"},
                                            ),
                                            html.Ul(
                                                [
                                                    html.Li(
                                                        "AI Blog Writer + Activation Checklist"
                                                    ),
                                                    html.Li("Store in 5 Minutes"),
                                                    html.Li("Social Share Templates"),
                                                    html.Li("Pricing Benchmarks"),
                                                ],
                                                style={"fontSize": "13px"},
                                            ),
                                        ]
                                    )
                                ],
                                style={
                                    "border": "2px solid #9CA3AF",
                                    "background": "#F3F4F6",
                                },
                            ),
                            md=6,
                        ),
                    ]
                ),
            ]
        ),
        html.Hr(),
        # Revenue Projections
        section_header("Revenue Projections"),
        card_wrapper(html.Div(id="gs-projections")),
        dbc.Row(id="gs-proj-kpi", className="mb-3"),
        html.Hr(),
        # Key Targets
        section_header("Key Targets"),
        card_wrapper(html.Div(id="gs-targets")),
        # Hidden trigger
        dcc.Store(id="gs-trigger", data=True),
    ]
)


@callback(
    Output("gs-kpi-row", "children"),
    Output("gs-cluster-pie", "figure"),
    Output("gs-cluster-table", "children"),
    Output("gs-strategy-cards", "children"),
    Output("gs-portfolio-table", "children"),
    Output("gs-ltv-chart", "figure"),
    Output("gs-renew-scatter", "figure"),
    Output("gs-ue-kpi", "children"),
    Output("gs-engagement", "figure"),
    Output("gs-sub-flow", "figure"),
    Output("gs-cum-net", "figure"),
    Output("gs-projections", "children"),
    Output("gs-proj-kpi", "children"),
    Output("gs-targets", "children"),
    Input("gs-date-range", "value"),
    Input("gs-trigger", "data"),
)
def update_strategy(days_back, _):
    df = load_growth_strategy_app_stats()
    monthly = load_growth_strategy_monthly()

    if df.empty:
        e = _empty_fig("No data — run refresh script")
        nd = html.P("No data", style={"color": NEUTRAL})
        return [], e, nd, [], nd, e, e, [], e, e, e, nd, [], nd

    # Apply date range filter
    if days_back and days_back < 99999:
        cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m")
        # Filter monthly data to only include months within range
        if not monthly.empty and "month" in monthly.columns:
            monthly = monthly[monthly["month"] >= cutoff].copy()
        # Filter app stats: keep apps with created_date within range (or no date)
        if "created_date" in df.columns:
            df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
            cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days_back)
            df = df[
                (df["created_date"].isna()) | (df["created_date"] >= cutoff_date)
            ].copy()

    if df.empty:
        e = _empty_fig("No data for selected date range")
        nd = html.P("No data for selected period", style={"color": NEUTRAL})
        return [], e, nd, [], nd, e, e, [], e, e, e, nd, [], nd

    # Derived columns
    df["kliq_revenue"] = (df["iap_revenue"] * df["kliq_fee_pct"] / 100).round(2)
    df["active_months"] = df["active_rev_months"].clip(lower=1)
    df["monthly_rev"] = (df["iap_revenue"] / df["active_months"]).round(2)
    df["total_payments"] = df["purchases"] + df["recurring_payments"]
    df["ltv_per_buyer"] = np.where(
        df["purchases"] > 0, (df["iap_revenue"] / df["purchases"]).round(2), 0
    )
    df["renewal_ratio"] = np.where(
        df["purchases"] > 0, (df["recurring_payments"] / df["purchases"]).round(1), 0
    )
    df["retention_rate"] = np.where(
        df["new_subscribers"] > 0,
        ((1 - df["cancellations"] / df["new_subscribers"]).clip(0, 1) * 100).round(0),
        0,
    )
    df["cluster"] = df.apply(_assign_cluster, axis=1)

    rev_df = df[df["iap_revenue"] > 0].copy()
    total_iap = rev_df["iap_revenue"].sum()
    total_kliq = rev_df["kliq_revenue"].sum()
    total_buyers = rev_df["purchases"].sum()
    weighted_ltv = total_iap / total_buyers if total_buyers > 0 else 0
    avg_renewal = (
        rev_df.loc[rev_df["purchases"] > 0, "renewal_ratio"].mean()
        if (rev_df["purchases"] > 0).any()
        else 0
    )
    n_prime = len(rev_df[rev_df["cluster"] == "PRIME"])
    n_growth = len(rev_df[rev_df["cluster"] == "GROWTH"])

    # KPIs
    kpi = [
        dbc.Col(
            metric_card("Total IAP Revenue", f"${total_iap:,.0f}", "Apple + Google"),
            md=2,
        ),
        dbc.Col(
            metric_card(
                "KLIQ Revenue", f"${total_kliq:,.0f}", f"From {len(rev_df)} apps"
            ),
            md=2,
        ),
        dbc.Col(
            metric_card(
                "LTV/Buyer", f"${weighted_ltv:,.2f}", f"{total_buyers:,} purchases"
            ),
            md=2,
        ),
        dbc.Col(
            metric_card("Avg Renewals", f"{avg_renewal:.1f}x", "Per paying user"), md=2
        ),
        dbc.Col(
            metric_card(
                "Ad-Ready Apps",
                f"{n_prime + n_growth}",
                f"{n_prime} Prime + {n_growth} Growth",
            ),
            md=2,
        ),
    ]

    # Cluster summary
    cluster_summary = []
    for cl in CLUSTER_ORDER:
        sub = (
            rev_df[rev_df["cluster"] == cl]
            if cl != "INACTIVE"
            else df[df["cluster"] == cl]
        )
        if len(sub) == 0:
            continue
        cluster_summary.append(
            {
                "Cluster": f"{CLUSTER_EMOJI[cl]} {cl}",
                "Apps": len(sub),
                "Total Revenue": f"${sub['iap_revenue'].sum():,.0f}",
                "KLIQ Revenue": f"${sub['kliq_revenue'].sum():,.0f}",
                "Avg Monthly Rev": f"${sub['monthly_rev'].mean():,.0f}",
                "Avg Retention": f"{sub['retention_rate'].mean():.0f}%",
            }
        )
    cs_df = pd.DataFrame(cluster_summary)

    fig_pie = _empty_fig("No cluster data")
    cluster_table = html.P("No data", style={"color": NEUTRAL})
    if not cs_df.empty:
        pie_data = rev_df.groupby("cluster")["iap_revenue"].sum().reset_index()
        pie_data["label"] = pie_data["cluster"].map(
            lambda c: f"{CLUSTER_EMOJI.get(c, '')} {c}"
        )
        fig_pie = px.pie(
            pie_data,
            names="label",
            values="iap_revenue",
            title="Revenue by Cluster",
            color="cluster",
            color_discrete_map=CLUSTER_COLORS,
        )
        fig_pie.update_layout(height=350)
        cluster_table = dash_table.DataTable(
            data=cs_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in cs_df.columns],
            style_cell={
                "fontSize": "12px",
                "padding": "6px",
                "fontFamily": "Sora",
                "textAlign": "left",
            },
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
        )

    # Strategy cards
    strategies = [
        (
            "PRIME",
            "Scale with Paid Ads",
            "Aggressively scale with KLIQ-managed PPC. Ad Budget: £1K–2K/mo.",
            "#F0FDF4",
            "#15803D",
        ),
        (
            "GROWTH",
            "Accelerate with Moderate Spend",
            "Moderate ad spend + funnel optimisation. Ad Budget: £500–1K/mo.",
            "#DBEAFE",
            "#2563EB",
        ),
        (
            "EMERGING",
            "Activate Before Spending",
            "Fix content & engagement before paid ads. Focus on activation.",
            "#FEF3C7",
            "#D97706",
        ),
        (
            "EARLY",
            "Onboard Properly",
            "Not ready for paid acquisition. Focus on 30/60 day milestones.",
            "#F3F4F6",
            "#6B7280",
        ),
    ]
    strat_cards = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H6(
                                    f"{CLUSTER_EMOJI[cl]} {title}",
                                    style={"color": accent, "fontWeight": "700"},
                                ),
                                html.P(
                                    desc, style={"fontSize": "13px", "color": "#333"}
                                ),
                            ]
                        )
                    ],
                    style={"background": bg, "borderLeft": f"4px solid {accent}"},
                ),
                md=6,
                className="mb-2",
            )
            for cl, title, desc, bg, accent in strategies
        ]
    )

    # Portfolio Table
    portfolio = html.P("No data", style={"color": NEUTRAL})
    if not rev_df.empty:
        disp = rev_df[
            [
                "app",
                "cluster",
                "iap_revenue",
                "kliq_revenue",
                "kliq_fee_pct",
                "active_months",
                "monthly_rev",
                "purchases",
                "recurring_payments",
                "renewal_ratio",
                "ltv_per_buyer",
                "retention_rate",
            ]
        ].copy()
        disp = disp.sort_values("iap_revenue", ascending=False)
        disp.columns = [
            "App",
            "Cluster",
            "IAP Revenue",
            "KLIQ Revenue",
            "KLIQ %",
            "Active Mo",
            "Monthly Rev",
            "Purchases",
            "Recurring",
            "Renewal",
            "LTV/Buyer",
            "Retention %",
        ]
        portfolio = dash_table.DataTable(
            data=disp.to_dict("records"),
            columns=[
                (
                    {
                        "name": c,
                        "id": c,
                        "type": "numeric",
                        "format": {"specifier": "$,.0f"},
                    }
                    if c in ("IAP Revenue", "KLIQ Revenue", "Monthly Rev", "LTV/Buyer")
                    else {"name": c, "id": c}
                )
                for c in disp.columns
            ],
            style_table={"overflowX": "auto"},
            style_cell={
                "fontSize": "11px",
                "padding": "5px",
                "fontFamily": "Sora",
                "textAlign": "right",
            },
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            style_data_conditional=[
                {"if": {"column_id": c}, "textAlign": "left"}
                for c in ["App", "Cluster"]
            ],
            sort_action="native",
            filter_action="native",
            page_size=25,
        )

    # LTV Charts
    paying = rev_df[rev_df["purchases"] >= 5].sort_values(
        "iap_revenue", ascending=False
    )
    fig_ltv = _empty_fig("Not enough data")
    fig_renew = _empty_fig()
    if not paying.empty:
        fig_ltv = px.bar(
            paying.head(15),
            x="app",
            y="ltv_per_buyer",
            title="LTV per Paying User (Top 15)",
            color="cluster",
            color_discrete_map=CLUSTER_COLORS,
        )
        fig_ltv.update_layout(height=400, xaxis_tickangle=-45)
        fig_renew = px.scatter(
            paying,
            x="renewal_ratio",
            y="ltv_per_buyer",
            size="iap_revenue",
            color="cluster",
            hover_name="app",
            title="Renewal Ratio vs LTV",
            color_discrete_map=CLUSTER_COLORS,
        )
        fig_renew.update_layout(height=400)

    # Unit Economics KPIs
    total_recurring = rev_df["recurring_payments"].sum()
    avg_renewals_all = total_recurring / total_buyers if total_buyers > 0 else 0
    total_subs = rev_df["new_subscribers"].sum()
    conversion = total_buyers / total_subs * 100 if total_subs > 0 else 0
    ue_kpi = [
        dbc.Col(
            metric_card(
                "Avg Rev/Purchase",
                f"${total_iap / total_buyers:,.2f}" if total_buyers > 0 else "$0",
            ),
            md=3,
        ),
        dbc.Col(metric_card("Platform Avg Renewals", f"{avg_renewals_all:.1f}x"), md=3),
        dbc.Col(metric_card("Purchase Conversion", f"{conversion:.1f}%"), md=3),
        dbc.Col(metric_card("Total Recurring", f"{total_recurring:,}"), md=3),
    ]

    # Engagement
    fig_eng = _empty_fig("No engagement data")
    eng_metrics = [
        "livestreams",
        "live_joins",
        "workouts",
        "community_posts",
        "modules_published",
        "programs_published",
    ]
    eng_labels = [
        "Livestreams",
        "Live Joins",
        "Workouts",
        "Community Posts",
        "Modules",
        "Programs",
    ]
    eng_data = []
    for cl in ["PRIME", "GROWTH", "EMERGING", "EARLY"]:
        sub = rev_df[rev_df["cluster"] == cl]
        if len(sub) == 0:
            continue
        months = sub["event_months"].clip(lower=1)
        for m, l in zip(eng_metrics, eng_labels):
            if m in sub.columns:
                eng_data.append(
                    {
                        "Cluster": cl,
                        "Metric": l,
                        "Avg/Month/App": round((sub[m] / months).mean(), 1),
                    }
                )
    if eng_data:
        eng_df = pd.DataFrame(eng_data)
        fig_eng = px.bar(
            eng_df,
            x="Metric",
            y="Avg/Month/App",
            color="Cluster",
            barmode="group",
            title="Monthly Engagement per App by Cluster",
            color_discrete_map=CLUSTER_COLORS,
        )
        fig_eng.update_layout(height=400)

    # Subscriber Retention
    fig_sub = _empty_fig("No monthly data")
    fig_cum = _empty_fig()
    if not monthly.empty:
        rev_apps = rev_df["app"].unique()
        mr = monthly[monthly["app"].isin(rev_apps)]
        sf = (
            mr.groupby("month")
            .agg(new_subs=("new_subs", "sum"), cancels=("cancels", "sum"))
            .reset_index()
            .sort_values("month")
        )
        sf["net"] = sf["new_subs"] - sf["cancels"]
        sf["cumulative_net"] = sf["net"].cumsum()
        fig_sub = go.Figure()
        fig_sub.add_trace(
            go.Bar(
                x=sf["month"], y=sf["new_subs"], name="New Subs", marker_color=POSITIVE
            )
        )
        fig_sub.add_trace(
            go.Bar(
                x=sf["month"],
                y=-sf["cancels"],
                name="Cancellations",
                marker_color=NEGATIVE,
            )
        )
        fig_sub.update_layout(
            title="Monthly Subscriber Flow", barmode="relative", height=400
        )
        fig_cum = px.area(
            sf, x="month", y="cumulative_net", title="Cumulative Net Subscribers"
        )
        fig_cum.update_layout(height=400)
        fig_cum.update_traces(line_color=GREEN, fillcolor="rgba(28,56,56,0.15)")

    # Projections
    proj_data = [
        {
            "Service": "Managed PPC",
            "Year 1": "£30K",
            "Year 2": "£120K",
            "Coaches": "50",
            "Status": "Ready to pilot",
        },
        {
            "Service": "Affiliate Marketplace",
            "Year 1": "£6K",
            "Year 2": "£36K",
            "Coaches": "50",
            "Status": "Build needed",
        },
        {
            "Service": "Brand Deals",
            "Year 1": "£15K",
            "Year 2": "£60K",
            "Coaches": "21",
            "Status": "Outreach ready",
        },
        {
            "Service": "Content Licensing",
            "Year 1": "£10K",
            "Year 2": "£50K",
            "Coaches": "10",
            "Status": "Build needed",
        },
        {
            "Service": "Creator Fund",
            "Year 1": "£5K",
            "Year 2": "£30K",
            "Coaches": "5-10",
            "Status": "Ready to pilot",
        },
    ]
    proj_table = dash_table.DataTable(
        data=proj_data,
        columns=[{"name": c, "id": c} for c in proj_data[0].keys()],
        style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
        style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
    )
    proj_kpi = [
        dbc.Col(metric_card("Year 1 New Revenue", "£66K"), md=4),
        dbc.Col(metric_card("Year 2 New Revenue", "£296K"), md=4),
        dbc.Col(metric_card("Current KLIQ IAP Revenue", f"${total_kliq:,.0f}"), md=4),
    ]

    # Targets
    targets_data = [
        {
            "Metric": "Coaches with revenue",
            "Current": str(len(rev_df)),
            "6-Month": "50",
            "12-Month": "100",
        },
        {
            "Metric": "250+ subscribers",
            "Current": "21",
            "6-Month": "35",
            "12-Month": "50",
        },
        {
            "Metric": "1,000+ subscribers",
            "Current": "12",
            "6-Month": "18",
            "12-Month": "25",
        },
        {
            "Metric": "Avg coach MRR (top 25)",
            "Current": "£432",
            "6-Month": "£600",
            "12-Month": "£1,000",
        },
        {
            "Metric": "PPC coaches active",
            "Current": "0",
            "6-Month": "50",
            "12-Month": "200",
        },
    ]
    targets_table = dash_table.DataTable(
        data=targets_data,
        columns=[{"name": c, "id": c} for c in targets_data[0].keys()],
        style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
        style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
    )

    return (
        kpi,
        fig_pie,
        cluster_table,
        strat_cards,
        portfolio,
        fig_ltv,
        fig_renew,
        ue_kpi,
        fig_eng,
        fig_sub,
        fig_cum,
        proj_table,
        proj_kpi,
        targets_table,
    )


@callback(
    Output("gs-roi-kpi", "children"),
    Output("gs-roi-breakdown", "children"),
    Output("gs-scenario-chart", "figure"),
    Input("gs-ad-spend", "value"),
    Input("gs-cpa", "value"),
    Input("gs-kliq-pct", "value"),
)
def update_roi(ad_spend, cpa, kliq_pct):
    df = load_growth_strategy_app_stats()
    if df.empty:
        return [], html.P("No data", style={"color": NEUTRAL}), _empty_fig()

    df["ltv_per_buyer"] = np.where(
        df["purchases"] > 0, (df["iap_revenue"] / df["purchases"]).round(2), 0
    )
    df["renewal_ratio"] = np.where(
        df["purchases"] > 0, (df["recurring_payments"] / df["purchases"]).round(1), 0
    )
    rev_df = df[df["iap_revenue"] > 0]
    total_buyers = rev_df["purchases"].sum()
    total_iap = rev_df["iap_revenue"].sum()
    weighted_ltv = total_iap / total_buyers if total_buyers > 0 else 0
    avg_renewal = (
        rev_df.loc[rev_df["purchases"] > 0, "renewal_ratio"].mean()
        if (rev_df["purchases"] > 0).any()
        else 0
    )

    new_subs = ad_spend / cpa
    platform_fee_pct = 30
    coach_net_pct = 100 - platform_fee_pct - kliq_pct
    retention_curve = [
        1.0,
        0.85,
        0.72,
        0.65,
        0.58,
        0.52,
        0.47,
        0.43,
        0.40,
        0.37,
        0.35,
        0.33,
    ]
    avg_monthly_price = (
        weighted_ltv / (1 + avg_renewal) if avg_renewal > 0 else weighted_ltv / 4
    )
    ltv_12m = sum(avg_monthly_price * r for r in retention_curve)
    kliq_ltv = ltv_12m * kliq_pct / 100
    coach_ltv = ltv_12m * coach_net_pct / 100
    monthly_new_gmv = new_subs * ltv_12m / 12
    monthly_kliq_from_cohort = new_subs * kliq_ltv / 12
    monthly_coach = new_subs * coach_ltv / 12
    kliq_mgmt_fee = 49 + 5 * new_subs
    kliq_total_monthly = monthly_kliq_from_cohort + kliq_mgmt_fee
    kliq_net = kliq_total_monthly - ad_spend

    roi_kpi = [
        dbc.Col(metric_card("New Subs/Month", f"{new_subs:.0f}"), md=3),
        dbc.Col(metric_card("12-Month LTV/Sub", f"${ltv_12m:,.2f}"), md=3),
        dbc.Col(
            metric_card(
                "KLIQ Net Monthly",
                f"${kliq_net:,.0f}",
                "Profitable" if kliq_net >= 0 else "Loss",
            ),
            md=3,
        ),
        dbc.Col(metric_card("Coach Net Monthly", f"${monthly_coach:,.0f}"), md=3),
    ]

    breakdown = [
        {"Metric": "New subscribers", "Value": f"{new_subs:.0f}"},
        {"Metric": "12-month LTV/sub", "Value": f"${ltv_12m:,.2f}"},
        {"Metric": "Monthly GMV from cohort", "Value": f"${monthly_new_gmv:,.0f}"},
        {
            "Metric": f"Platform fee ({platform_fee_pct}%)",
            "Value": f"${monthly_new_gmv * platform_fee_pct / 100:,.0f}",
        },
        {
            "Metric": f"KLIQ % revenue ({kliq_pct}%)",
            "Value": f"${monthly_kliq_from_cohort:,.0f}",
        },
        {"Metric": "KLIQ mgmt fee (£49 + £5/sub)", "Value": f"${kliq_mgmt_fee:,.0f}"},
        {"Metric": "KLIQ total monthly", "Value": f"${kliq_total_monthly:,.0f}"},
        {"Metric": "Ad spend", "Value": f"${ad_spend:,.0f}"},
        {"Metric": "KLIQ net", "Value": f"${kliq_net:,.0f}"},
        {
            "Metric": f"Coach payout ({coach_net_pct}%)",
            "Value": f"${monthly_coach:,.0f}",
        },
    ]
    breakdown_table = dash_table.DataTable(
        data=breakdown,
        columns=[{"name": "Metric", "id": "Metric"}, {"name": "Value", "id": "Value"}],
        style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
        style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
    )

    # Scenario chart
    scenarios = []
    for spend in [500, 1000, 2000, 3000, 5000]:
        for c in [3, 5, 8, 12, 15, 20]:
            subs = spend / c
            m_gmv = subs * ltv_12m / 12
            m_kliq = m_gmv * kliq_pct / 100 + 49 + 5 * subs
            net = m_kliq - spend
            scenarios.append(
                {
                    "Ad Spend": f"£{spend:,}",
                    "CPA (£)": c,
                    "KLIQ Net ($/mo)": round(net, 0),
                }
            )
    scen_df = pd.DataFrame(scenarios)
    fig_scen = px.line(
        scen_df,
        x="CPA (£)",
        y="KLIQ Net ($/mo)",
        color="Ad Spend",
        title="KLIQ Net Monthly Revenue by CPA",
        markers=True,
    )
    fig_scen.add_hline(
        y=0, line_dash="dash", line_color="red", annotation_text="Break-even"
    )
    fig_scen.update_layout(height=400)

    return roi_kpi, breakdown_table, fig_scen
