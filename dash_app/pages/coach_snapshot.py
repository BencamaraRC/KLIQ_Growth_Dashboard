"""
Page 3 — Coach Snapshot
Total GMV, paid to KLIQ, hosting fee, currency, months active,
KLIQ fee %, GMV timeline, MAU/DAU, app opens.
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
    BG_CARD,
    CARD_RADIUS,
    SHADOW_CARD,
    metric_card,
    section_header,
    chart_card,
    card_wrapper,
)
from data import (
    load_coach_summary,
    load_coach_growth_stages,
    load_coach_gmv_timeline,
    load_unified_revenue,
    load_app_lookup,
    load_app_mau,
    load_app_dau,
    load_app_engagement_d2,
    load_churn_analysis,
)

dash.register_page(
    __name__,
    path="/coach-snapshot",
    name="Coach Snapshot",
    title="Coach Snapshot — KLIQ",
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
            "Coach Snapshot",
            style={"fontSize": "20px", "fontWeight": "700", "color": DARK},
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
                            id="snap-app-filter",
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
                            id="snap-date-range",
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
        section_header("Key Metrics"),
        dbc.Row(id="snap-kpi-row", className="mb-3"),
        html.Div(id="snap-revenue-source"),
        html.Hr(),
        # GMV Timeline
        section_header("📈 GMV Timeline (All Sources)"),
        chart_card(dcc.Graph(id="snap-gmv-chart")),
        chart_card(dcc.Graph(id="snap-top-coaches-chart")),
        html.Hr(),
        # MAU / DAU
        section_header("📊 MAU, DAU & App Opens"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="snap-mau-chart")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="snap-dau-chart")), md=6),
            ]
        ),
        chart_card(dcc.Graph(id="snap-opens-chart")),
        html.Hr(),
        # Coach Detail Table
        section_header("📋 Coach Detail"),
        card_wrapper(html.Div(id="snap-detail-table")),
    ]
)


@callback(
    Output("snap-app-filter", "options"),
    Input("snap-app-filter", "value"),
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
    Output("snap-kpi-row", "children"),
    Output("snap-revenue-source", "children"),
    Output("snap-gmv-chart", "figure"),
    Output("snap-top-coaches-chart", "figure"),
    Output("snap-mau-chart", "figure"),
    Output("snap-dau-chart", "figure"),
    Output("snap-opens-chart", "figure"),
    Output("snap-detail-table", "children"),
    Input("snap-app-filter", "value"),
    Input("snap-date-range", "value"),
)
def update_snapshot(selected_app, days_back):
    summary = load_coach_summary()
    stages = load_coach_growth_stages()
    unified_rev = load_unified_revenue()

    def filter_by_name(df):
        if (
            selected_app == "All Apps"
            or df.empty
            or "application_name" not in df.columns
        ):
            return df
        return df[df["application_name"] == selected_app]

    summary_f = filter_by_name(summary)
    stages_f = filter_by_name(stages)
    unified_f = filter_by_name(unified_rev)

    # Get app_id for MAU/DAU filtering
    apps = load_app_lookup()
    app_map = {}
    if (
        not apps.empty
        and "application_name" in apps.columns
        and "application_id" in apps.columns
    ):
        app_map = dict(zip(apps["application_name"], apps["application_id"]))
    app_id = app_map.get(selected_app) if selected_app != "All Apps" else None

    def filter_by_id(df):
        if app_id is None or df.empty or "application_id" not in df.columns:
            return df
        return df[df["application_id"] == app_id]

    def filt_date(df, date_col="date"):
        if (
            days_back is None
            or days_back >= 99999
            or df.empty
            or date_col not in df.columns
        ):
            return df
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        cutoff = datetime.now() - timedelta(days=days_back)
        return df[df[date_col] >= cutoff]

    # Total GMV
    total_gmv = (
        unified_f["revenue"].sum()
        if not unified_f.empty and "revenue" in unified_f.columns
        else 0
    )

    # ── KPI Cards ──
    kpi_children = []
    rev_source_content = []

    if selected_app != "All Apps" and not summary_f.empty:
        row = summary_f.iloc[0]
        kpi_children = [
            dbc.Col(metric_card("Total GMV", f"${total_gmv:,.0f}"), md=3),
            dbc.Col(
                metric_card(
                    "Paid to KLIQ", f"${row.get('total_app_fee_to_kliq', 0) or 0:,.0f}"
                ),
                md=3,
            ),
            dbc.Col(
                metric_card(
                    "Hosting Fee",
                    f"${row.get('hosting_fee_last_month', 0) or 0:,.0f}",
                    "Last Month",
                ),
                md=3,
            ),
            dbc.Col(metric_card("Currency", str(row.get("currency", "N/A"))), md=3),
        ]
        kpi_children += [
            dbc.Col(
                metric_card("Months Active", f"{row.get('months_on_platform', 'N/A')}"),
                md=3,
            ),
            dbc.Col(
                metric_card(
                    "KLIQ Fee %", f"{row.get('kliq_revenue_pct', 0) or 0:.1f}%"
                ),
                md=3,
            ),
            dbc.Col(metric_card("Latest MAU", f"{row.get('latest_mau', 'N/A')}"), md=3),
            dbc.Col(
                metric_card(
                    "Active Subs",
                    f"{stages_f.iloc[0].get('total_subs', 'N/A') if not stages_f.empty else 'N/A'}",
                ),
                md=3,
            ),
        ]
    else:
        kliq_total = (
            summary["total_app_fee_to_kliq"].sum()
            if not summary.empty and "total_app_fee_to_kliq" in summary.columns
            else 0
        )
        mrr = stages["mrr"].sum() if not stages.empty and "mrr" in stages.columns else 0
        kpi_children = [
            dbc.Col(metric_card("Total GMV", f"${total_gmv:,.0f}"), md=3),
            dbc.Col(metric_card("Total Paid to KLIQ", f"${kliq_total:,.0f}"), md=3),
            dbc.Col(metric_card("Total Coaches", f"{len(summary):,}"), md=3),
            dbc.Col(metric_card("Total MRR", f"${mrr:,.0f}"), md=3),
        ]

    # Revenue source breakdown
    src_df = unified_f if selected_app != "All Apps" else unified_rev
    if not src_df.empty and "revenue_source" in src_df.columns:
        src_totals = src_df.groupby("revenue_source")["revenue"].sum().reset_index()
        src_totals.columns = ["Source", "Revenue"]
        fig_src = px.pie(
            src_totals, names="Source", values="Revenue", title="GMV by Revenue Source"
        )
        fig_src.update_layout(height=300)
        rev_source_content = chart_card(dcc.Graph(figure=fig_src))

    # ── GMV Timeline ──
    fig_gmv = _empty_fig("No revenue data")
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
            fig_gmv = px.bar(
                monthly,
                x="month",
                y="revenue",
                color="revenue_source",
                title=f"Monthly GMV — {selected_app}",
                labels={"revenue": "GMV ($)", "month": "Month"},
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
            fig_gmv = px.bar(
                monthly,
                x="month",
                y="revenue",
                color="revenue_source",
                title="Monthly GMV — All Coaches",
                labels={"revenue": "GMV ($)", "month": "Month"},
                barmode="stack",
                color_discrete_map={
                    "Stripe": GREEN,
                    "iOS App Store": TANGERINE,
                    "Google Play Store": ALPINE,
                },
            )
            # Top 10 coaches
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
            fig_top = px.line(
                top_monthly,
                x="month",
                y="revenue",
                color="application_name",
                title="Monthly GMV — Top 10 Coaches",
                labels={"revenue": "GMV ($)", "month": "Month"},
            )
            fig_top.update_layout(height=400)
        fig_gmv.update_layout(height=450)

    # ── MAU ──
    fig_mau = _empty_fig("No MAU data")
    try:
        mau = filter_by_id(load_app_mau())
        if not mau.empty and "month" in mau.columns and "mau" in mau.columns:
            agg = mau.groupby("month")["mau"].sum().reset_index()
            title = (
                f"MAU — {selected_app}" if selected_app != "All Apps" else "Total MAU"
            )
            fig_mau = px.bar(
                agg,
                x="month",
                y="mau",
                title=title,
                labels={"mau": "MAU", "month": "Month"},
            )
            fig_mau.update_layout(height=350)
    except Exception as _e:
        print(f"[coach_snapshot] chart error: {_e}")

    # ── DAU ──
    fig_dau = _empty_fig("No DAU data")
    try:
        dau = filt_date(filter_by_id(load_app_dau()), "date")
        if not dau.empty and "date" in dau.columns and "dau" in dau.columns:
            dau = dau.copy()
            dau["date"] = pd.to_datetime(dau["date"], errors="coerce")
            agg = dau.groupby("date")["dau"].sum().reset_index()
            title = (
                f"DAU — {selected_app}" if selected_app != "All Apps" else "Total DAU"
            )
            fig_dau = px.line(
                agg,
                x="date",
                y="dau",
                title=title,
                labels={"dau": "DAU", "date": "Date"},
            )
            fig_dau.update_layout(height=350)
    except Exception as _e:
        print(f"[coach_snapshot] chart error: {_e}")

    # ── App Opens ──
    fig_opens = _empty_fig("No app opens data")
    try:
        engagement = filt_date(filter_by_id(load_app_engagement_d2()), "date")
        if (
            not engagement.empty
            and "metric" in engagement.columns
            and "value" in engagement.columns
        ):
            app_opens = engagement[
                engagement["metric"].str.contains("app_open|open", case=False, na=False)
            ]
            if not app_opens.empty and "date" in app_opens.columns:
                app_opens = app_opens.copy()
                app_opens["date"] = pd.to_datetime(app_opens["date"], errors="coerce")
                app_opens["week"] = app_opens["date"].dt.to_period("W").dt.start_time
                weekly = app_opens.groupby("week")["value"].sum().reset_index()
                fig_opens = px.bar(
                    weekly,
                    x="week",
                    y="value",
                    title=(
                        f"Weekly App Opens — {selected_app}"
                        if selected_app != "All Apps"
                        else "Weekly App Opens"
                    ),
                    labels={"value": "App Opens", "week": "Week"},
                )
                fig_opens.update_layout(height=350)
    except Exception as _e:
        print(f"[coach_snapshot] chart error: {_e}")

    # ── Detail Table ──
    detail_table = html.P("No data", style={"color": NEUTRAL})
    if not summary_f.empty:
        detail_table = dash_table.DataTable(
            data=summary_f.to_dict("records"),
            columns=[{"name": c, "id": c} for c in summary_f.columns],
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

    return (
        kpi_children,
        rev_source_content,
        fig_gmv,
        fig_top,
        fig_mau,
        fig_dau,
        fig_opens,
        detail_table,
    )
