"""
Page 8 — Leads & Sales
Weekly time series of acquisition, conversion, revenue, churn, demo calls,
Meta Ads, and TikTok Ads performance.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kliq_ui import (
    GREEN,
    DARK,
    TANGERINE,
    LIME,
    ALPINE,
    ERROR,
    NEUTRAL,
    metric_card,
    section_header,
    chart_card,
    card_wrapper,
)
from data import (
    load_leads_sales,
    load_demo_calls,
    load_meta_ads,
    load_tiktok_ads,
    load_revenue_split,
)

dash.register_page(
    __name__, path="/leads-sales", name="Leads & Sales", title="Leads & Sales — KLIQ"
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
            "Leads & Sales",
            style={"fontSize": "20px", "fontWeight": "700", "color": DARK},
        ),
        html.P(
            "Weekly time series — replaces the manual tracking spreadsheet",
            style={"color": NEUTRAL, "fontSize": "13px"},
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Quick Select",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dbc.RadioItems(
                            id="ls-time",
                            options=[
                                {"label": "30 d", "value": 30},
                                {"label": "60 d", "value": 60},
                                {"label": "90 d", "value": 90},
                                {"label": "6 mo", "value": 180},
                                {"label": "1 yr", "value": 365},
                                {"label": "All", "value": 99999},
                            ],
                            value=30,
                            inline=True,
                        ),
                    ],
                    md=5,
                ),
                dbc.Col(
                    [
                        dbc.Label(
                            "Custom Date Range",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dcc.DatePickerRange(
                            id="ls-date-picker",
                            min_date_allowed=date(2022, 1, 1),
                            max_date_allowed=date.today() + timedelta(days=7),
                            start_date=None,
                            end_date=None,
                            display_format="DD/MM/YYYY",
                            clearable=True,
                            style={"fontSize": "12px"},
                            start_date_placeholder_text="Start date",
                            end_date_placeholder_text="End date",
                        ),
                        html.Div(
                            id="ls-date-status",
                            style={
                                "fontSize": "11px",
                                "marginTop": "4px",
                                "color": NEUTRAL,
                            },
                        ),
                    ],
                    md=5,
                ),
            ],
            className="mb-4",
        ),
        # Period KPIs (aggregated over selected range)
        section_header("📊 Period Summary"),
        dbc.Row(id="ls-kpi-row1", className="mb-2"),
        dbc.Row(id="ls-kpi-row2", className="mb-3"),
        html.Hr(),
        # Acquisition Funnel
        section_header("🔄 Weekly Acquisition Funnel"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="ls-funnel")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="ls-conversion")), md=6),
            ]
        ),
        html.Hr(),
        # Revenue & Cancellations
        section_header("💰 Revenue & Paying Customers"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="ls-revenue")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="ls-cancellations")), md=6),
            ]
        ),
        html.Hr(),
        # Net Growth
        section_header("📉 Churn & Net Growth"),
        chart_card(dcc.Graph(id="ls-net-new")),
        html.Hr(),
        # Platform Health
        section_header("👥 Platform Health"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="ls-active-users")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="ls-free-accounts")), md=6),
            ]
        ),
        html.Hr(),
        # Demo Calls
        section_header("📞 Demo Calls"),
        dbc.Row(
            [
                dbc.Col(chart_card(dcc.Graph(id="ls-demos")), md=6),
                dbc.Col(chart_card(dcc.Graph(id="ls-demo-conv")), md=6),
            ]
        ),
        html.Hr(),
        # Meta Ads
        section_header("📣 Meta Ads Performance"),
        dbc.Row(id="ls-meta-kpi", className="mb-3"),
        card_wrapper(html.Div(id="ls-meta-table")),
        html.Hr(),
        # TikTok Ads
        section_header("🎵 TikTok Ads Performance"),
        dbc.Row(id="ls-tt-kpi", className="mb-3"),
        card_wrapper(html.Div(id="ls-tt-table")),
        html.Hr(),
        # Full Data Table
        section_header("📋 Weekly Data Table"),
        card_wrapper(html.Div(id="ls-full-table")),
    ]
)


@callback(
    Output("ls-kpi-row1", "children"),
    Output("ls-kpi-row2", "children"),
    Output("ls-funnel", "figure"),
    Output("ls-conversion", "figure"),
    Output("ls-revenue", "figure"),
    Output("ls-cancellations", "figure"),
    Output("ls-net-new", "figure"),
    Output("ls-active-users", "figure"),
    Output("ls-free-accounts", "figure"),
    Output("ls-demos", "figure"),
    Output("ls-demo-conv", "figure"),
    Output("ls-meta-kpi", "children"),
    Output("ls-meta-table", "children"),
    Output("ls-tt-kpi", "children"),
    Output("ls-tt-table", "children"),
    Output("ls-full-table", "children"),
    Output("ls-date-status", "children"),
    Input("ls-time", "value"),
    Input("ls-date-picker", "start_date"),
    Input("ls-date-picker", "end_date"),
)
def update_leads_sales(time_days, pick_start, pick_end):
    # ── Date picker always wins if both dates are filled ──
    use_picker = bool(pick_start and pick_end)
    print(
        f"[leads_sales] Inputs: time_days={time_days}, pick_start={pick_start}, pick_end={pick_end}, use_picker={use_picker}"
    )

    # ── Load all data sources with logging ──
    df = load_leads_sales()
    if df.empty:
        print("[leads_sales] WARNING: load_leads_sales() returned empty")
        e = _empty_fig("No data — run refresh script first")
        nd = html.P("No data", style={"color": NEUTRAL})
        return [], [], e, e, e, e, e, e, e, e, e, [], nd, [], nd, nd, ""

    df["week_start"] = pd.to_datetime(df["week_start"])
    print(
        f"[leads_sales] Loaded {len(df)} weeks, range {df['week_start'].min().date()} → {df['week_start'].max().date()}"
    )

    # Merge demo calls
    try:
        demo_df = load_demo_calls()
        if not demo_df.empty:
            demo_df["week_start"] = pd.to_datetime(demo_df["week_start"])
            df = df.merge(demo_df, on="week_start", how="left")
            df["demo_calls"] = df["demo_calls"].fillna(0).astype(int)
    except Exception as _e:
        print(f"[leads_sales] Demo calls merge error: {_e}")

    # Merge Meta ads
    try:
        meta_df = load_meta_ads()
        if not meta_df.empty:
            meta_df["week_start"] = pd.to_datetime(meta_df["week_start"])
            df = df.merge(meta_df, on="week_start", how="left")
            for c in [
                "meta_spend",
                "meta_impressions",
                "meta_clicks",
                "meta_link_clicks",
                "meta_landing_page_views",
                "meta_leads",
                "meta_video_views",
                "meta_post_reactions",
            ]:
                if c in df.columns:
                    df[c] = df[c].fillna(0)
            print(
                f"[leads_sales] Meta ads merged — {meta_df.shape[0]} weeks, total leads: {df['meta_leads'].sum() if 'meta_leads' in df.columns else 0}"
            )
        else:
            print("[leads_sales] WARNING: load_meta_ads() returned empty")
    except Exception as _e:
        print(f"[leads_sales] Meta ads merge error: {_e}")

    # Merge TikTok ads
    try:
        tiktok_df = load_tiktok_ads()
        if not tiktok_df.empty:
            tiktok_df["week_start"] = pd.to_datetime(tiktok_df["week_start"])
            df = df.merge(tiktok_df, on="week_start", how="left")
            for c in [
                "tt_spend",
                "tt_impressions",
                "tt_clicks",
                "tt_conversions",
                "tt_reach",
                "tt_cpc",
                "tt_cpm",
                "tt_ctr",
                "tt_cost_per_conversion",
                "tt_video_views_100",
            ]:
                if c in df.columns:
                    df[c] = df[c].fillna(0)
    except Exception as _e:
        print(f"[leads_sales] TikTok ads merge error: {_e}")

    # Merge revenue split (new sales vs recurring)
    try:
        rev_df = load_revenue_split()
        if not rev_df.empty:
            rev_df["week_start"] = pd.to_datetime(rev_df["week_start"])
            df = df.merge(rev_df, on="week_start", how="left")
            for c in [
                "new_sales_revenue",
                "recurring_revenue",
                "new_hosting_signups",
                "new_app_signups",
                "renewal_invoices",
            ]:
                if c in df.columns:
                    df[c] = df[c].fillna(0)
            print(
                f"[leads_sales] Revenue split merged — new sales total: ${df['new_sales_revenue'].sum():.2f}, recurring: ${df['recurring_revenue'].sum():.2f}"
            )
        else:
            print("[leads_sales] WARNING: load_revenue_split() returned empty")
    except Exception as _e:
        print(f"[leads_sales] Revenue split merge error: {_e}")

    # ── Date filter: use picker if it triggered, otherwise radio ──
    if use_picker and pick_start and pick_end:
        start = pd.Timestamp(pick_start)
        end = pd.Timestamp(pick_end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df = df[(df["week_start"] >= start) & (df["week_start"] <= end)]
        print(
            f"[leads_sales] Custom date range: {start.date()} → {end.date()}, {len(df)} weeks matched"
        )
    else:
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=time_days)
        df = df[df["week_start"] >= cutoff]
        print(
            f"[leads_sales] Quick select: {time_days}d, cutoff={cutoff.date()}, {len(df)} weeks matched"
        )

    if use_picker:
        date_msg = html.Span(
            f"Showing {pick_start} → {pick_end}",
            style={"color": GREEN, "fontWeight": "600", "fontSize": "11px"},
        )
    else:
        date_msg = ""

    if df.empty:
        e = _empty_fig("No data for selected period")
        nd = html.P("No data", style={"color": NEUTRAL})
        return [], [], e, e, e, e, e, e, e, e, e, [], nd, [], nd, nd, date_msg

    # ── Period-aggregated KPIs (sum over ALL weeks in range) ──
    def col_sum(col):
        return int(df[col].sum()) if col in df.columns else 0

    def col_sumf(col):
        return float(df[col].sum()) if col in df.columns else 0.0

    weeks_in_range = len(df)
    leads = col_sum("meta_leads")
    apps = col_sum("applications_created")
    cards = col_sum("card_details")
    trialers = col_sum("new_trialers")
    customers = col_sum("new_customers")
    registrations = col_sum("new_registrations")
    new_sales_rev = col_sumf("new_sales_revenue")  # hosting fee from first payment
    recurring_rev = col_sumf("recurring_revenue")  # Stripe app-fee renewals
    new_hosting = col_sum("new_hosting_signups")  # apps that paid hosting first time
    new_app_signups = col_sum("new_app_signups")  # all new app creations
    cancels = col_sum("cancellations")
    demos = col_sum("demo_calls")
    spend = col_sumf("meta_spend")
    link_clicks = col_sumf("meta_link_clicks")

    card_conv = (cards / apps * 100) if apps > 0 else 0
    cpc = spend / link_clicks if link_clicks > 0 else 0
    cpl = spend / leads if leads > 0 else 0
    lead_to_app = (apps / leads * 100) if leads > 0 else 0

    # Latest active users (snapshot, not sum)
    latest_au = (
        int(df["active_users"].iloc[-1])
        if "active_users" in df.columns and not df["active_users"].empty
        else 0
    )
    latest_paying = (
        int(df["total_paying_customers"].iloc[-1])
        if "total_paying_customers" in df.columns
        and not df["total_paying_customers"].empty
        else 0
    )

    period_label = f"{weeks_in_range}w"

    kpi1 = [
        dbc.Col(metric_card("Meta Leads", f"{leads:,}", period_label), md=2),
        dbc.Col(metric_card("Apps Created", f"{apps:,}", period_label), md=2),
        dbc.Col(
            metric_card("New Registrations", f"{registrations:,}", period_label), md=2
        ),
        dbc.Col(
            metric_card("Card Details", f"{cards:,}", f"Conv: {card_conv:.1f}%"), md=2
        ),
        dbc.Col(metric_card("New Trialers", f"{trialers:,}", period_label), md=2),
        dbc.Col(metric_card("New Customers", f"{customers:,}", period_label), md=2),
    ]

    kpi2 = [
        dbc.Col(
            metric_card(
                "New Hosting Rev", f"${new_sales_rev:,.0f}", f"{new_hosting} new paying"
            ),
            md=2,
        ),
        dbc.Col(
            metric_card("Recurring Rev", f"${recurring_rev:,.0f}", "app fees"), md=2
        ),
        dbc.Col(metric_card("Cancellations", f"{cancels:,}", period_label), md=2),
        dbc.Col(metric_card("Meta Spend", f"${spend:,.0f}", f"CPC: ${cpc:,.2f}"), md=2),
        dbc.Col(metric_card("Cost/Lead", f"${cpl:,.2f}", f"{leads} leads"), md=2),
        dbc.Col(
            metric_card(
                "Lead\u2192App %", f"{lead_to_app:.1f}%", f"{leads}\u2192{apps}"
            ),
            md=2,
        ),
    ]

    # Funnel Chart
    fig_funnel = go.Figure()
    for col, label, color in [
        ("applications_created", "Apps Created", GREEN),
        ("card_details", "Card Details", TANGERINE),
        ("new_trialers", "New Trialers", LIME),
        ("new_customers", "New Customers", ALPINE),
    ]:
        if col in df.columns:
            fig_funnel.add_trace(
                go.Scatter(
                    x=df["week_start"],
                    y=df[col],
                    name=label,
                    mode="lines+markers",
                    marker=dict(size=4),
                    line=dict(color=color),
                )
            )
    fig_funnel.update_layout(
        height=400,
        title="Acquisition Pipeline",
        xaxis_title="Week",
        yaxis_title="Count",
    )

    # Conversion Chart
    fig_conv = go.Figure()
    if "card_conversion_pct" in df.columns:
        fig_conv.add_trace(
            go.Scatter(
                x=df["week_start"],
                y=df["card_conversion_pct"],
                name="Card Conversion %",
                mode="lines+markers",
                line=dict(color=TANGERINE),
            )
        )
    if "self_serve_conversion_pct" in df.columns:
        fig_conv.add_trace(
            go.Scatter(
                x=df["week_start"],
                y=df["self_serve_conversion_pct"],
                name="Self-Serve Conv %",
                mode="lines+markers",
                line=dict(color=GREEN),
            )
        )
    fig_conv.update_layout(
        height=400, title="Conversion Rates (%)", xaxis_title="Week", yaxis_title="%"
    )

    # Revenue — stacked bar: new hosting sales vs recurring app fees
    fig_rev = _empty_fig("No revenue data")
    if "new_sales_revenue" in df.columns and "recurring_revenue" in df.columns:
        fig_rev = go.Figure()
        fig_rev.add_trace(
            go.Bar(
                x=df["week_start"],
                y=df["new_sales_revenue"],
                name="New Hosting Fees",
                marker_color=GREEN,
            )
        )
        fig_rev.add_trace(
            go.Bar(
                x=df["week_start"],
                y=df["recurring_revenue"],
                name="Recurring App Fees",
                marker_color=TANGERINE,
            )
        )
        fig_rev.update_layout(
            barmode="stack",
            height=400,
            title="Weekly KLIQ Revenue — New Hosting vs Recurring App Fees ($)",
            xaxis_title="Week",
            yaxis_title="Revenue ($)",
        )
    elif "sales_revenue_usd" in df.columns:
        fig_rev = px.bar(
            df,
            x="week_start",
            y="sales_revenue_usd",
            title="Weekly Revenue ($)",
            color_discrete_sequence=[GREEN],
        )
        fig_rev.update_layout(height=400)

    # Cancellations
    fig_cancel = _empty_fig("No cancellation data")
    if "cancellations" in df.columns:
        fig_cancel = px.bar(
            df,
            x="week_start",
            y="cancellations",
            title="Weekly Cancellations",
            color_discrete_sequence=[ERROR],
        )
        fig_cancel.update_layout(height=400)

    # Net New
    fig_net = _empty_fig()
    if "cancellations" in df.columns and "new_trialers" in df.columns:
        net = df.copy()
        net["net_new"] = net["new_trialers"] - net["cancellations"]
        fig_net = px.bar(
            net,
            x="week_start",
            y="net_new",
            title="Net New (Trialers − Cancellations)",
            color_discrete_sequence=[ALPINE],
        )
        fig_net.update_layout(height=400)

    # Active Users
    fig_au = _empty_fig("No active user data")
    if "active_users" in df.columns:
        fig_au = px.line(
            df,
            x="week_start",
            y="active_users",
            title="Weekly Active Users",
            markers=True,
            color_discrete_sequence=[GREEN],
        )
        fig_au.update_layout(height=400)

    # Free Accounts
    fig_fa = _empty_fig("No free account data")
    if "free_accounts" in df.columns:
        fig_fa = px.line(
            df,
            x="week_start",
            y="free_accounts",
            title="Cumulative Free Accounts",
            markers=True,
            color_discrete_sequence=[TANGERINE],
        )
        fig_fa.update_layout(height=400)

    # Demo Calls
    fig_demo = _empty_fig("No demo data")
    fig_dc = _empty_fig()
    if "demo_calls" in df.columns and df["demo_calls"].sum() > 0:
        fig_demo = px.bar(
            df,
            x="week_start",
            y="demo_calls",
            title="Weekly Demo Calls",
            color_discrete_sequence=[TANGERINE],
        )
        fig_demo.update_layout(height=400)
        if "new_customers" in df.columns:
            dc = df.copy()
            dc["demo_conv_pct"] = (
                (dc["new_customers"] / dc["demo_calls"].replace(0, float("nan")) * 100)
                .round(1)
                .fillna(0)
            )
            fig_dc = px.line(
                dc,
                x="week_start",
                y="demo_conv_pct",
                title="Demo → Customer Conversion %",
                markers=True,
                color_discrete_sequence=[GREEN],
            )
            fig_dc.update_layout(height=400)

    # Meta Ads KPIs + Table
    meta_kpi = []
    meta_table = html.P("No Meta Ads data yet.", style={"color": NEUTRAL})
    if "meta_spend" in df.columns and df["meta_spend"].sum() > 0:
        ts = df["meta_spend"].sum()
        tlc = df["meta_link_clicks"].sum() if "meta_link_clicks" in df.columns else 0
        ti = df["meta_impressions"].sum() if "meta_impressions" in df.columns else 0
        tl = df["meta_leads"].sum() if "meta_leads" in df.columns else 0
        acpc = ts / tlc if tlc > 0 else 0
        actr = (tlc / ti * 100) if ti > 0 else 0
        cpl_all = ts / tl if tl > 0 else 0
        meta_kpi = [
            dbc.Col(metric_card("Total Spend", f"${ts:,.0f}"), md=2),
            dbc.Col(metric_card("Leads", f"{int(tl):,}"), md=2),
            dbc.Col(metric_card("Cost/Lead", f"${cpl_all:,.2f}"), md=2),
            dbc.Col(metric_card("Link Clicks", f"{int(tlc):,}"), md=2),
            dbc.Col(metric_card("Avg CPC", f"${acpc:,.2f}"), md=2),
            dbc.Col(metric_card("CTR", f"{actr:.2f}%"), md=2),
        ]
        mt = df[["week_start"]].copy()
        mt["week_start"] = mt["week_start"].dt.strftime("%d/%m/%Y")
        for src, tgt in [
            ("meta_spend", "Spend"),
            ("meta_leads", "Leads"),
            ("meta_impressions", "Impressions"),
            ("meta_link_clicks", "Link Clicks"),
            ("meta_landing_page_views", "LPV"),
        ]:
            if src in df.columns:
                mt[tgt] = df[src].values
        mt = mt.rename(columns={"week_start": "Week"}).iloc[::-1].reset_index(drop=True)
        meta_table = dash_table.DataTable(
            data=mt.to_dict("records"),
            columns=[{"name": c, "id": c} for c in mt.columns],
            style_cell={
                "fontSize": "12px",
                "padding": "6px",
                "fontFamily": "Sora",
                "textAlign": "right",
            },
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            style_data_conditional=[{"if": {"column_id": "Week"}, "textAlign": "left"}],
            page_size=20,
        )

    # TikTok Ads KPIs + Table
    tt_kpi = []
    tt_table = html.P("No TikTok Ads data yet.", style={"color": NEUTRAL})
    if "tt_spend" in df.columns and df["tt_spend"].sum() > 0:
        tts = df["tt_spend"].sum()
        ttc = df["tt_clicks"].sum() if "tt_clicks" in df.columns else 0
        tti = df["tt_impressions"].sum() if "tt_impressions" in df.columns else 0
        ttconv = df["tt_conversions"].sum() if "tt_conversions" in df.columns else 0
        ttcpc = tts / ttc if ttc > 0 else 0
        ttctr = (ttc / tti * 100) if tti > 0 else 0
        ttcpconv = tts / ttconv if ttconv > 0 else 0
        tt_kpi = [
            dbc.Col(metric_card("Total Spend", f"${tts:,.0f}"), md=2),
            dbc.Col(metric_card("Conversions", f"{int(ttconv):,}"), md=2),
            dbc.Col(metric_card("Cost/Conv", f"${ttcpconv:,.2f}"), md=2),
            dbc.Col(metric_card("Clicks", f"{int(ttc):,}"), md=2),
            dbc.Col(metric_card("Avg CPC", f"${ttcpc:,.2f}"), md=2),
            dbc.Col(metric_card("CTR", f"{ttctr:.2f}%"), md=2),
        ]
        tt = df[["week_start"]].copy()
        tt["week_start"] = tt["week_start"].dt.strftime("%d/%m/%Y")
        for src, tgt in [
            ("tt_spend", "Spend"),
            ("tt_conversions", "Conversions"),
            ("tt_impressions", "Impressions"),
            ("tt_clicks", "Clicks"),
        ]:
            if src in df.columns:
                tt[tgt] = df[src].values
        tt = tt.rename(columns={"week_start": "Week"}).iloc[::-1].reset_index(drop=True)
        tt_table = dash_table.DataTable(
            data=tt.to_dict("records"),
            columns=[{"name": c, "id": c} for c in tt.columns],
            style_cell={
                "fontSize": "12px",
                "padding": "6px",
                "fontFamily": "Sora",
                "textAlign": "right",
            },
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            style_data_conditional=[{"if": {"column_id": "Week"}, "textAlign": "left"}],
            page_size=20,
        )

    # Full Data Table
    disp = df.copy()
    disp["week_start"] = disp["week_start"].dt.strftime("%d/%m/%Y")
    rename_map = {
        "week_start": "Week",
        "applications_created": "Apps Created",
        "card_details": "Card Details",
        "card_conversion_pct": "Card Conv %",
        "new_trialers": "New Trialers",
        "new_customers": "New Customers",
        "sales_revenue_usd": "Sales ($)",
        "cancellations": "Cancellations",
        "active_users": "Active Users",
        "free_accounts": "Free Accounts",
        "demo_calls": "Demo Calls",
    }
    avail_renames = {k: v for k, v in rename_map.items() if k in disp.columns}
    disp = disp.rename(columns=avail_renames).iloc[::-1].reset_index(drop=True)
    full_table = dash_table.DataTable(
        data=disp.to_dict("records"),
        columns=[{"name": c, "id": c} for c in disp.columns],
        style_table={"overflowX": "auto"},
        style_cell={
            "fontSize": "11px",
            "padding": "5px",
            "fontFamily": "Sora",
            "textAlign": "right",
        },
        style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
        style_data_conditional=[{"if": {"column_id": "Week"}, "textAlign": "left"}],
        sort_action="native",
        filter_action="native",
        page_size=30,
    )

    return (
        kpi1,
        kpi2,
        fig_funnel,
        fig_conv,
        fig_rev,
        fig_cancel,
        fig_net,
        fig_au,
        fig_fa,
        fig_demo,
        fig_dc,
        meta_kpi,
        meta_table,
        tt_kpi,
        tt_table,
        full_table,
        date_msg,
    )
