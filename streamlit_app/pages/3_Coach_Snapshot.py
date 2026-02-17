"""
Page 3 — Coach Snapshot
Total GMV, paid to KLIQ, hosting fee, currency, months active on KLIQ,
KLIQ app fee %, GMV timeline, MAU, DAU, app opens.
Filtered by time and app name.
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

st.set_page_config(page_title="Coach Snapshot — KLIQ", page_icon="📸", layout="wide")
inject_css()
register_plotly_template()
require_auth()
logout_button()
st.title("Coach Snapshot")
st.markdown("---")

# ── Filters ──
apps = load_app_lookup()
app_names = []
app_map = {}
if not apps.empty and "application_name" in apps.columns:
    app_names = sorted([n for n in apps["application_name"].dropna().unique() if n])
    if "application_id" in apps.columns:
        app_map = dict(zip(apps["application_name"], apps["application_id"]))

selected_app = st.sidebar.selectbox(
    "Filter by App", ["All Apps"] + app_names, key="snap_app"
)

days_options = {
    "Last 30 days": 30,
    "Last 90 days": 90,
    "Last 180 days": 180,
    "Last 365 days": 365,
    "All Time": 9999,
}
selected_range = st.sidebar.selectbox(
    "Time Range", list(days_options.keys()), index=4, key="snap_time"
)
days_back = days_options[selected_range]


def get_app_id():
    if selected_app == "All Apps":
        return None
    return app_map.get(selected_app)


def filter_by_app_name(df):
    if selected_app == "All Apps" or df.empty or "application_name" not in df.columns:
        return df
    return df[df["application_name"] == selected_app]


def filter_by_app_id(df):
    app_id = get_app_id()
    if app_id is None or df.empty or "application_id" not in df.columns:
        return df
    return df[df["application_id"] == app_id]


# ── Load Data ──
with st.spinner("Loading coach snapshot..."):
    summary = load_coach_summary()
    stages = load_coach_growth_stages()
    gmv_timeline = load_coach_gmv_timeline()
    unified_rev = load_unified_revenue()
    churn = load_churn_analysis()

summary_f = filter_by_app_name(summary)
stages_f = filter_by_app_name(stages)
churn_f = filter_by_app_name(churn)
unified_f = filter_by_app_name(unified_rev)

# ── KPI Cards ──
st.subheader("Key Metrics")

# Total GMV from unified revenue (Stripe + Apple IAP + Google Play)
total_unified_gmv = (
    unified_f["revenue"].sum()
    if not unified_f.empty and "revenue" in unified_f.columns
    else 0
)

if selected_app != "All Apps" and not summary_f.empty:
    row = summary_f.iloc[0]
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total GMV", f"${total_unified_gmv:,.0f}")
    with col2:
        kliq_fee = row.get("total_app_fee_to_kliq", 0) or 0
        st.metric("Paid to KLIQ", f"${kliq_fee:,.0f}")
    with col3:
        hosting = row.get("hosting_fee_last_month", None)
        if hosting is not None:
            st.metric("Hosting Fee (Last Month)", f"${hosting:,.0f}")
        else:
            st.metric("Hosting Fee (Last Month)", "N/A")
    with col4:
        currency = row.get("currency", "N/A")
        st.metric("Currency", str(currency) if currency else "N/A")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        months = row.get("months_on_platform", "N/A")
        st.metric("Months Active on KLIQ", f"{months}")
    with col6:
        kliq_rev_pct = row.get("kliq_revenue_pct", None)
        if kliq_rev_pct is not None:
            st.metric("KLIQ App Fee %", f"{kliq_rev_pct:.1f}%")
        else:
            st.metric("KLIQ App Fee %", "N/A")
    with col7:
        mau_val = row.get("latest_mau", "N/A")
        st.metric("Latest MAU", f"{mau_val}" if mau_val else "N/A")
    with col8:
        subs = stages_f.iloc[0].get("total_subs", None) if not stages_f.empty else None
        st.metric("Active Subs", f"{subs}" if subs else "N/A")

    # Revenue source breakdown for this coach
    if not unified_f.empty and "revenue_source" in unified_f.columns:
        src_totals = unified_f.groupby("revenue_source")["revenue"].sum().reset_index()
        src_totals.columns = ["Source", "Revenue"]
        st.markdown("**Revenue by Source:**")
        for _, r in src_totals.iterrows():
            st.markdown(f"- {r['Source']}: **${r['Revenue']:,.0f}**")

elif selected_app == "All Apps":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total GMV", f"${total_unified_gmv:,.0f}")
    with col2:
        if not summary.empty and "total_app_fee_to_kliq" in summary.columns:
            st.metric(
                "Total Paid to KLIQ", f"${summary['total_app_fee_to_kliq'].sum():,.0f}"
            )
        else:
            st.metric("Total Paid to KLIQ", "N/A")
    with col3:
        st.metric("Total Coaches", f"{len(summary):,}")
    with col4:
        if not stages.empty and "mrr" in stages.columns:
            st.metric("Total MRR", f"${stages['mrr'].sum():,.0f}")
        else:
            st.metric("Total MRR", "N/A")

    # Paying Coaches & Active Coaches
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        paying = (
            summary[summary["total_gmv"] > 0]
            if not summary.empty and "total_gmv" in summary.columns
            else pd.DataFrame()
        )
        st.metric("Paying Coaches", f"{len(paying):,}", help="Coaches with GMV > $0")
    with col6:
        non_paying_active = (
            summary[(summary["total_gmv"] == 0) & (summary["latest_mau"] > 0)]
            if not summary.empty
            and "total_gmv" in summary.columns
            and "latest_mau" in summary.columns
            else pd.DataFrame()
        )
        st.metric(
            "Active Coaches (Non-Paying)",
            f"{len(non_paying_active):,}",
            help="Coaches with engagement/activity but $0 GMV",
        )
    with col7:
        pass
    with col8:
        pass

    # Show revenue source breakdown
    if not unified_rev.empty and "revenue_source" in unified_rev.columns:
        src_totals = (
            unified_rev.groupby("revenue_source")["revenue"].sum().reset_index()
        )
        src_totals.columns = ["Source", "Revenue"]
        col_a, col_b = st.columns(2)
        with col_a:
            st.dataframe(src_totals, use_container_width=True, hide_index=True)
        with col_b:
            fig_src = px.pie(
                src_totals,
                names="Source",
                values="Revenue",
                title="GMV by Revenue Source",
            )
            fig_src.update_layout(height=300)
            st.plotly_chart(fig_src, use_container_width=True)

st.markdown("---")

# ── GMV Timeline (Unified: Stripe + Apple IAP) ──
st.subheader("📈 GMV Timeline (All Sources)")

if (
    not unified_f.empty
    and "month" in unified_f.columns
    and "revenue" in unified_f.columns
):
    if selected_app != "All Apps":
        # Single coach: stacked bar by revenue source
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
            title=f"Monthly GMV — {selected_app} (by Source)",
            labels={"revenue": "GMV ($)", "month": "Month"},
            barmode="stack",
            color_discrete_map={
                "Stripe": GREEN,
                "iOS App Store": TANGERINE,
                "Google Play Store": ALPINE,
            },
        )
    else:
        # All coaches: total monthly GMV stacked by source
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
            title="Monthly GMV — All Coaches (Stripe + Apple IAP + Google Play)",
            labels={"revenue": "GMV ($)", "month": "Month"},
            barmode="stack",
            color_discrete_map={
                "Stripe": GREEN,
                "iOS App Store": TANGERINE,
                "Google Play Store": ALPINE,
            },
        )
    fig_gmv.update_layout(height=450)
    st.plotly_chart(fig_gmv, use_container_width=True)

    # Also show top coaches line chart for All Apps view
    if selected_app == "All Apps":
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
        st.plotly_chart(fig_top, use_container_width=True)
else:
    st.info("No unified revenue data available.")

st.markdown("---")

# ── MAU / DAU / App Opens ──
st.subheader("📊 MAU, DAU & App Opens")

col1, col2 = st.columns(2)

with col1:
    try:
        mau = load_app_mau()
        mau_f = filter_by_app_id(mau)
        if not mau_f.empty and "month" in mau_f.columns and "mau" in mau_f.columns:
            agg = mau_f.groupby("month")["mau"].sum().reset_index()
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
            st.plotly_chart(fig_mau, use_container_width=True)
        else:
            st.info("No MAU data available.")
    except Exception as e:
        st.warning(f"Could not load MAU: {e}")

with col2:
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
            fig_dau = px.line(
                agg,
                x="date",
                y="dau",
                title=title,
                labels={"dau": "DAU", "date": "Date"},
            )
            fig_dau.update_layout(height=350)
            st.plotly_chart(fig_dau, use_container_width=True)
        else:
            st.info("No DAU data available.")
    except Exception as e:
        st.warning(f"Could not load DAU: {e}")

# App Opens
try:
    engagement = load_app_engagement_d2()
    eng_f = filter_by_app_id(engagement)
    if not eng_f.empty and "metric" in eng_f.columns and "value" in eng_f.columns:
        app_opens = eng_f[
            eng_f["metric"].str.contains("app_open|open", case=False, na=False)
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
                    else "Weekly App Opens (All)"
                ),
                labels={"value": "App Opens", "week": "Week"},
            )
            fig_opens.update_layout(height=350)
            st.plotly_chart(fig_opens, use_container_width=True)
except Exception as e:
    st.warning(f"Could not load app opens: {e}")

# ── Coach Detail Table ──
st.markdown("---")
st.subheader("📋 Coach Detail")

if not summary_f.empty:
    st.dataframe(summary_f, use_container_width=True, hide_index=True)
else:
    st.info("No coach summary data available.")
