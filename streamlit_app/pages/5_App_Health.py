"""
Page 5 — App Health
MAU/DAU, user overview, engagement metrics, subscriptions,
device breakdown, user location. Filterable by app.
"""

import streamlit as st
import plotly.express as px
import pandas as pd
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

st.set_page_config(page_title="App Health — KLIQ", page_icon="📱", layout="wide")
inject_css()
register_plotly_template()
require_auth()
logout_button()
st.title("App Health")
st.markdown("---")

# ── App Filter ──
with st.spinner("Loading app data..."):
    apps = load_app_lookup()

app_map = {}
if (
    not apps.empty
    and "application_id" in apps.columns
    and "application_name" in apps.columns
):
    app_map = dict(zip(apps["application_name"], apps["application_id"]))
    app_names = sorted([n for n in apps["application_name"].dropna().unique() if n])
    selected_app = st.sidebar.selectbox(
        "Select App", ["All Apps"] + app_names, key="health_app"
    )
else:
    selected_app = "All Apps"


def get_app_id():
    if selected_app == "All Apps":
        return None
    return app_map.get(selected_app)


def filter_by_app_id(df):
    app_id = get_app_id()
    if app_id is None or df.empty or "application_id" not in df.columns:
        return df
    return df[df["application_id"] == app_id]


def filter_by_app_name(df):
    if selected_app == "All Apps" or df.empty or "application_name" not in df.columns:
        return df
    return df[df["application_name"] == selected_app]


st.sidebar.markdown("---")
st.sidebar.markdown(f"**Apps tracked:** {len(apps):,}")

# ── KPI Cards ──
try:
    users_all = load_app_user_overview()
    users_kpi = filter_by_app_id(users_all) if selected_app != "All Apps" else users_all
    total_registered = (
        int(users_kpi["total_users"].sum())
        if not users_kpi.empty and "total_users" in users_kpi.columns
        else 0
    )
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total Registered Users", f"{total_registered:,}")
    with kpi2:
        regular = (
            int(users_kpi["regular_users"].sum())
            if not users_kpi.empty and "regular_users" in users_kpi.columns
            else 0
        )
        st.metric("Regular Users", f"{regular:,}")
    with kpi3:
        web_u = (
            int(users_kpi["web_users"].sum())
            if not users_kpi.empty and "web_users" in users_kpi.columns
            else 0
        )
        st.metric("Web Users", f"{web_u:,}")
    with kpi4:
        app_u = (
            int(users_kpi["app_users"].sum())
            if not users_kpi.empty and "app_users" in users_kpi.columns
            else 0
        )
        st.metric("App Users", f"{app_u:,}")
    st.markdown("---")
except Exception as e:
    st.warning(f"Could not load user KPIs: {e}")

# ── MAU ──
st.subheader("📊 Monthly Active Users (MAU)")

try:
    mau = load_app_mau()
    mau_f = filter_by_app_id(mau)
    if not mau_f.empty and "month" in mau_f.columns and "mau" in mau_f.columns:
        agg = mau_f.groupby("month")["mau"].sum().reset_index()
        title = (
            f"MAU — {selected_app}"
            if selected_app != "All Apps"
            else "Total MAU Over Time"
        )
        fig = px.bar(
            agg,
            x="month",
            y="mau",
            title=title,
            labels={"mau": "MAU", "month": "Month"},
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No MAU data available.")
except Exception as e:
    st.warning(f"Could not load MAU: {e}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Daily Active Users")
    try:
        dau = load_app_dau()
        dau_f = filter_by_app_id(dau)
        if not dau_f.empty and "date" in dau_f.columns and "dau" in dau_f.columns:
            dau_f = dau_f.copy()
            dau_f["date"] = pd.to_datetime(dau_f["date"], errors="coerce")
            agg = dau_f.groupby("date")["dau"].sum().reset_index()
            title = (
                f"DAU — {selected_app}" if selected_app != "All Apps" else "Total DAU"
            )
            fig2 = px.line(agg, x="date", y="dau", title=title)
            fig2.update_layout(height=350)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No DAU data available.")
    except Exception as e:
        st.warning(f"Could not load DAU: {e}")

with col2:
    st.subheader("👥 User Overview")
    try:
        users = load_app_user_overview()
        users_f = filter_by_app_id(users)
        if not users_f.empty:
            # Show application_name if available
            display_cols = [
                c
                for c in [
                    "application_name",
                    "total_users",
                    "talent_users",
                    "regular_users",
                    "web_users",
                    "app_users",
                ]
                if c in users_f.columns
            ]
            st.dataframe(
                users_f[display_cols] if display_cols else users_f,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No user overview data available.")
    except Exception as e:
        st.warning(f"Could not load user overview: {e}")

st.markdown("---")

# ── Engagement ──
st.subheader("⚡ Engagement Metrics")

try:
    engagement = load_app_engagement_d2()
    eng_f = filter_by_app_id(engagement)
    if (
        not eng_f.empty
        and "metric" in eng_f.columns
        and "date" in eng_f.columns
        and "value" in eng_f.columns
    ):
        metrics = sorted(eng_f["metric"].unique().tolist())
        selected_metrics = st.multiselect(
            "Select engagement metrics", metrics, default=metrics[:5], key="health_eng"
        )
        filtered = eng_f[eng_f["metric"].isin(selected_metrics)]
        if not filtered.empty:
            filtered = filtered.copy()
            filtered["date"] = pd.to_datetime(filtered["date"])
            filtered["week"] = filtered["date"].dt.to_period("W").dt.start_time
            weekly = filtered.groupby(["week", "metric"])["value"].sum().reset_index()
            fig3 = px.line(
                weekly, x="week", y="value", color="metric", title="Weekly Engagement"
            )
            fig3.update_layout(height=450)
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No engagement data available.")
except Exception as e:
    st.warning(f"Could not load engagement: {e}")

# ── Subscriptions ──
st.subheader("💳 Subscriptions & Revenue")

try:
    subs = load_app_subscriptions()
    subs_f = filter_by_app_id(subs)
    if (
        not subs_f.empty
        and "metric" in subs_f.columns
        and "date" in subs_f.columns
        and "value" in subs_f.columns
    ):
        metrics = sorted(subs_f["metric"].unique().tolist())
        selected = st.multiselect(
            "Select subscription metrics",
            metrics,
            default=metrics[:4],
            key="health_sub",
        )
        filtered = subs_f[subs_f["metric"].isin(selected)]
        if not filtered.empty:
            filtered = filtered.copy()
            filtered["date"] = pd.to_datetime(filtered["date"])
            filtered["month"] = filtered["date"].dt.to_period("M").dt.start_time
            monthly = filtered.groupby(["month", "metric"])["value"].sum().reset_index()
            fig4 = px.bar(
                monthly,
                x="month",
                y="value",
                color="metric",
                title="Subscriptions & Revenue",
                barmode="group",
            )
            fig4.update_layout(height=450)
            st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No subscription data available.")
except Exception as e:
    st.warning(f"Could not load subscriptions: {e}")

st.markdown("---")

# ── Device Breakdown & Downloads ──
st.subheader("📱 Device Breakdown & Downloads")

col1, col2 = st.columns(2)

with col1:
    try:
        devices = load_app_device_breakdown()
        dev_f = filter_by_app_name(devices)
        if (
            not dev_f.empty
            and "device" in dev_f.columns
            and "unique_users" in dev_f.columns
        ):
            if selected_app == "All Apps":
                agg = dev_f.groupby("device")["unique_users"].sum().reset_index()
            else:
                agg = dev_f
            fig5 = px.pie(
                agg, names="device", values="unique_users", title="Users by Device Type"
            )
            fig5.update_layout(height=350)
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No device breakdown data available.")
    except Exception as e:
        st.warning(f"Could not load device breakdown: {e}")

with col2:
    try:
        downloads = load_app_downloads()
        dl_f = filter_by_app_name(downloads)
        if not dl_f.empty:
            st.markdown("**App Downloads (iOS + KLIQ Registered)**")
            display_dl_cols = [
                c
                for c in [
                    "application_name",
                    "ios_first_downloads",
                    "ios_redownloads",
                    "ios_total_downloads",
                    "kliq_registered_users",
                ]
                if c in dl_f.columns
            ]
            st.dataframe(
                dl_f[display_dl_cols] if display_dl_cols else dl_f,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No download data available.")
    except Exception as e:
        st.warning(f"Could not load downloads: {e}")

st.markdown("---")

# ── User Location ──
st.subheader("🌍 User Location")

try:
    acq = load_ga4_acquisition()
    if not acq.empty and "country" in acq.columns and "unique_users" in acq.columns:
        country_agg = (
            acq.groupby("country")["unique_users"].sum().nlargest(25).reset_index()
        )

        col1, col2 = st.columns([2, 1])
        with col1:
            fig_map = px.choropleth(
                country_agg,
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
            st.plotly_chart(fig_map, use_container_width=True)
        with col2:
            country_agg_display = country_agg.copy()
            country_agg_display["unique_users"] = country_agg_display[
                "unique_users"
            ].apply(lambda x: f"{x:,}")
            country_agg_display.columns = ["Country", "Users"]
            st.dataframe(country_agg_display, use_container_width=True, hide_index=True)
    else:
        st.info("No location data available.")
except Exception as e:
    st.warning(f"Could not load location data: {e}")
