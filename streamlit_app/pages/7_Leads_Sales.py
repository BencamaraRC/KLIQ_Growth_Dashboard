"""
Leads & Sales — Weekly time series of acquisition, conversion, revenue, and churn metrics.
Mirrors the manual tracking spreadsheet with live BigQuery data.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data import load_leads_sales, load_demo_calls, load_meta_ads, load_tiktok_ads
from kliq_ui_kit import (
    inject_css,
    register_plotly_template,
    GREEN,
    DARK,
    IVORY,
    TANGERINE,
    LIME,
    ALPINE,
    ERROR,
    NEUTRAL,
    CHART_SEQUENCE,
)

st.set_page_config(page_title="Leads & Sales", layout="wide")
inject_css()
register_plotly_template()

st.title("Leads & Sales")
st.caption("Weekly time series — replaces the manual tracking spreadsheet")

# ── Load Data ──
with st.spinner("Loading leads & sales data..."):
    df = load_leads_sales()
    try:
        demo_df = load_demo_calls()
    except Exception:
        demo_df = pd.DataFrame()
    try:
        meta_df = load_meta_ads()
    except Exception:
        meta_df = pd.DataFrame()
    try:
        tiktok_df = load_tiktok_ads()
    except Exception:
        tiktok_df = pd.DataFrame()

if df.empty:
    st.warning("No leads & sales data available. Run the refresh script first.")
    st.stop()

df["week_start"] = pd.to_datetime(df["week_start"])

# Merge demo calls
if not demo_df.empty:
    demo_df["week_start"] = pd.to_datetime(demo_df["week_start"])
    df = df.merge(demo_df, on="week_start", how="left")
    df["demo_calls"] = df["demo_calls"].fillna(0).astype(int)

# Merge Meta ads
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

# Merge TikTok ads
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
        "tt_video_views_25",
        "tt_video_views_50",
        "tt_video_views_75",
        "tt_video_views_100",
    ]:
        if c in df.columns:
            df[c] = df[c].fillna(0)

# ── Sidebar Filters ──
st.sidebar.header("Filters")

time_filter = st.sidebar.radio(
    "Time Period",
    [
        "Last 7 days",
        "Last 14 days",
        "Last 30 days",
        "Last 60 days",
        "Last 90 days",
        "All Time",
    ],
    index=2,
    key="ls_time",
)
time_days = {
    "Last 7 days": 7,
    "Last 14 days": 14,
    "Last 30 days": 30,
    "Last 60 days": 60,
    "Last 90 days": 90,
    "All Time": 99999,
}[time_filter]

cutoff = pd.Timestamp.now() - pd.Timedelta(days=time_days)
df = df[df["week_start"] >= cutoff]


# ── Helper ──
def safe_col(col):
    return col if col in df.columns else None


def fmt_pct(val):
    return f"{val:.1f}%" if pd.notna(val) else "—"


# ── KPI Cards (Current Week Snapshot: Mon–Sun) ──
today = pd.Timestamp.now()
current_monday = today - pd.Timedelta(days=today.weekday())
current_sunday = current_monday + pd.Timedelta(days=6)
current_week = df[df["week_start"] == current_monday.normalize()]

# Fall back to the most recent week if current week has no data yet
if current_week.empty and len(df) > 0:
    current_week = df.iloc[[-1]]
    current_monday = current_week["week_start"].iloc[0]
    current_sunday = current_monday + pd.Timedelta(days=6)

if not current_week.empty:
    cw = current_week.iloc[0]
    mon_str = current_monday.strftime("%d %b")
    sun_str = current_sunday.strftime("%d %b %Y")
    st.subheader(f"📊 This Week — {mon_str} to {sun_str}")

    def cw_val(col):
        return cw.get(col, 0) if col in current_week.columns else 0

    leads = int(cw_val("meta_leads"))
    apps = int(cw_val("applications_created"))
    cards = int(cw_val("card_details"))
    trialers = int(cw_val("new_trialers"))
    customers = int(cw_val("new_customers"))
    revenue = cw_val("sales_revenue_usd")
    card_conv = (cards / apps * 100) if apps > 0 else 0

    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    k1.metric("Meta Leads", f"{leads:,}")
    k2.metric("Apps Created", f"{apps:,}")
    k3.metric("Card Details", f"{cards:,}")
    k4.metric("Card Conversion", f"{card_conv:.1f}%")
    k5.metric("New Trialers", f"{trialers:,}")
    k6.metric("New Customers", f"{customers:,}")
    k7.metric("Sales Revenue", f"${revenue:,.0f}")

    # Second row
    demos = int(cw_val("demo_calls"))
    cancels = int(cw_val("cancellations"))
    spend = cw_val("meta_spend")
    link_clicks = cw_val("meta_link_clicks")
    cpc = spend / link_clicks if link_clicks > 0 else 0
    cpl = spend / leads if leads > 0 else 0

    r1, r2, r3, r4, r5 = st.columns(5)
    r1.metric("Demo Calls", f"{demos:,}")
    r2.metric("Cancellations", f"{cancels:,}", delta_color="inverse")
    if "meta_spend" in df.columns:
        r3.metric("Meta Ad Spend", f"${spend:,.0f}")
        r4.metric("CPC (Meta)", f"${cpc:,.2f}")
        r5.metric("Cost per Lead", f"${cpl:,.2f}")
    else:
        r3.metric("Meta Ad Spend", "—")
        r4.metric("CPC", "—")
        r5.metric("Cost per Lead", "—")

st.markdown("---")

# ── Acquisition Funnel (Weekly) ──
st.subheader("🔄 Weekly Acquisition Funnel")

col1, col2 = st.columns(2)

with col1:
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
    st.plotly_chart(fig_funnel, use_container_width=True)

with col2:
    fig_conv = go.Figure()
    if "card_conversion_pct" in df.columns:
        fig_conv.add_trace(
            go.Scatter(
                x=df["week_start"],
                y=df["card_conversion_pct"],
                name="Card Conversion %",
                mode="lines+markers",
                marker=dict(size=4),
                line=dict(color=TANGERINE),
            )
        )
    if "self_serve_conversion_pct" in df.columns:
        fig_conv.add_trace(
            go.Scatter(
                x=df["week_start"],
                y=df["self_serve_conversion_pct"],
                name="Self-Serve Conversion %",
                mode="lines+markers",
                marker=dict(size=4),
                line=dict(color=GREEN),
            )
        )
    fig_conv.update_layout(
        height=400,
        title="Conversion Rates (%)",
        xaxis_title="Week",
        yaxis_title="%",
    )
    st.plotly_chart(fig_conv, use_container_width=True)

st.markdown("---")

# ── Revenue & Customers ──
st.subheader("💰 Revenue & Paying Customers")

col1, col2 = st.columns(2)

with col1:
    if "sales_revenue_usd" in df.columns:
        fig_rev = px.bar(
            df,
            x="week_start",
            y="sales_revenue_usd",
            title="Weekly Sales Revenue ($)",
            labels={"week_start": "Week", "sales_revenue_usd": "Revenue ($)"},
            color_discrete_sequence=[GREEN],
        )
        fig_rev.update_layout(height=400, yaxis=dict(automargin=True))
        st.plotly_chart(fig_rev, use_container_width=True, key="chart_revenue")

with col2:
    if "cancellations" in df.columns:
        fig_cancel = px.bar(
            df,
            x="week_start",
            y="cancellations",
            title="Weekly Cancellations",
            labels={"week_start": "Week", "cancellations": "Cancellations"},
            color_discrete_sequence=[ERROR],
        )
        fig_cancel.update_layout(height=400)
        st.plotly_chart(fig_cancel, use_container_width=True, key="chart_cancellations")

st.markdown("---")

# ── Churn: Net New ──
st.subheader("📉 Churn & Net Growth")

col1, col2 = st.columns(2)
with col1:
    if "cancellations" in df.columns and "new_trialers" in df.columns:
        net = df.copy()
        net["net_new"] = net["new_trialers"] - net["cancellations"]
        fig_net = px.bar(
            net,
            x="week_start",
            y="net_new",
            title="Net New (Trialers − Cancellations)",
            labels={"week_start": "Week", "net_new": "Net New"},
            color_discrete_sequence=[ALPINE],
        )
        fig_net.update_layout(height=400)
        st.plotly_chart(fig_net, use_container_width=True, key="chart_net_new")

st.markdown("---")

# ── Platform Health: Active Users & Free Accounts ──
st.subheader("👥 Platform Health")

col1, col2 = st.columns(2)

with col1:
    if "active_users" in df.columns:
        fig_au = px.line(
            df,
            x="week_start",
            y="active_users",
            title="Weekly Active Users",
            markers=True,
            labels={"week_start": "Week", "active_users": "Active Users"},
            color_discrete_sequence=[GREEN],
        )
        fig_au.update_layout(height=400)
        st.plotly_chart(fig_au, use_container_width=True)

with col2:
    if "free_accounts" in df.columns:
        fig_fa = px.line(
            df,
            x="week_start",
            y="free_accounts",
            title="Cumulative Free Accounts",
            markers=True,
            labels={"week_start": "Week", "free_accounts": "Free Accounts"},
            color_discrete_sequence=[TANGERINE],
        )
        fig_fa.update_layout(height=400)
        st.plotly_chart(fig_fa, use_container_width=True)

st.markdown("---")

# ── Demo Calls ──
st.subheader("📞 Demo Calls (Google Calendar)")

if "demo_calls" in df.columns and df["demo_calls"].sum() > 0:
    col1, col2 = st.columns(2)
    with col1:
        fig_demo = px.bar(
            df,
            x="week_start",
            y="demo_calls",
            title="Weekly Demo Calls Booked",
            labels={"week_start": "Week", "demo_calls": "Demo Calls"},
            color_discrete_sequence=[TANGERINE],
        )
        fig_demo.update_layout(height=400)
        st.plotly_chart(fig_demo, use_container_width=True)

    with col2:
        if "new_customers" in df.columns:
            demo_conv = df.copy()
            demo_conv["demo_conversion_pct"] = (
                (
                    demo_conv["new_customers"]
                    / demo_conv["demo_calls"].replace(0, float("nan"))
                    * 100
                )
                .round(1)
                .fillna(0)
            )
            fig_dc = px.line(
                demo_conv,
                x="week_start",
                y="demo_conversion_pct",
                title="Demo → Customer Conversion %",
                markers=True,
                labels={"week_start": "Week", "demo_conversion_pct": "Conversion %"},
                color_discrete_sequence=[GREEN],
            )
            fig_dc.update_layout(height=400)
            st.plotly_chart(fig_dc, use_container_width=True)
else:
    st.info(
        "No demo call data yet. Share your Google Calendar with the service account to enable this."
    )

st.markdown("---")

# ── Meta Ads ──
st.subheader("📣 Meta Ads Performance")

if "meta_spend" in df.columns and df["meta_spend"].sum() > 0:
    # All-time summary cards
    total_spend = df["meta_spend"].sum()
    total_link_clicks = (
        df["meta_link_clicks"].sum() if "meta_link_clicks" in df.columns else 0
    )
    total_impressions = (
        df["meta_impressions"].sum() if "meta_impressions" in df.columns else 0
    )
    total_leads = df["meta_leads"].sum() if "meta_leads" in df.columns else 0
    total_lpv = (
        df["meta_landing_page_views"].sum()
        if "meta_landing_page_views" in df.columns
        else 0
    )
    total_video_views = (
        df["meta_video_views"].sum() if "meta_video_views" in df.columns else 0
    )
    total_reactions = (
        df["meta_post_reactions"].sum() if "meta_post_reactions" in df.columns else 0
    )
    avg_cpc = total_spend / total_link_clicks if total_link_clicks > 0 else 0
    avg_ctr = (
        (total_link_clicks / total_impressions * 100) if total_impressions > 0 else 0
    )
    cost_per_lead = total_spend / total_leads if total_leads > 0 else 0

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Spend", f"${total_spend:,.0f}")
    m2.metric("Leads (Form)", f"{int(total_leads):,}")
    m3.metric("Cost per Lead", f"${cost_per_lead:,.2f}")
    m4.metric("Link Clicks", f"{int(total_link_clicks):,}")
    m5.metric("Avg CPC", f"${avg_cpc:,.2f}")
    m6.metric("CTR", f"{avg_ctr:.2f}%")

    m7, m8, m9, m10, m11, m12 = st.columns(6)
    m7.metric("Impressions", f"{int(total_impressions):,}")
    m8.metric("Landing Page Views", f"{int(total_lpv):,}")
    m9.metric("Video Views", f"{int(total_video_views):,}")
    m10.metric("Post Reactions", f"{int(total_reactions):,}")
    total_new_cust = df["new_customers"].sum() if "new_customers" in df.columns else 0
    overall_cac = total_spend / total_new_cust if total_new_cust > 0 else 0
    m11.metric("Overall CAC", f"${overall_cac:,.0f}")
    m12.metric("", "")

    st.markdown("")

    # Weekly table
    meta_table = df[["week_start"]].copy()
    meta_table["week_start"] = meta_table["week_start"].dt.strftime("%d/%m/%Y")
    if "meta_spend" in df.columns:
        meta_table["Spend ($)"] = df["meta_spend"].map(lambda x: f"${x:,.2f}")
    if "meta_leads" in df.columns:
        meta_table["Leads (Form)"] = df["meta_leads"].astype(int)
    if "meta_impressions" in df.columns:
        meta_table["Impressions"] = df["meta_impressions"].astype(int)
    if "meta_link_clicks" in df.columns:
        meta_table["Link Clicks"] = df["meta_link_clicks"].astype(int)
    if "meta_landing_page_views" in df.columns:
        meta_table["LPV"] = df["meta_landing_page_views"].astype(int)
    if "meta_video_views" in df.columns:
        meta_table["Video Views"] = df["meta_video_views"].astype(int)
    if "meta_post_reactions" in df.columns:
        meta_table["Reactions"] = df["meta_post_reactions"].astype(int)
    if "meta_link_clicks" in df.columns and "meta_impressions" in df.columns:
        meta_table["CTR %"] = (
            (
                df["meta_link_clicks"]
                / df["meta_impressions"].replace(0, float("nan"))
                * 100
            )
            .round(2)
            .fillna(0)
        )
    if "meta_spend" in df.columns and "meta_link_clicks" in df.columns:
        meta_table["CPC ($)"] = (
            (df["meta_spend"] / df["meta_link_clicks"].replace(0, float("nan")))
            .round(2)
            .fillna(0)
            .map(lambda x: f"${x:,.2f}")
        )
    if "meta_spend" in df.columns and "meta_leads" in df.columns:
        meta_table["CPL ($)"] = (
            (df["meta_spend"] / df["meta_leads"].replace(0, float("nan")))
            .round(2)
            .fillna(0)
            .map(lambda x: f"${x:,.2f}")
        )

    meta_table = meta_table.rename(columns={"week_start": "Week"})
    meta_table = meta_table.iloc[::-1].reset_index(drop=True)

    st.dataframe(meta_table, use_container_width=True, hide_index=True, height=400)
else:
    st.info(
        "No Meta Ads data yet. Set META_ACCESS_TOKEN in refresh_dashboard.py to enable this."
    )

st.markdown("---")

# ── TikTok Ads ──
st.subheader("🎵 TikTok Ads Performance")

if "tt_spend" in df.columns and df["tt_spend"].sum() > 0:
    # Summary KPI cards
    tt_total_spend = df["tt_spend"].sum()
    tt_total_clicks = df["tt_clicks"].sum() if "tt_clicks" in df.columns else 0
    tt_total_impressions = (
        df["tt_impressions"].sum() if "tt_impressions" in df.columns else 0
    )
    tt_total_conversions = (
        df["tt_conversions"].sum() if "tt_conversions" in df.columns else 0
    )
    tt_total_reach = df["tt_reach"].sum() if "tt_reach" in df.columns else 0
    tt_total_vv100 = (
        df["tt_video_views_100"].sum() if "tt_video_views_100" in df.columns else 0
    )
    tt_avg_cpc = tt_total_spend / tt_total_clicks if tt_total_clicks > 0 else 0
    tt_avg_ctr = (
        (tt_total_clicks / tt_total_impressions * 100)
        if tt_total_impressions > 0
        else 0
    )
    tt_cost_per_conv = (
        tt_total_spend / tt_total_conversions if tt_total_conversions > 0 else 0
    )

    t1, t2, t3, t4, t5, t6 = st.columns(6)
    t1.metric("Total Spend", f"${tt_total_spend:,.0f}")
    t2.metric("Conversions", f"{int(tt_total_conversions):,}")
    t3.metric("Cost / Conv", f"${tt_cost_per_conv:,.2f}")
    t4.metric("Clicks", f"{int(tt_total_clicks):,}")
    t5.metric("Avg CPC", f"${tt_avg_cpc:,.2f}")
    t6.metric("CTR", f"{tt_avg_ctr:.2f}%")

    t7, t8, t9, t10, t11, t12 = st.columns(6)
    t7.metric("Impressions", f"{int(tt_total_impressions):,}")
    t8.metric("Reach", f"{int(tt_total_reach):,}")
    t9.metric("Video Completions", f"{int(tt_total_vv100):,}")
    t10.metric("", "")
    t11.metric("", "")
    t12.metric("", "")

    st.markdown("")

    # Weekly table
    tt_table = df[["week_start"]].copy()
    tt_table["week_start"] = tt_table["week_start"].dt.strftime("%d/%m/%Y")
    if "tt_spend" in df.columns:
        tt_table["Spend ($)"] = df["tt_spend"].map(lambda x: f"${x:,.2f}")
    if "tt_conversions" in df.columns:
        tt_table["Conversions"] = df["tt_conversions"].astype(int)
    if "tt_impressions" in df.columns:
        tt_table["Impressions"] = df["tt_impressions"].astype(int)
    if "tt_clicks" in df.columns:
        tt_table["Clicks"] = df["tt_clicks"].astype(int)
    if "tt_reach" in df.columns:
        tt_table["Reach"] = df["tt_reach"].astype(int)
    if "tt_video_views_100" in df.columns:
        tt_table["Video Completions"] = df["tt_video_views_100"].astype(int)
    if "tt_clicks" in df.columns and "tt_impressions" in df.columns:
        tt_table["CTR %"] = (
            (df["tt_clicks"] / df["tt_impressions"].replace(0, float("nan")) * 100)
            .round(2)
            .fillna(0)
        )
    if "tt_spend" in df.columns and "tt_clicks" in df.columns:
        tt_table["CPC ($)"] = (
            (df["tt_spend"] / df["tt_clicks"].replace(0, float("nan")))
            .round(2)
            .fillna(0)
            .map(lambda x: f"${x:,.2f}")
        )
    if "tt_spend" in df.columns and "tt_conversions" in df.columns:
        tt_table["Cost/Conv ($)"] = (
            (df["tt_spend"] / df["tt_conversions"].replace(0, float("nan")))
            .round(2)
            .fillna(0)
            .map(lambda x: f"${x:,.2f}")
        )

    tt_table = tt_table.rename(columns={"week_start": "Week"})
    tt_table = tt_table.iloc[::-1].reset_index(drop=True)

    st.dataframe(tt_table, use_container_width=True, hide_index=True, height=400)
else:
    st.info(
        "No TikTok Ads data yet. Set TIKTOK_ACCESS_TOKEN in refresh_dashboard.py once your app is approved."
    )

st.markdown("---")

# ── Full Data Table ──
st.subheader("📋 Weekly Data Table")
st.caption("Full weekly breakdown — matches the manual tracking spreadsheet format")

display_df = df.copy()
display_df["week_start"] = display_df["week_start"].dt.strftime("%d/%m/%Y")

rename_map = {
    "week_start": "Week",
    "week_number": "#",
    "applications_created": "Apps Created",
    "card_details": "Card Details",
    "card_conversion_pct": "Card Conv %",
    "new_trialers": "New Trialers",
    "self_serve_conversion_pct": "Self-Serve Conv %",
    "new_customers": "New Customers",
    "sales_revenue_usd": "Sales ($)",
    "cancellations": "Cancellations",
    "total_paying_customers": "Total Paying",
    "active_users": "Active Users",
    "new_registrations": "New Registrations",
    "free_accounts": "Free Accounts",
    "demo_calls": "Demo Calls",
    "meta_spend": "Meta Spend ($)",
    "meta_impressions": "Meta Impressions",
    "meta_clicks": "Meta Clicks",
    "meta_link_clicks": "Meta Link Clicks",
    "meta_landing_page_views": "Meta Leads (LPV)",
    "meta_video_views": "Meta Video Views",
    "meta_post_reactions": "Meta Reactions",
    "tt_spend": "TikTok Spend ($)",
    "tt_impressions": "TikTok Impressions",
    "tt_clicks": "TikTok Clicks",
    "tt_conversions": "TikTok Conversions",
    "tt_reach": "TikTok Reach",
    "tt_cpc": "TikTok CPC",
    "tt_ctr": "TikTok CTR %",
    "tt_cost_per_conversion": "TikTok Cost/Conv",
    "tt_video_views_100": "TikTok Video Completions",
}

available_renames = {k: v for k, v in rename_map.items() if k in display_df.columns}
display_df = display_df.rename(columns=available_renames)

# Show most recent first
display_df = display_df.iloc[::-1].reset_index(drop=True)

st.dataframe(display_df, use_container_width=True, hide_index=True, height=600)

# ── Download CSV ──
csv = display_df.to_csv(index=False)
st.download_button(
    label="📥 Download as CSV",
    data=csv,
    file_name="kliq_leads_sales_weekly.csv",
    mime="text/csv",
)
