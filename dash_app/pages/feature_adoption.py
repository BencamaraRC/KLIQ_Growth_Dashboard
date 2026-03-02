"""
Page 11 — Feature Adoption
Per-app feature usage and platform-wide feature adoption analysis.
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
    IVORY,
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
    load_feature_adoption_platform,
    load_feature_adoption_per_app,
    load_feature_monthly_trend,
    load_total_coach_apps,
    load_feature_frequency,
    load_module_adoption,
    load_module_monthly_trend,
    MODULE_MAP,
    FEATURE_LABELS,
)

dash.register_page(
    __name__,
    path="/feature-adoption",
    name="Feature Adoption",
    title="Feature Adoption — KLIQ",
)

FEATURE_CATEGORIES = {
    "Engagement": [
        "app_opened",
        "visits_community_page",
        "visits_blog",
        "visits_library_page",
        "visits_program_page",
        "visits_program_detail_page",
        "visits_nutrition_page",
        "visits_course_blog",
    ],
    "Content Consumption": [
        "engage_with_blog_post",
        "completes_program_workout",
        "starts_library_video",
        "completes_library_video",
        "ends_library_video",
        "engages_with_recipe",
        "starts_past_session",
        "ends_past_session",
        "completes_past_session",
        "starts_program",
        "completes_program",
    ],
    "Community": [
        "like_on_community_post",
        "replies_on_community",
        "post_on_community",
        "post_on_community_feed_with_photo",
        "post_on_community_feed_with_voice_notes",
        "saved_post",
        "commented_in_live_session",
        "post_comment_in_past_session",
    ],
    "Live Sessions": ["live_session_created", "live_session_joined"],
    "Revenue": [
        "user_subscribed",
        "recurring_payment",
        "purchase_success",
        "start_purchase",
        "checkout_completion",
        "cancels_subscription",
        "purchase_cancelled",
        "promo_code_used_talent",
    ],
    "Coach Tools": [
        "create_module",
        "edit_module",
        "publish_module",
        "creates_program",
        "publishes_program",
    ],
    "Other": [
        "favourited_session_video",
        "favourites_recipe",
        "favourites_library",
        "connects_health_device",
        "completed_1_to_1_session",
        "1_to_1_session_schedule",
    ],
}


def _label(event_name):
    return FEATURE_LABELS.get(event_name, event_name.replace("_", " ").title())


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


def _color_card(bg, label, value, desc):
    return html.Div(
        [
            html.P(
                label,
                style={
                    "margin": "0",
                    "fontSize": "11px",
                    "fontWeight": "600",
                    "letterSpacing": "0.04em",
                    "textTransform": "uppercase",
                    "opacity": "0.7",
                    "color": IVORY,
                },
            ),
            html.H3(
                value,
                style={
                    "margin": "6px 0",
                    "fontSize": "1.5rem",
                    "fontWeight": "700",
                    "lineHeight": "1.1",
                    "color": IVORY,
                },
            ),
            html.P(
                desc,
                style={
                    "margin": "0",
                    "fontSize": "12px",
                    "opacity": "0.75",
                    "color": IVORY,
                },
            ),
        ],
        style={
            "background": bg,
            "padding": "16px",
            "borderRadius": f"{CARD_RADIUS}px",
            "textAlign": "center",
            "boxShadow": SHADOW_CARD,
        },
    )


layout = html.Div(
    [
        html.H1(
            "Feature Adoption",
            style={"fontSize": "20px", "fontWeight": "700", "color": DARK},
        ),
        html.P(
            "Which features are most used per app and across the platform",
            style={"color": NEUTRAL, "fontSize": "13px"},
        ),
        html.Hr(),
        # Date Range Filter
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Date Range",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dcc.Dropdown(
                            id="fa-date-range",
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
        dbc.Row(id="fa-kpi-row", className="mb-3"),
        # Top Features
        section_header("Platform-Wide Feature Adoption"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="fa-top25")), md=7),
                dbc.Col(card_wrapper(html.Div(id="fa-platform-table")), md=5),
            ]
        ),
        html.Hr(),
        # Category Breakdown
        section_header("Feature Adoption by Category"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="fa-cat-pie")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="fa-cat-bar")), md=6),
            ]
        ),
        card_wrapper(html.Div(id="fa-cat-table")),
        html.Hr(),
        # Coach Uptake
        section_header("Coach Uptake by Feature"),
        html.Div(id="fa-uptake-cards", className="mb-3"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="fa-uptake-pie")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="fa-uptake-bar")), md=6),
            ]
        ),
        card_wrapper(html.Div(id="fa-uptake-table")),
        html.Hr(),
        # Frequency
        section_header("Feature Usage Frequency"),
        html.Div(id="fa-freq-cards", className="mb-3"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="fa-freq-chart")), md=7),
                dbc.Col(card_wrapper(html.Div(id="fa-freq-table")), md=5),
            ]
        ),
        html.Hr(),
        # Monthly Trends
        section_header("Feature Trends Over Time"),
        chart_card(dcc.Graph(id="fa-trend")),
        chart_card(dcc.Graph(id="fa-trend-apps")),
        html.Hr(),
        # Module Adoption
        section_header("Module Adoption Breakdown"),
        html.Div(id="fa-module-kpi-cards", className="mb-3"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="fa-module-uptake-pie")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="fa-module-bar")), md=6),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="fa-module-events-pie")), md=5),
                dbc.Col(card_wrapper(html.Div(id="fa-module-table")), md=7),
            ]
        ),
        chart_card(dcc.Graph(id="fa-module-trend")),
        chart_card(dcc.Graph(id="fa-module-apps-trend")),
        html.Hr(),
        # Per-App Feature Usage
        section_header("Per-App Feature Usage"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Select App",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dcc.Dropdown(
                            id="fa-app-filter",
                            options=[],
                            placeholder="Select an app",
                            style={"fontSize": "13px"},
                        ),
                    ],
                    md=4,
                ),
            ],
            className="mb-3",
        ),
        dbc.Row(id="fa-app-kpi-row", className="mb-3"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="fa-app-chart")), md=7),
                dbc.Col(card_wrapper(html.Div(id="fa-app-detail-table")), md=5),
            ]
        ),
        chart_card(dcc.Graph(id="fa-app-cat-chart")),
        chart_card(dcc.Graph(id="fa-app-vs-platform")),
        card_wrapper(html.Div(id="fa-app-vs-table")),
        dcc.Store(id="fa-trigger", data=True),
    ]
)


@callback(
    Output("fa-kpi-row", "children"),
    Output("fa-top25", "figure"),
    Output("fa-platform-table", "children"),
    Output("fa-cat-pie", "figure"),
    Output("fa-cat-bar", "figure"),
    Output("fa-cat-table", "children"),
    Output("fa-uptake-cards", "children"),
    Output("fa-uptake-pie", "figure"),
    Output("fa-uptake-bar", "figure"),
    Output("fa-uptake-table", "children"),
    Output("fa-freq-cards", "children"),
    Output("fa-freq-chart", "figure"),
    Output("fa-freq-table", "children"),
    Output("fa-trend", "figure"),
    Output("fa-trend-apps", "figure"),
    Output("fa-module-kpi-cards", "children"),
    Output("fa-module-uptake-pie", "figure"),
    Output("fa-module-bar", "figure"),
    Output("fa-module-events-pie", "figure"),
    Output("fa-module-table", "children"),
    Output("fa-module-trend", "figure"),
    Output("fa-module-apps-trend", "figure"),
    Output("fa-app-filter", "options"),
    Input("fa-date-range", "value"),
    Input("fa-trigger", "data"),
)
def update_feature_adoption(days_back, _):
    platform_df = load_feature_adoption_platform()
    trend_df = load_feature_monthly_trend()
    total_coach_apps = load_total_coach_apps()
    freq_df = load_feature_frequency()
    module_df = load_module_adoption()
    module_trend_df = load_module_monthly_trend()
    per_app_df = load_feature_adoption_per_app()

    # Apply date range filter
    if days_back and days_back < 99999:
        cutoff_month = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m")
        if not trend_df.empty and "month" in trend_df.columns:
            trend_df = trend_df[trend_df["month"] >= cutoff_month].copy()
        if not module_trend_df.empty and "month" in module_trend_df.columns:
            module_trend_df = module_trend_df[
                module_trend_df["month"] >= cutoff_month
            ].copy()
        if not platform_df.empty and "last_seen" in platform_df.columns:
            platform_df = platform_df[platform_df["last_seen"] >= cutoff_month].copy()

    e = _empty_fig("No data")
    nd = html.P("No data", style={"color": NEUTRAL})

    if platform_df.empty:
        return (
            [],
            e,
            nd,
            e,
            e,
            nd,
            [],
            e,
            e,
            nd,
            [],
            e,
            nd,
            e,
            e,
            [],
            e,
            e,
            e,
            nd,
            e,
            e,
            [],
        )

    total_events = platform_df["total_events"].sum()
    total_features = len(platform_df)
    total_apps = platform_df["apps_using"].max() if not platform_df.empty else 0
    non_open = platform_df[platform_df["event_name"] != "app_opened"]
    top_feat_name = (
        _label(non_open.iloc[0]["event_name"]) if not non_open.empty else "N/A"
    )
    top_feat_apps = int(non_open.iloc[0]["apps_using"]) if not non_open.empty else 0

    kpi = [
        dbc.Col(
            _color_card(
                GREEN,
                "Total Events",
                f"{total_events:,.0f}",
                "All-time across platform",
            ),
            md=3,
        ),
        dbc.Col(
            _color_card(
                DARK,
                "Distinct Features",
                f"{total_features:,}",
                "Unique event types tracked",
            ),
            md=3,
        ),
        dbc.Col(
            _color_card(
                TANGERINE, "Apps Tracked", f"{total_apps:,}", "Apps with any events"
            ),
            md=3,
        ),
        dbc.Col(
            _color_card(
                ALPINE,
                "Most Adopted Feature",
                top_feat_name,
                f"Used by {top_feat_apps:,} apps",
            ),
            md=3,
        ),
    ]

    # Top 25 bar chart
    top25 = platform_df.head(25).copy()
    top25["feature"] = top25["event_name"].map(_label)
    fig_top = px.bar(
        top25,
        x="total_events",
        y="feature",
        orientation="h",
        color="apps_using",
        color_continuous_scale=["#e8f5e9", GREEN],
        labels={
            "total_events": "Total Events",
            "feature": "",
            "apps_using": "Apps Using",
        },
        title="Top 25 Features by Total Events",
    )
    fig_top.update_layout(
        yaxis=dict(autorange="reversed", categoryorder="total ascending"),
        height=650,
        margin=dict(l=10, r=10, t=40, b=10),
    )

    # Platform table
    disp = platform_df.copy()
    disp["Feature"] = disp["event_name"].map(_label)
    disp = disp.rename(
        columns={
            "total_events": "Total Events",
            "apps_using": "Apps Using",
            "months_active": "Months Active",
            "first_seen": "First Seen",
            "last_seen": "Last Seen",
        }
    )
    plat_table = dash_table.DataTable(
        data=disp[
            [
                "Feature",
                "Total Events",
                "Apps Using",
                "Months Active",
                "First Seen",
                "Last Seen",
            ]
        ].to_dict("records"),
        columns=[
            {"name": c, "id": c}
            for c in [
                "Feature",
                "Total Events",
                "Apps Using",
                "Months Active",
                "First Seen",
                "Last Seen",
            ]
        ],
        style_table={"maxHeight": "650px", "overflowY": "auto"},
        style_cell={
            "fontSize": "11px",
            "padding": "5px",
            "fontFamily": "Sora",
            "textAlign": "right",
        },
        style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
        style_data_conditional=[{"if": {"column_id": "Feature"}, "textAlign": "left"}],
        sort_action="native",
        page_size=50,
    )

    # Category breakdown
    cat_data = []
    for cat, events in FEATURE_CATEGORIES.items():
        cr = platform_df[platform_df["event_name"].isin(events)]
        if not cr.empty:
            cat_data.append(
                {
                    "Category": cat,
                    "Features": len(cr),
                    "Total Events": cr["total_events"].sum(),
                    "Avg Apps Using": round(cr["apps_using"].mean(), 1),
                    "Top Feature": _label(cr.iloc[0]["event_name"]),
                    "Top Feature Events": int(cr.iloc[0]["total_events"]),
                }
            )
    cat_df = (
        pd.DataFrame(cat_data).sort_values("Total Events", ascending=False)
        if cat_data
        else pd.DataFrame()
    )

    fig_cat_pie = _empty_fig()
    fig_cat_bar = _empty_fig()
    cat_table = nd
    if not cat_df.empty:
        fig_cat_pie = px.pie(
            cat_df,
            values="Total Events",
            names="Category",
            title="Events by Category",
            color_discrete_sequence=CHART_SEQUENCE,
            hole=0.4,
        )
        fig_cat_pie.update_layout(height=400)
        fig_cat_bar = px.bar(
            cat_df,
            x="Category",
            y="Avg Apps Using",
            color="Category",
            color_discrete_sequence=CHART_SEQUENCE,
            title="Avg Apps Using Features (by Category)",
        )
        fig_cat_bar.update_layout(height=400, showlegend=False)
        cat_table = dash_table.DataTable(
            data=cat_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in cat_df.columns],
            style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
        )

    # Coach Uptake — cards + pie + bar + table
    uptake_cards_content = []
    fig_uptake_pie = _empty_fig()
    fig_uptake = _empty_fig()
    uptake_table = nd
    if not platform_df.empty and total_coach_apps > 0:
        udf = platform_df[platform_df["event_name"] != "app_opened"].copy()
        udf["feature"] = udf["event_name"].map(_label)
        udf["uptake_pct"] = (udf["apps_using"] / total_coach_apps * 100).round(1)
        udf = udf.sort_values("uptake_pct", ascending=False)

        # Top 8 uptake cards
        top_uptake = udf.head(8)
        card_cols = []
        for _, row in top_uptake.iterrows():
            pct = row["uptake_pct"]
            bg = GREEN if pct >= 30 else (ALPINE if pct >= 15 else TANGERINE)
            card_cols.append(
                dbc.Col(
                    _color_card(
                        bg,
                        str(row["feature"])[:25],
                        f"{pct:.1f}%",
                        f"{int(row['apps_using']):,} of {total_coach_apps:,} apps",
                    ),
                    md=3,
                    className="mb-2",
                )
            )
        uptake_cards_content = dbc.Row(card_cols)

        # Uptake pie (top 10)
        pie_data = udf.head(10)
        fig_uptake_pie = px.pie(
            pie_data,
            values="uptake_pct",
            names="feature",
            title="Top 10 Features by Coach Uptake %",
            color_discrete_sequence=CHART_SEQUENCE,
            hole=0.4,
        )
        fig_uptake_pie.update_traces(textinfo="label+percent", textposition="outside")
        fig_uptake_pie.update_layout(height=450, showlegend=False)

        # Uptake bar (top 20)
        bar_data = udf.head(20)
        fig_uptake = px.bar(
            bar_data,
            x="uptake_pct",
            y="feature",
            orientation="h",
            color="uptake_pct",
            color_continuous_scale=["#ffccbc", GREEN],
            labels={"uptake_pct": "Coach Uptake %", "feature": ""},
            title=f"Coach Uptake % (Top 20 Features)",
        )
        fig_uptake.update_layout(
            yaxis=dict(autorange="reversed", categoryorder="total ascending"),
            height=500,
            margin=dict(l=10, r=10, t=40, b=10),
        )

        ut = udf[["feature", "apps_using", "uptake_pct", "total_events"]].copy()
        ut.columns = ["Feature", "Apps Using", "Uptake %", "Total Events"]
        uptake_table = dash_table.DataTable(
            data=ut.to_dict("records"),
            columns=[{"name": c, "id": c} for c in ut.columns],
            style_table={"maxHeight": "500px", "overflowY": "auto"},
            style_cell={
                "fontSize": "11px",
                "padding": "5px",
                "fontFamily": "Sora",
                "textAlign": "right",
            },
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            style_data_conditional=[
                {"if": {"column_id": "Feature"}, "textAlign": "left"}
            ],
            sort_action="native",
            page_size=50,
        )

    # Frequency — cards + chart + table
    freq_cards_content = []
    fig_freq = _empty_fig("No frequency data")
    freq_table = nd
    if not freq_df.empty:
        fd = freq_df.copy()
        fd["feature"] = fd["event_name"].map(_label)
        fd = fd[fd["event_name"] != "app_opened"]

        # Top 8 frequency cards
        top_freq = fd.head(8)
        freq_card_cols = []
        for _, row in top_freq.iterrows():
            days = row["avg_days_between"]
            bg = GREEN if days <= 3 else (ALPINE if days <= 7 else TANGERINE)
            freq_card_cols.append(
                dbc.Col(
                    _color_card(
                        bg,
                        str(row["feature"])[:25],
                        f"{days:.1f} days",
                        f"{int(row['apps_with_repeat']):,} apps with repeat usage",
                    ),
                    md=3,
                    className="mb-2",
                )
            )
        freq_cards_content = dbc.Row(freq_card_cols)

        chart_data = fd.head(25)
        fig_freq = px.bar(
            chart_data,
            x="avg_days_between",
            y="feature",
            orientation="h",
            color="avg_days_between",
            color_continuous_scale=[GREEN, "#ffccbc"],
            labels={"avg_days_between": "Avg Days Between", "feature": ""},
            title="Avg Days Between Feature Usage (Top 25)",
        )
        fig_freq.update_layout(
            yaxis=dict(autorange="reversed", categoryorder="total ascending"),
            height=600,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        ft = fd[
            ["feature", "avg_days_between", "avg_weeks_between", "apps_with_repeat"]
        ].copy()
        ft.columns = ["Feature", "Avg Days", "Avg Weeks", "Apps w/ Repeat"]
        freq_table = dash_table.DataTable(
            data=ft.to_dict("records"),
            columns=[{"name": c, "id": c} for c in ft.columns],
            style_table={"maxHeight": "600px", "overflowY": "auto"},
            style_cell={
                "fontSize": "11px",
                "padding": "5px",
                "fontFamily": "Sora",
                "textAlign": "right",
            },
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            style_data_conditional=[
                {"if": {"column_id": "Feature"}, "textAlign": "left"}
            ],
            sort_action="native",
            page_size=50,
        )

    # Monthly Trend — events + apps active
    fig_trend = _empty_fig("No trend data")
    fig_trend_apps = _empty_fig()
    if not trend_df.empty:
        tf = trend_df[trend_df["event_name"] != "app_opened"].copy()
        tf["feature"] = tf["event_name"].map(_label)
        top_features = (
            tf.groupby("feature")["event_count"].sum().nlargest(6).index.tolist()
        )
        plot_data = tf[tf["feature"].isin(top_features)]
        fig_trend = px.line(
            plot_data,
            x="month",
            y="event_count",
            color="feature",
            title="Monthly Feature Usage (Top 6)",
            labels={"event_count": "Events", "month": "Month", "feature": "Feature"},
            color_discrete_sequence=CHART_SEQUENCE,
        )
        fig_trend.update_layout(height=450)

        if "apps_active" in tf.columns:
            fig_trend_apps = px.line(
                plot_data,
                x="month",
                y="apps_active",
                color="feature",
                title="Apps Actively Using Feature (Monthly)",
                labels={
                    "apps_active": "Active Apps",
                    "month": "Month",
                    "feature": "Feature",
                },
                color_discrete_sequence=CHART_SEQUENCE,
            )
            fig_trend_apps.update_layout(height=400)

    # Module Adoption — KPI cards + pies + bar + table + trends
    module_kpi_cards = []
    fig_mod_uptake_pie = _empty_fig("No module data")
    fig_mod_bar = _empty_fig()
    fig_mod_events_pie = _empty_fig()
    mod_table_content = nd
    fig_mod_trend = _empty_fig()
    fig_mod_apps_trend = _empty_fig()

    if not module_df.empty and total_coach_apps > 0:
        md_df = module_df.copy()
        md_df["module"] = md_df["entity_name"].map(MODULE_MAP).fillna("Other")
        md_df = md_df[md_df["module"] != "Other"]

        mod_summary = (
            md_df.groupby("module")
            .agg(
                total_events=("event_count", "sum"),
                apps_using=("application_name", "nunique"),
                avg_months=("months_active", "mean"),
            )
            .reset_index()
        )
        mod_summary["uptake_pct"] = (
            mod_summary["apps_using"] / total_coach_apps * 100
        ).round(1)
        mod_summary = mod_summary.sort_values("uptake_pct", ascending=False)

        # Module KPI cards
        mod_card_cols = []
        for _, row in mod_summary.iterrows():
            pct = row["uptake_pct"]
            bg = GREEN if pct >= 40 else (ALPINE if pct >= 20 else TANGERINE)
            mod_card_cols.append(
                dbc.Col(
                    _color_card(
                        bg,
                        row["module"],
                        f"{pct:.1f}%",
                        f"{int(row['apps_using']):,} apps \u00b7 {int(row['total_events']):,} events",
                    ),
                    md=2,
                    className="mb-2",
                )
            )
        module_kpi_cards = dbc.Row(mod_card_cols)

        # Module uptake pie
        fig_mod_uptake_pie = px.pie(
            mod_summary,
            values="apps_using",
            names="module",
            title="Coach Uptake by Module (# of Apps)",
            color_discrete_sequence=CHART_SEQUENCE,
            hole=0.4,
        )
        fig_mod_uptake_pie.update_traces(
            textinfo="label+percent", textposition="outside"
        )
        fig_mod_uptake_pie.update_layout(height=450, showlegend=False)

        # Module bar
        fig_mod_bar = px.bar(
            mod_summary.sort_values("uptake_pct", ascending=True),
            x="uptake_pct",
            y="module",
            orientation="h",
            color="total_events",
            color_continuous_scale=["#e8f5e9", GREEN],
            labels={
                "uptake_pct": "Coach Uptake %",
                "module": "",
                "total_events": "Total Events",
            },
            title="Module Uptake % (of all coach apps)",
            text="uptake_pct",
        )
        fig_mod_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_mod_bar.update_layout(height=450, margin=dict(l=10, r=40, t=40, b=10))

        # Module events pie
        fig_mod_events_pie = px.pie(
            mod_summary,
            values="total_events",
            names="module",
            title="Share of Total Events by Module",
            color_discrete_sequence=CHART_SEQUENCE,
            hole=0.4,
        )
        fig_mod_events_pie.update_traces(
            textinfo="label+percent", textposition="outside"
        )
        fig_mod_events_pie.update_layout(height=400, showlegend=False)

        # Module table
        tbl = mod_summary[
            ["module", "apps_using", "uptake_pct", "total_events", "avg_months"]
        ].copy()
        tbl.columns = [
            "Module",
            "Apps Using",
            "Uptake %",
            "Total Events",
            "Avg Months Active",
        ]
        tbl["Avg Months Active"] = tbl["Avg Months Active"].round(1)
        mod_table_content = dash_table.DataTable(
            data=tbl.to_dict("records"),
            columns=[{"name": c, "id": c} for c in tbl.columns],
            style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
        )

    if not module_trend_df.empty:
        mt = module_trend_df.copy()
        mt["module"] = mt["entity_name"].map(MODULE_MAP).fillna("Other")
        mt = mt[mt["module"] != "Other"]
        mt_agg = (
            mt.groupby(["module", "month"])
            .agg(event_count=("event_count", "sum"), apps_active=("apps_active", "sum"))
            .reset_index()
        )

        fig_mod_trend = px.line(
            mt_agg,
            x="month",
            y="event_count",
            color="module",
            title="Monthly Events by Module",
            labels={"event_count": "Events", "month": "Month", "module": "Module"},
            color_discrete_sequence=CHART_SEQUENCE,
        )
        fig_mod_trend.update_layout(height=450)

        fig_mod_apps_trend = px.line(
            mt_agg,
            x="month",
            y="apps_active",
            color="module",
            title="Monthly Active Apps by Module",
            labels={"apps_active": "Active Apps", "month": "Month", "module": "Module"},
            color_discrete_sequence=CHART_SEQUENCE,
        )
        fig_mod_apps_trend.update_layout(height=400)

    # App filter options
    app_opts = []
    if not per_app_df.empty and "app" in per_app_df.columns:
        app_opts = [
            {"label": n, "value": n}
            for n in sorted(per_app_df["app"].dropna().unique())
        ]

    return (
        kpi,
        fig_top,
        plat_table,
        fig_cat_pie,
        fig_cat_bar,
        cat_table,
        uptake_cards_content,
        fig_uptake_pie,
        fig_uptake,
        uptake_table,
        freq_cards_content,
        fig_freq,
        freq_table,
        fig_trend,
        fig_trend_apps,
        module_kpi_cards,
        fig_mod_uptake_pie,
        fig_mod_bar,
        fig_mod_events_pie,
        mod_table_content,
        fig_mod_trend,
        fig_mod_apps_trend,
        app_opts,
    )


@callback(
    Output("fa-app-kpi-row", "children"),
    Output("fa-app-chart", "figure"),
    Output("fa-app-detail-table", "children"),
    Output("fa-app-cat-chart", "figure"),
    Output("fa-app-vs-platform", "figure"),
    Output("fa-app-vs-table", "children"),
    Input("fa-app-filter", "value"),
)
def update_app_features(selected_app):
    nd = html.P("Select an app to view its feature usage.", style={"color": NEUTRAL})
    e = _empty_fig("Select an app")
    if not selected_app:
        return [], e, nd, e, e, nd

    per_app_df = load_feature_adoption_per_app()
    platform_df = load_feature_adoption_platform()
    if per_app_df.empty or "app" not in per_app_df.columns:
        return [], e, html.P("No data", style={"color": NEUTRAL}), e, e, nd

    app_data = per_app_df[per_app_df["app"] == selected_app].copy()
    if app_data.empty:
        return (
            [],
            e,
            html.P(f"No feature data for {selected_app}", style={"color": NEUTRAL}),
            e,
            e,
            nd,
        )

    app_data["feature"] = app_data["event_name"].map(_label)
    app_data = app_data.sort_values("event_count", ascending=False)

    # KPI cards
    total_app_events = app_data["event_count"].sum()
    features_used = len(app_data)
    top_feature = app_data.iloc[0]["feature"] if not app_data.empty else "N/A"
    top_events = int(app_data.iloc[0]["event_count"]) if not app_data.empty else 0
    avg_months = (
        app_data["months_used"].mean()
        if not app_data.empty and "months_used" in app_data.columns
        else 0
    )

    app_kpi = [
        dbc.Col(
            _color_card(
                GREEN, "Total Events", f"{total_app_events:,.0f}", selected_app
            ),
            md=3,
        ),
        dbc.Col(
            _color_card(
                DARK, "Features Used", f"{features_used:,}", "Distinct feature types"
            ),
            md=3,
        ),
        dbc.Col(
            _color_card(
                TANGERINE,
                "Top Feature",
                str(top_feature)[:20],
                f"{top_events:,} events",
            ),
            md=3,
        ),
        dbc.Col(
            _color_card(
                ALPINE,
                "Avg Feature Lifespan",
                f"{avg_months:.1f} mo",
                "Months per feature",
            ),
            md=3,
        ),
    ]

    # Top 20 features bar chart
    top20 = app_data.head(20)
    fig_app = px.bar(
        top20,
        x="event_count",
        y="feature",
        orientation="h",
        color="months_used" if "months_used" in top20.columns else None,
        color_continuous_scale=["#fff3e0", TANGERINE],
        labels={"event_count": "Events", "feature": "", "months_used": "Months Used"},
        title=f"Top 20 Features \u2014 {selected_app}",
    )
    fig_app.update_layout(
        yaxis=dict(autorange="reversed", categoryorder="total ascending"),
        height=550,
        margin=dict(l=10, r=10, t=40, b=10),
    )

    # Detail table with Events/Month
    detail = app_data[["feature", "event_count"]].copy()
    if "months_used" in app_data.columns:
        detail["months_used"] = app_data["months_used"]
        detail["Events/Month"] = (
            (detail["event_count"] / detail["months_used"].clip(lower=1))
            .round(0)
            .astype(int)
        )
    detail.columns = ["Feature", "Events"] + (
        ["Months Used", "Events/Month"] if "months_used" in app_data.columns else []
    )
    app_detail_table = dash_table.DataTable(
        data=detail.to_dict("records"),
        columns=[{"name": c, "id": c} for c in detail.columns],
        style_table={"maxHeight": "550px", "overflowY": "auto"},
        style_cell={
            "fontSize": "11px",
            "padding": "5px",
            "fontFamily": "Sora",
            "textAlign": "right",
        },
        style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
        style_data_conditional=[{"if": {"column_id": "Feature"}, "textAlign": "left"}],
        sort_action="native",
        page_size=50,
    )

    # Category breakdown for this app
    fig_app_cat = _empty_fig("No category data")
    app_cat_data = []
    for cat, events in FEATURE_CATEGORIES.items():
        cat_rows = app_data[app_data["event_name"].isin(events)]
        if not cat_rows.empty:
            app_cat_data.append(
                {
                    "Category": cat,
                    "Events": int(cat_rows["event_count"].sum()),
                    "Features Used": len(cat_rows),
                    "Top Feature": cat_rows.iloc[0]["feature"],
                }
            )
    if app_cat_data:
        app_cat_df = pd.DataFrame(app_cat_data).sort_values("Events", ascending=False)
        fig_app_cat = px.bar(
            app_cat_df,
            x="Category",
            y="Events",
            color="Category",
            color_discrete_sequence=CHART_SEQUENCE,
            title=f"Events by Category \u2014 {selected_app}",
            text="Events",
        )
        fig_app_cat.update_layout(height=350, showlegend=False)
        fig_app_cat.update_traces(texttemplate="%{text:,.0f}", textposition="outside")

    # App vs Platform Average comparison
    fig_compare = _empty_fig("No comparison data")
    compare_table = nd
    if not platform_df.empty:
        platform_avg = (
            platform_df.set_index("event_name")["total_events"]
            / platform_df.set_index("event_name")["apps_using"]
        )
        compare_rows = []
        for _, row in app_data.head(15).iterrows():
            evt = row["event_name"]
            app_count = row["event_count"]
            plat_avg = platform_avg.get(evt, 0)
            if plat_avg > 0:
                compare_rows.append(
                    {
                        "Feature": row["feature"],
                        "App Events": int(app_count),
                        "Platform Avg": round(plat_avg),
                        "vs Avg": f"{(app_count / plat_avg - 1) * 100:+.0f}%",
                    }
                )
        if compare_rows:
            compare_df = pd.DataFrame(compare_rows)
            fig_compare = go.Figure()
            fig_compare.add_trace(
                go.Bar(
                    name=selected_app,
                    x=compare_df["Feature"],
                    y=compare_df["App Events"],
                    marker_color=GREEN,
                )
            )
            fig_compare.add_trace(
                go.Bar(
                    name="Platform Average",
                    x=compare_df["Feature"],
                    y=compare_df["Platform Avg"],
                    marker_color=NEUTRAL,
                )
            )
            fig_compare.update_layout(
                barmode="group",
                title=f"{selected_app} vs Platform Average (Top 15 Features)",
                height=400,
                xaxis_tickangle=-45,
            )
            compare_table = dash_table.DataTable(
                data=compare_df.to_dict("records"),
                columns=[{"name": c, "id": c} for c in compare_df.columns],
                style_cell={"fontSize": "12px", "padding": "6px", "fontFamily": "Sora"},
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            )

    return (app_kpi, fig_app, app_detail_table, fig_app_cat, fig_compare, compare_table)
