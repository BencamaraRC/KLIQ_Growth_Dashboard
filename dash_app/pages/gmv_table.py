"""
Page 6 — GMV Table
Per-coach monthly GMV revenue table, total GMV, avg LTV per app.
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
    metric_card,
    section_header,
    chart_card,
    card_wrapper,
)
from data import (
    load_coach_gmv_timeline,
    load_coach_growth_stages,
    load_unified_revenue,
    load_app_lookup,
    load_inapp_purchases,
    load_recurring_payments,
    load_revenue_by_channel,
)

dash.register_page(
    __name__, path="/gmv-table", name="GMV Table", title="GMV Table — KLIQ"
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
            "GMV Table", style={"fontSize": "20px", "fontWeight": "700", "color": DARK}
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Filter by App",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dcc.Dropdown(
                            id="gmv-app-filter",
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
                            "Date Range",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dcc.Dropdown(
                            id="gmv-date-range",
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
        dbc.Row(id="gmv-kpi-row", className="mb-3"),
        html.Hr(),
        section_header("📊 Monthly GMV by Coach (Stripe + Apple IAP)"),
        card_wrapper(html.Div(id="gmv-pivot-table")),
        html.Hr(),
        section_header("📈 GMV Trend"),
        chart_card(dcc.Graph(id="gmv-trend-chart")),
        chart_card(dcc.Graph(id="gmv-top-coaches-chart")),
        html.Hr(),
        section_header("📋 Coach Revenue Summary"),
        card_wrapper(html.Div(id="gmv-summary-table")),
        html.Hr(),
        section_header("📱 In-App Purchases"),
        dbc.Row(
            [
                dbc.Col(dbc.Row(id="gmv-iap-kpi"), md=4),
                dbc.Col(chart_card(dcc.Graph(id="gmv-iap-trend")), md=8),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(card_wrapper(html.Div(id="gmv-iap-plan-table")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="gmv-iap-plan-pie")), md=6),
            ]
        ),
        html.Hr(),
        section_header("🔄 Recurring Payments"),
        dbc.Row(
            [
                dbc.Col(dbc.Row(id="gmv-rec-kpi"), md=4),
                dbc.Col(chart_card(dcc.Graph(id="gmv-rec-trend")), md=8),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(card_wrapper(html.Div(id="gmv-rec-platform-table")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="gmv-rec-platform-pie")), md=6),
            ]
        ),
    ]
)


@callback(Output("gmv-app-filter", "options"), Input("gmv-app-filter", "value"))
def populate_apps(_):
    apps = load_app_lookup()
    names = (
        sorted([n for n in apps["application_name"].dropna().unique() if n])
        if not apps.empty and "application_name" in apps.columns
        else []
    )
    return [{"label": "All Apps", "value": "All Apps"}] + [
        {"label": n, "value": n} for n in names
    ]


@callback(
    Output("gmv-kpi-row", "children"),
    Output("gmv-pivot-table", "children"),
    Output("gmv-trend-chart", "figure"),
    Output("gmv-top-coaches-chart", "figure"),
    Output("gmv-summary-table", "children"),
    Output("gmv-iap-kpi", "children"),
    Output("gmv-iap-trend", "figure"),
    Output("gmv-iap-plan-table", "children"),
    Output("gmv-iap-plan-pie", "figure"),
    Output("gmv-rec-kpi", "children"),
    Output("gmv-rec-trend", "figure"),
    Output("gmv-rec-platform-table", "children"),
    Output("gmv-rec-platform-pie", "figure"),
    Input("gmv-app-filter", "value"),
    Input("gmv-date-range", "value"),
)
def update_gmv(selected_app, days_back):
    unified_rev = load_unified_revenue()
    stages = load_coach_growth_stages()

    # Apply date range filter
    if days_back and days_back < 99999:
        cutoff_month = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m")
        if not unified_rev.empty and "month" in unified_rev.columns:
            unified_rev = unified_rev[unified_rev["month"] >= cutoff_month].copy()

    def filt(df):
        if (
            selected_app == "All Apps"
            or df.empty
            or "application_name" not in df.columns
        ):
            return df
        return df[df["application_name"] == selected_app]

    unified_f = filt(unified_rev)
    stages_f = filt(stages)
    total_gmv = (
        unified_f["revenue"].sum()
        if not unified_f.empty and "revenue" in unified_f.columns
        else 0
    )

    # KPIs
    kpi = [dbc.Col(metric_card("Total GMV", f"${total_gmv:,.0f}"), md=3)]
    if not unified_f.empty and "application_name" in unified_f.columns:
        app_totals = unified_f.groupby("application_name")["revenue"].sum()
        apps_with_rev = app_totals[app_totals > 0]
        avg_ltv = apps_with_rev.mean() if len(apps_with_rev) > 0 else 0
        kpi.append(dbc.Col(metric_card("Avg LTV/App", f"${avg_ltv:,.0f}"), md=3))
    else:
        kpi.append(dbc.Col(metric_card("Avg LTV/App", "N/A"), md=3))

    if not unified_f.empty and "month" in unified_f.columns:
        last_m = unified_f["month"].max()
        lm_data = unified_f[unified_f["month"] == last_m]
        avg_last = (
            lm_data.groupby("application_name")["revenue"].sum().mean()
            if not lm_data.empty
            else 0
        )
        kpi.append(
            dbc.Col(metric_card("Avg Rev/App (Last Month)", f"${avg_last:,.0f}"), md=3)
        )
    else:
        kpi.append(dbc.Col(metric_card("Avg Rev/App (Last Month)", "N/A"), md=3))

    apps_count = (
        unified_f["application_name"].nunique()
        if not unified_f.empty and "application_name" in unified_f.columns
        else 0
    )
    kpi.append(dbc.Col(metric_card("Apps with Revenue", f"{apps_count:,}"), md=3))

    # Pivot Table
    pivot_content = html.P("No data", style={"color": NEUTRAL})
    if (
        not unified_f.empty
        and "month" in unified_f.columns
        and "application_name" in unified_f.columns
        and "revenue" in unified_f.columns
    ):
        agg = (
            unified_f.groupby(["application_name", "month"])["revenue"]
            .sum()
            .reset_index()
        )
        pivot = agg.pivot_table(
            index="application_name",
            columns="month",
            values="revenue",
            aggfunc="sum",
            fill_value=0,
        )
        pivot["Total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("Total", ascending=False).reset_index()
        pivot_content = dash_table.DataTable(
            data=pivot.to_dict("records"),
            columns=[
                (
                    {
                        "name": c,
                        "id": c,
                        "type": "numeric",
                        "format": {"specifier": "$,.0f"},
                    }
                    if c != "application_name"
                    else {"name": "Coach", "id": c}
                )
                for c in pivot.columns
            ],
            style_table={
                "overflowX": "auto",
                "maxHeight": "600px",
                "overflowY": "auto",
            },
            style_cell={
                "fontSize": "11px",
                "padding": "4px",
                "fontFamily": "Sora",
                "textAlign": "right",
                "minWidth": "80px",
            },
            style_header={
                "fontWeight": "600",
                "backgroundColor": "#F2F3EE",
                "textAlign": "center",
            },
            style_data_conditional=[
                {"if": {"column_id": "application_name"}, "textAlign": "left"}
            ],
            sort_action="native",
            filter_action="native",
            page_size=50,
        )

    # GMV Trend
    fig_trend = _empty_fig("No revenue data")
    fig_top = _empty_fig()
    if (
        not unified_f.empty
        and "month" in unified_f.columns
        and "revenue" in unified_f.columns
    ):
        if selected_app != "All Apps":
            monthly = (
                unified_f.groupby(["month", "revenue_source"])["revenue"]
                .sum()
                .reset_index()
            )
            fig_trend = px.bar(
                monthly,
                x="month",
                y="revenue",
                color="revenue_source",
                title=f"Monthly GMV — {selected_app}",
                barmode="stack",
                color_discrete_map={
                    "Stripe": GREEN,
                    "iOS App Store": TANGERINE,
                    "Google Play Store": ALPINE,
                },
            )
        else:
            monthly = (
                unified_rev.groupby(["month", "revenue_source"])["revenue"]
                .sum()
                .reset_index()
            )
            fig_trend = px.bar(
                monthly,
                x="month",
                y="revenue",
                color="revenue_source",
                title="Total Monthly GMV",
                barmode="stack",
                color_discrete_map={
                    "Stripe": GREEN,
                    "iOS App Store": TANGERINE,
                    "Google Play Store": ALPINE,
                },
            )
            top_coaches = (
                unified_rev.groupby("application_name")["revenue"]
                .sum()
                .nlargest(10)
                .index.tolist()
            )
            top_data = unified_rev[unified_rev["application_name"].isin(top_coaches)]
            top_monthly = (
                top_data.groupby(["month", "application_name"])["revenue"]
                .sum()
                .reset_index()
            )
            fig_top = px.bar(
                top_monthly,
                x="month",
                y="revenue",
                color="application_name",
                title="Monthly GMV — Top 10 Coaches",
                barmode="stack",
            )
            fig_top.update_layout(height=450)
        fig_trend.update_layout(height=400)

    # Summary Table
    summary_content = html.P("No data", style={"color": NEUTRAL})
    if not stages_f.empty:
        cols = [
            "application_name",
            "total_gmv",
            "kliq_revenue",
            "mrr",
            "total_subs",
            "avg_sub_price",
            "active_months",
            "growth_stage",
        ]
        avail = [c for c in cols if c in stages_f.columns]
        if avail:
            summary_content = dash_table.DataTable(
                data=stages_f[avail]
                .sort_values(avail[1] if len(avail) > 1 else avail[0], ascending=False)
                .to_dict("records"),
                columns=[{"name": c, "id": c} for c in avail],
                style_cell={
                    "fontSize": "12px",
                    "padding": "6px",
                    "fontFamily": "Sora",
                    "textAlign": "left",
                },
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
                sort_action="native",
                filter_action="native",
                page_size=25,
            )

    # IAP
    iap_kpi = []
    fig_iap = _empty_fig("No IAP data")
    iap_plan_table = html.P("No data", style={"color": NEUTRAL})
    fig_iap_pie = _empty_fig()
    try:
        iap = filt(load_inapp_purchases())
        if not iap.empty:
            total_p = int(iap["purchases"].sum()) if "purchases" in iap.columns else 0
            total_b = (
                int(iap["unique_buyers"].sum()) if "unique_buyers" in iap.columns else 0
            )
            iap_kpi = [
                dbc.Col(
                    metric_card("Total IAP", f"{total_p:,}"), md=12, className="mb-2"
                ),
                dbc.Col(metric_card("Unique Buyers", f"{total_b:,}"), md=12),
            ]
            if "month" in iap.columns and "purchases" in iap.columns:
                m_iap = iap.groupby("month")["purchases"].sum().reset_index()
                fig_iap = px.bar(
                    m_iap,
                    x="month",
                    y="purchases",
                    title="Monthly In-App Purchases",
                    color_discrete_sequence=[TANGERINE],
                )
                fig_iap.update_layout(height=300)
            sub_cols = [
                c
                for c in [
                    "monthly_purchases",
                    "quarterly_purchases",
                    "yearly_purchases",
                    "sixmonth_purchases",
                ]
                if c in iap.columns
            ]
            if sub_cols:
                sub_totals = {
                    c.replace("_purchases", "").title(): int(iap[c].sum())
                    for c in sub_cols
                }
                sub_df = pd.DataFrame(
                    list(sub_totals.items()), columns=["Plan Type", "Purchases"]
                )
                sub_df = sub_df[sub_df["Purchases"] > 0].sort_values(
                    "Purchases", ascending=False
                )
                if not sub_df.empty:
                    iap_plan_table = dash_table.DataTable(
                        data=sub_df.to_dict("records"),
                        columns=[{"name": c, "id": c} for c in sub_df.columns],
                        style_cell={
                            "fontSize": "12px",
                            "padding": "6px",
                            "fontFamily": "Sora",
                        },
                        style_header={
                            "fontWeight": "600",
                            "backgroundColor": "#F2F3EE",
                        },
                    )
                    fig_iap_pie = px.pie(
                        sub_df,
                        names="Plan Type",
                        values="Purchases",
                        title="Plan Type Split",
                    )
                    fig_iap_pie.update_layout(height=300)
    except Exception as _e:
        print(f"[gmv_table] chart error: {_e}")

    # Recurring
    rec_kpi = []
    fig_rec = _empty_fig("No recurring data")
    rec_plat_table = html.P("No data", style={"color": NEUTRAL})
    fig_rec_pie = _empty_fig()
    try:
        recurring = filt(load_recurring_payments())
        if not recurring.empty:
            total_r = (
                int(recurring["recurring_payments"].sum())
                if "recurring_payments" in recurring.columns
                else 0
            )
            total_u = (
                int(recurring["unique_users"].sum())
                if "unique_users" in recurring.columns
                else 0
            )
            rec_kpi = [
                dbc.Col(
                    metric_card("Total Recurring", f"{total_r:,}"),
                    md=12,
                    className="mb-2",
                ),
                dbc.Col(metric_card("Unique Users", f"{total_u:,}"), md=12),
            ]
            if (
                "month" in recurring.columns
                and "recurring_payments" in recurring.columns
            ):
                m_rec = (
                    recurring.groupby("month")["recurring_payments"].sum().reset_index()
                )
                fig_rec = px.bar(
                    m_rec,
                    x="month",
                    y="recurring_payments",
                    title="Monthly Recurring Payments",
                    color_discrete_sequence=[ALPINE],
                )
                fig_rec.update_layout(height=300)
            if "platform_type" in recurring.columns:
                pt = (
                    recurring.groupby("platform_type")["recurring_payments"]
                    .sum()
                    .reset_index()
                )
                pt.columns = ["Platform", "Payments"]
                rec_plat_table = dash_table.DataTable(
                    data=pt.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in pt.columns],
                    style_cell={
                        "fontSize": "12px",
                        "padding": "6px",
                        "fontFamily": "Sora",
                    },
                    style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
                )
                fig_rec_pie = px.pie(
                    pt, names="Platform", values="Payments", title="Platform Split"
                )
                fig_rec_pie.update_layout(height=300)
    except Exception as _e:
        print(f"[gmv_table] chart error: {_e}")

    return (
        kpi,
        pivot_content,
        fig_trend,
        fig_top,
        summary_content,
        iap_kpi,
        fig_iap,
        iap_plan_table,
        fig_iap_pie,
        rec_kpi,
        fig_rec,
        rec_plat_table,
        fig_rec_pie,
    )
