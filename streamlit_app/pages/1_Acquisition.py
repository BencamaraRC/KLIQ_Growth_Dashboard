"""
Page 1 — Acquisition
Signups, new customers, country breakdown, website traffic by channel,
GA4 sessions, signup funnel with drop-offs, device breakdown.
Filtered by date range (days previous).
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth, logout_button
from kliq_ui_kit import (
    inject_css,
    register_plotly_template,
    GREEN,
    DARK,
    TANGERINE,
    LIME,
    ALPINE,
    ERROR,
    NEUTRAL,
    CHART_SEQUENCE,
)
from data import (
    load_growth_metrics,
    load_ga4_acquisition,
    load_ga4_traffic,
    load_ga4_funnel,
    load_device_type,
    load_onboarding_funnel,
    load_engagement_funnel,
)

st.set_page_config(page_title="Acquisition — KLIQ", page_icon="🌐", layout="wide")
inject_css()
register_plotly_template()
require_auth()
logout_button()
st.title("Acquisition")
st.markdown("---")

# ── Date Filter ──
days_options = {
    "Last 7 days": 7,
    "Last 14 days": 14,
    "Last 30 days": 30,
    "Last 90 days": 90,
    "All Time": 9999,
}
selected_range = st.sidebar.selectbox("Date Range", list(days_options.keys()), index=2)
days_back = days_options[selected_range]
cutoff = datetime.now() - timedelta(days=days_back)


def filter_by_date(df, date_col="date"):
    if df.empty or date_col not in df.columns:
        return df
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df[df[date_col] >= cutoff]


# ── Load Data ──
with st.spinner("Loading acquisition data..."):
    growth = load_growth_metrics()
    acquisition = load_ga4_acquisition()
    traffic = load_ga4_traffic()
    funnel = load_ga4_funnel()
    devices = load_device_type()
    onboarding = load_onboarding_funnel()
    engagement_funnel = load_engagement_funnel()

growth_f = filter_by_date(growth)
acq_f = filter_by_date(acquisition)
traffic_f = filter_by_date(traffic)
funnel_f = filter_by_date(funnel)
devices_f = filter_by_date(devices)
onboarding_f = filter_by_date(onboarding)
engagement_f = filter_by_date(engagement_funnel)

# ── KPI Cards ──
col1, col2, col3, col4 = st.columns(4)

# Signups
with col1:
    if (
        not growth_f.empty
        and "metric" in growth_f.columns
        and "value" in growth_f.columns
    ):
        signups = growth_f[
            growth_f["metric"].str.contains(
                "signup|sign_up|self_serve", case=False, na=False
            )
        ]
        total_signups = int(signups["value"].sum()) if not signups.empty else 0
        st.metric("Total Signups", f"{total_signups:,}")
    else:
        st.metric("Total Signups", "N/A")

# New Customers (upgraded)
with col2:
    if (
        not growth_f.empty
        and "metric" in growth_f.columns
        and "value" in growth_f.columns
    ):
        customers = growth_f[
            growth_f["metric"].str.contains(
                "customer|upgrade|paid|convert", case=False, na=False
            )
        ]
        total_customers = int(customers["value"].sum()) if not customers.empty else 0
        st.metric(
            "New Customers", f"{total_customers:,}" if total_customers > 0 else "N/A"
        )
    else:
        st.metric("New Customers", "N/A")

# Total Sessions
with col3:
    if not traffic_f.empty and "sessions" in traffic_f.columns:
        st.metric("Website Sessions", f"{int(traffic_f['sessions'].sum()):,}")
    else:
        st.metric("Website Sessions", "N/A")

# Countries
with col4:
    if not acq_f.empty and "country" in acq_f.columns:
        st.metric("Countries", f"{acq_f['country'].nunique()}")
    else:
        st.metric("Countries", "N/A")

st.markdown("---")

# ── Signups by Country ──
st.subheader("🌍 Signups by Country")

if not acq_f.empty and "country" in acq_f.columns and "unique_users" in acq_f.columns:
    country_agg = (
        acq_f.groupby("country")["unique_users"].sum().nlargest(20).reset_index()
    )
    col1, col2 = st.columns([2, 1])
    with col1:
        fig_country = px.bar(
            country_agg,
            x="country",
            y="unique_users",
            title="Top 20 Countries by Unique Users",
            labels={"unique_users": "Users", "country": "Country"},
            color="unique_users",
            color_continuous_scale=[[0, "#9CF0FF"], [0.5, "#1C3838"], [1, "#021111"]],
        )
        fig_country.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_country, use_container_width=True)
    with col2:
        st.dataframe(country_agg, use_container_width=True, hide_index=True)
else:
    st.info("No country data available.")

st.markdown("---")

# ── Website Traffic by Channel ──
st.subheader("📊 Website Traffic by Channel")

if (
    not traffic_f.empty
    and "channel" in traffic_f.columns
    and "sessions" in traffic_f.columns
):
    traffic_c = traffic_f.copy()
    traffic_c["week"] = traffic_c["date"].dt.to_period("W").dt.start_time

    weekly = traffic_c.groupby(["week", "channel"])["sessions"].sum().reset_index()
    channels = sorted(weekly["channel"].unique().tolist())
    selected_channels = st.multiselect(
        "Select channels", channels, default=channels[:6], key="acq_channels"
    )
    filtered = weekly[weekly["channel"].isin(selected_channels)]
    if not filtered.empty:
        fig = px.line(
            filtered,
            x="week",
            y="sessions",
            color="channel",
            title="Weekly Sessions by Channel",
            labels={"sessions": "Sessions", "week": "Week"},
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

    # Traffic by device + country
    col1, col2 = st.columns(2)
    with col1:
        if "device_type" in traffic_f.columns:
            dev_agg = traffic_f.groupby("device_type")["sessions"].sum().reset_index()
            fig_dev = px.pie(
                dev_agg,
                names="device_type",
                values="sessions",
                title="Sessions by Device",
            )
            fig_dev.update_layout(height=350)
            st.plotly_chart(fig_dev, use_container_width=True)
    with col2:
        if "country" in traffic_f.columns:
            country_sessions = (
                traffic_f.groupby("country")["sessions"]
                .sum()
                .nlargest(15)
                .reset_index()
            )
            fig_cs = px.bar(
                country_sessions,
                x="country",
                y="sessions",
                title="Top 15 Countries by Sessions",
            )
            fig_cs.update_layout(height=350, xaxis_tickangle=-45)
            st.plotly_chart(fig_cs, use_container_width=True)
else:
    st.info("No traffic data available.")

st.markdown("---")

# ── Acquisition Sources ──
st.subheader("🔗 Acquisition Sources")

if not acq_f.empty and "source" in acq_f.columns and "unique_users" in acq_f.columns:
    col1, col2 = st.columns(2)
    with col1:
        source_agg = (
            acq_f.groupby("source")["unique_users"].sum().nlargest(15).reset_index()
        )
        fig_src = px.bar(
            source_agg,
            x="source",
            y="unique_users",
            title="Top 15 Sources",
            labels={"unique_users": "Users", "source": "Source"},
        )
        fig_src.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_src, use_container_width=True)
    with col2:
        if "medium" in acq_f.columns:
            medium_agg = acq_f.groupby("medium")["unique_users"].sum().reset_index()
            fig_med = px.pie(
                medium_agg,
                names="medium",
                values="unique_users",
                title="Users by Medium",
            )
            fig_med.update_layout(height=400)
            st.plotly_chart(fig_med, use_container_width=True)

st.markdown("---")

# ── Visual 1: Sign-up Funnel ──
st.subheader("🔽 Sign-up Funnel")
st.caption("Started Sign-up → Created Account → Added Payment → Completed Payment")

if (
    not onboarding_f.empty
    and "funnel_step" in onboarding_f.columns
    and "value" in onboarding_f.columns
):
    ob_agg = (
        onboarding_f.groupby(["funnel_step", "step_order"])["value"]
        .sum()
        .reset_index()
        .sort_values("step_order")
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        fig_signup = px.funnel(
            ob_agg,
            x="value",
            y="funnel_step",
            title="Sign-up Funnel",
        )
        fig_signup.update_layout(height=400)
        st.plotly_chart(fig_signup, use_container_width=True)
    with col2:
        ob_agg = ob_agg.reset_index(drop=True)
        ob_agg["drop_off"] = ob_agg["value"].diff(-1).fillna(0).astype(int)
        ob_agg["drop_off_pct"] = (ob_agg["drop_off"] / ob_agg["value"] * 100).round(1)
        st.markdown("**Drop-off between steps:**")
        st.dataframe(
            ob_agg[["funnel_step", "value", "drop_off", "drop_off_pct"]].rename(
                columns={
                    "funnel_step": "Step",
                    "value": "Users",
                    "drop_off": "Drop-off",
                    "drop_off_pct": "Drop-off %",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info("No sign-up funnel data available.")

st.markdown("---")

# ── Visual 2: Engagement Funnel ──
st.subheader("⚡ Engagement Funnel")
st.caption("Uploaded Profile → Created Livestream → Previewed App → Copied URL")

if (
    not engagement_f.empty
    and "funnel_step" in engagement_f.columns
    and "value" in engagement_f.columns
):
    eng_agg = (
        engagement_f.groupby(["funnel_step", "step_order"])["value"]
        .sum()
        .reset_index()
        .sort_values("step_order")
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        fig_eng = px.funnel(
            eng_agg,
            x="value",
            y="funnel_step",
            title="Engagement Funnel",
        )
        fig_eng.update_layout(height=400)
        st.plotly_chart(fig_eng, use_container_width=True)
    with col2:
        eng_agg = eng_agg.reset_index(drop=True)
        eng_agg["drop_off"] = eng_agg["value"].diff(-1).fillna(0).astype(int)
        eng_agg["drop_off_pct"] = (eng_agg["drop_off"] / eng_agg["value"] * 100).round(
            1
        )
        st.markdown("**Drop-off between steps:**")
        st.dataframe(
            eng_agg[["funnel_step", "value", "drop_off", "drop_off_pct"]].rename(
                columns={
                    "funnel_step": "Step",
                    "value": "Users",
                    "drop_off": "Drop-off",
                    "drop_off_pct": "Drop-off %",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info("No engagement funnel data available.")

st.markdown("---")

# ── Device Breakdown ──
st.subheader("📱 Device Breakdown")

if (
    not devices_f.empty
    and "device_type" in devices_f.columns
    and "value" in devices_f.columns
):
    dev_totals = devices_f.groupby("device_type")["value"].sum().reset_index()
    dev_totals = dev_totals[dev_totals["value"] > 0]
    fig_pie = px.pie(
        dev_totals, names="device_type", values="value", title="Signups by Device Type"
    )
    fig_pie.update_layout(height=350)
    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("No device type data available.")

# ── Raw Data ──
with st.expander("📋 View Raw Data"):
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Acquisition", "Traffic", "Funnel", "Growth Metrics"]
    )
    with tab1:
        st.dataframe(acq_f, use_container_width=True)
    with tab2:
        st.dataframe(traffic_f, use_container_width=True)
    with tab3:
        st.dataframe(funnel_f, use_container_width=True)
    with tab4:
        st.dataframe(growth_f, use_container_width=True)
