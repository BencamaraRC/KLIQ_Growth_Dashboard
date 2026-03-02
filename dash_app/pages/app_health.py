"""
Page 5 — App Health
MAU/DAU, user overview, engagement metrics, subscriptions,
device breakdown, user location. Filterable by app.
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
    NEUTRAL,
    CHART_SEQUENCE,
    metric_card,
    section_header,
    chart_card,
    card_wrapper,
)
from data import (
    load_app_lookup,
    load_app_engagement_d2,
    load_app_subscriptions,
    load_app_user_overview,
    load_app_dau,
    load_app_mau,
    load_app_device_breakdown,
    load_app_downloads,
    load_ga4_acquisition,
)

dash.register_page(
    __name__, path="/app-health", name="App Health", title="App Health — KLIQ"
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
            "App Health", style={"fontSize": "20px", "fontWeight": "700", "color": DARK}
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Select App",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dcc.Dropdown(
                            id="health-app-filter",
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
                            id="health-date-range",
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
        # KPIs
        dbc.Row(id="health-kpi-row", className="mb-3"),
        html.Hr(),
        # MAU
        section_header("📊 Monthly Active Users (MAU)"),
        chart_card(dcc.Graph(id="health-mau")),
        # DAU + User Overview
        dbc.Row(
            [
                dbc.Col(
                    [
                        section_header("📅 Daily Active Users"),
                        chart_card(dcc.Graph(id="health-dau")),
                    ],
                    md=6,
                ),
                dbc.Col(
                    [
                        section_header("👥 User Overview"),
                        card_wrapper(html.Div(id="health-user-table")),
                    ],
                    md=6,
                ),
            ]
        ),
        html.Hr(),
        # Engagement
        section_header("⚡ Engagement Metrics"),
        chart_card(dcc.Graph(id="health-engagement")),
        # Subscriptions
        section_header("💳 Subscriptions & Revenue"),
        chart_card(dcc.Graph(id="health-subs")),
        html.Hr(),
        # Device + Downloads
        section_header("📱 Device Breakdown & Downloads"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="health-device-pie")), md=6),
                dbc.Col(card_wrapper(html.Div(id="health-downloads-table")), md=6),
            ]
        ),
        html.Hr(),
        # User Location
        section_header("🌍 User Location"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="health-map")), md=8),
                dbc.Col(card_wrapper(html.Div(id="health-country-table")), md=4),
            ]
        ),
    ]
)


@callback(Output("health-app-filter", "options"), Input("health-app-filter", "value"))
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
    Output("health-kpi-row", "children"),
    Output("health-mau", "figure"),
    Output("health-dau", "figure"),
    Output("health-user-table", "children"),
    Output("health-engagement", "figure"),
    Output("health-subs", "figure"),
    Output("health-device-pie", "figure"),
    Output("health-downloads-table", "children"),
    Output("health-map", "figure"),
    Output("health-country-table", "children"),
    Input("health-app-filter", "value"),
    Input("health-date-range", "value"),
)
def update_health(selected_app, days_back):
    apps = load_app_lookup()
    app_map = {}
    if (
        not apps.empty
        and "application_name" in apps.columns
        and "application_id" in apps.columns
    ):
        app_map = dict(zip(apps["application_name"], apps["application_id"]))
    app_id = app_map.get(selected_app) if selected_app != "All Apps" else None

    def filt_id(df):
        if app_id is None or df.empty or "application_id" not in df.columns:
            return df
        return df[df["application_id"] == app_id]

    def filt_name(df):
        if (
            selected_app == "All Apps"
            or df.empty
            or "application_name" not in df.columns
        ):
            return df
        return df[df["application_name"] == selected_app]

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

    # KPIs
    kpi = []
    try:
        users_all = load_app_user_overview()
        users_kpi = filt_id(users_all) if selected_app != "All Apps" else users_all
        total_reg = (
            int(users_kpi["total_users"].sum())
            if not users_kpi.empty and "total_users" in users_kpi.columns
            else 0
        )
        regular = (
            int(users_kpi["regular_users"].sum())
            if not users_kpi.empty and "regular_users" in users_kpi.columns
            else 0
        )
        web_u = (
            int(users_kpi["web_users"].sum())
            if not users_kpi.empty and "web_users" in users_kpi.columns
            else 0
        )
        app_u = (
            int(users_kpi["app_users"].sum())
            if not users_kpi.empty and "app_users" in users_kpi.columns
            else 0
        )
        kpi = [
            dbc.Col(metric_card("Total Users", f"{total_reg:,}"), md=3),
            dbc.Col(metric_card("Regular Users", f"{regular:,}"), md=3),
            dbc.Col(metric_card("Web Users", f"{web_u:,}"), md=3),
            dbc.Col(metric_card("App Users", f"{app_u:,}"), md=3),
        ]
    except Exception as _e:
        print(f"[app_health] chart error: {_e}")

    # MAU
    fig_mau = _empty_fig("No MAU data")
    try:
        mau = filt_id(load_app_mau())
        if not mau.empty and "month" in mau.columns and "mau" in mau.columns:
            agg = mau.groupby("month")["mau"].sum().reset_index()
            fig_mau = px.bar(
                agg,
                x="month",
                y="mau",
                title=(
                    f"MAU — {selected_app}"
                    if selected_app != "All Apps"
                    else "Total MAU"
                ),
                labels={"mau": "MAU", "month": "Month"},
            )
            fig_mau.update_layout(height=400)
    except Exception as _e:
        print(f"[app_health] chart error: {_e}")

    # DAU
    fig_dau = _empty_fig("No DAU data")
    try:
        dau = filt_date(filt_id(load_app_dau()), "date")
        if not dau.empty and "date" in dau.columns and "dau" in dau.columns:
            dau = dau.copy()
            dau["date"] = pd.to_datetime(dau["date"], errors="coerce")
            agg = dau.groupby("date")["dau"].sum().reset_index()
            fig_dau = px.line(
                agg,
                x="date",
                y="dau",
                title=(
                    f"DAU — {selected_app}"
                    if selected_app != "All Apps"
                    else "Total DAU"
                ),
            )
            fig_dau.update_layout(height=350)
    except Exception as _e:
        print(f"[app_health] chart error: {_e}")

    # User Overview
    user_table = html.P("No data", style={"color": NEUTRAL})
    try:
        users = filt_id(load_app_user_overview())
        if not users.empty:
            cols = [
                c
                for c in [
                    "application_name",
                    "total_users",
                    "talent_users",
                    "regular_users",
                    "web_users",
                    "app_users",
                ]
                if c in users.columns
            ]
            user_table = dash_table.DataTable(
                data=(
                    users[cols].to_dict("records") if cols else users.to_dict("records")
                ),
                columns=[{"name": c, "id": c} for c in (cols or users.columns)],
                style_cell={
                    "fontSize": "12px",
                    "padding": "6px",
                    "fontFamily": "Sora",
                    "textAlign": "left",
                },
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
                page_size=20,
                sort_action="native",
            )
    except Exception as _e:
        print(f"[app_health] chart error: {_e}")

    # Engagement
    fig_eng = _empty_fig("No engagement data")
    try:
        eng = filt_date(filt_id(load_app_engagement_d2()), "date")
        if (
            not eng.empty
            and "metric" in eng.columns
            and "date" in eng.columns
            and "value" in eng.columns
        ):
            eng = eng.copy()
            eng["date"] = pd.to_datetime(eng["date"], errors="coerce")
            eng["week"] = eng["date"].dt.to_period("W").dt.start_time
            top_metrics = (
                eng.groupby("metric")["value"].sum().nlargest(5).index.tolist()
            )
            filtered = eng[eng["metric"].isin(top_metrics)]
            weekly = filtered.groupby(["week", "metric"])["value"].sum().reset_index()
            fig_eng = px.line(
                weekly,
                x="week",
                y="value",
                color="metric",
                title="Weekly Engagement (Top 5)",
            )
            fig_eng.update_layout(height=450)
    except Exception as _e:
        print(f"[app_health] chart error: {_e}")

    # Subscriptions
    fig_subs = _empty_fig("No subscription data")
    try:
        subs = filt_date(filt_id(load_app_subscriptions()), "date")
        if (
            not subs.empty
            and "metric" in subs.columns
            and "date" in subs.columns
            and "value" in subs.columns
        ):
            subs = subs.copy()
            subs["date"] = pd.to_datetime(subs["date"], errors="coerce")
            subs["month"] = subs["date"].dt.to_period("M").dt.start_time
            top_m = subs.groupby("metric")["value"].sum().nlargest(4).index.tolist()
            filtered = subs[subs["metric"].isin(top_m)]
            monthly = filtered.groupby(["month", "metric"])["value"].sum().reset_index()
            fig_subs = px.bar(
                monthly,
                x="month",
                y="value",
                color="metric",
                title="Subscriptions & Revenue",
                barmode="group",
            )
            fig_subs.update_layout(height=450)
    except Exception as _e:
        print(f"[app_health] chart error: {_e}")

    # Device Breakdown
    fig_dev = _empty_fig("No device data")
    try:
        devices = filt_name(load_app_device_breakdown())
        if (
            not devices.empty
            and "device" in devices.columns
            and "unique_users" in devices.columns
        ):
            agg = (
                devices.groupby("device")["unique_users"].sum().reset_index()
                if selected_app == "All Apps"
                else devices
            )
            fig_dev = px.pie(
                agg, names="device", values="unique_users", title="Users by Device Type"
            )
            fig_dev.update_layout(height=350)
    except Exception as _e:
        print(f"[app_health] chart error: {_e}")

    # Downloads
    dl_table = html.P("No data", style={"color": NEUTRAL})
    try:
        downloads = filt_name(load_app_downloads())
        if not downloads.empty:
            cols = [
                c
                for c in [
                    "application_name",
                    "ios_first_downloads",
                    "ios_redownloads",
                    "ios_total_downloads",
                    "kliq_registered_users",
                ]
                if c in downloads.columns
            ]
            dl_table = [
                html.H6(
                    "App Downloads (iOS + KLIQ Registered)",
                    style={"fontWeight": "600", "marginBottom": "8px"},
                ),
                dash_table.DataTable(
                    data=(
                        downloads[cols].to_dict("records")
                        if cols
                        else downloads.to_dict("records")
                    ),
                    columns=[{"name": c, "id": c} for c in (cols or downloads.columns)],
                    style_cell={
                        "fontSize": "12px",
                        "padding": "6px",
                        "fontFamily": "Sora",
                        "textAlign": "left",
                    },
                    style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
                    page_size=15,
                    sort_action="native",
                ),
            ]
    except Exception as _e:
        print(f"[app_health] chart error: {_e}")

    # User Location
    fig_map = _empty_fig("No location data")
    country_table = html.P("No data", style={"color": NEUTRAL})
    try:
        acq = load_ga4_acquisition()
        if not acq.empty and "country" in acq.columns and "unique_users" in acq.columns:
            ca = acq.groupby("country")["unique_users"].sum().nlargest(25).reset_index()
            fig_map = px.choropleth(
                ca,
                locations="country",
                locationmode="country names",
                color="unique_users",
                title="Users by Country",
                color_continuous_scale=[
                    [0, "#9CF0FF"],
                    [0.5, "#1C3838"],
                    [1, "#021111"],
                ],
                labels={"unique_users": "Users"},
            )
            fig_map.update_layout(height=450)
            country_table = dash_table.DataTable(
                data=ca.to_dict("records"),
                columns=[
                    {"name": "Country", "id": "country"},
                    {"name": "Users", "id": "unique_users"},
                ],
                style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            )
    except Exception as _e:
        print(f"[app_health] chart error: {_e}")

    return (
        kpi,
        fig_mau,
        fig_dau,
        user_table,
        fig_eng,
        fig_subs,
        fig_dev,
        dl_table,
        fig_map,
        country_table,
    )
