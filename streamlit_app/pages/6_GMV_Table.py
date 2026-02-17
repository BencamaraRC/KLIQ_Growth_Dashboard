"""
Page 6 — GMV Table
Per-coach monthly GMV revenue table, total GMV, avg LTV per app,
avg rev per app last month. Filtered by app.
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
    load_coach_gmv_timeline,
    load_coach_growth_stages,
    load_unified_revenue,
    load_app_lookup,
)

st.set_page_config(page_title="GMV Table — KLIQ", page_icon="💵", layout="wide")
inject_css()
register_plotly_template()
require_auth()
logout_button()
st.title("GMV Table")
st.markdown("---")

# ── App Filter ──
apps = load_app_lookup()
app_names = []
if not apps.empty and "application_name" in apps.columns:
    app_names = sorted([n for n in apps["application_name"].dropna().unique() if n])

selected_app = st.sidebar.selectbox(
    "Filter by App", ["All Apps"] + app_names, key="gmv_app"
)


def filter_by_app_name(df):
    if selected_app == "All Apps" or df.empty or "application_name" not in df.columns:
        return df
    return df[df["application_name"] == selected_app]


# ── Load Data ──
with st.spinner("Loading GMV data..."):
    gmv_timeline = load_coach_gmv_timeline()
    stages = load_coach_growth_stages()
    unified_rev = load_unified_revenue()

gmv_f = filter_by_app_name(gmv_timeline)
stages_f = filter_by_app_name(stages)
unified_f = filter_by_app_name(unified_rev)

# Total GMV from unified revenue (Stripe + Apple IAP = ~$1.05M)
total_unified_gmv = (
    unified_f["revenue"].sum()
    if not unified_f.empty and "revenue" in unified_f.columns
    else 0
)

# ── KPI Cards ──
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total GMV (Stripe + Apple)", f"${total_unified_gmv:,.0f}")

with col2:
    # Avg LTV per app = total unified GMV / number of apps with revenue
    if not unified_f.empty and "application_name" in unified_f.columns:
        app_totals = unified_f.groupby("application_name")["revenue"].sum()
        apps_with_rev = app_totals[app_totals > 0]
        if len(apps_with_rev) > 0:
            avg_ltv = apps_with_rev.mean()
            st.metric("Avg LTV per App", f"${avg_ltv:,.0f}")
        else:
            st.metric("Avg LTV per App", "$0")
    else:
        st.metric("Avg LTV per App", "N/A")

with col3:
    # Avg rev per app last month
    if not unified_f.empty and "month" in unified_f.columns:
        last_month = unified_f["month"].max()
        last_month_data = unified_f[unified_f["month"] == last_month]
        if not last_month_data.empty:
            avg_last = (
                last_month_data.groupby("application_name")["revenue"].sum().mean()
            )
            st.metric("Avg Rev/App (Last Month)", f"${avg_last:,.0f}")
        else:
            st.metric("Avg Rev/App (Last Month)", "N/A")
    else:
        st.metric("Avg Rev/App (Last Month)", "N/A")

with col4:
    if not unified_f.empty and "application_name" in unified_f.columns:
        st.metric("Apps with Revenue", f"{unified_f['application_name'].nunique():,}")
    else:
        st.metric("Apps with Revenue", "N/A")

st.markdown("---")

# ── Monthly GMV Table (Pivot) — Unified Revenue ──
st.subheader("📊 Monthly GMV by Coach (Stripe + Apple IAP)")

if (
    not unified_f.empty
    and "month" in unified_f.columns
    and "application_name" in unified_f.columns
    and "revenue" in unified_f.columns
):
    # Aggregate across revenue sources per app per month
    agg = (
        unified_f.groupby(["application_name", "month"])["revenue"].sum().reset_index()
    )

    # Create pivot table: coaches as rows, months as columns
    pivot = agg.pivot_table(
        index="application_name",
        columns="month",
        values="revenue",
        aggfunc="sum",
        fill_value=0,
    )

    # Add total column
    pivot["Total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("Total", ascending=False)

    # Format as currency
    styled = pivot.style.format("${:,.0f}")
    st.dataframe(styled, use_container_width=True, height=600)

    # Summary row
    st.markdown(f"**Total GMV across all months:** ${pivot['Total'].sum():,.0f}")
    st.markdown(f"**Coaches shown:** {len(pivot)}")
else:
    st.info("No unified revenue data available.")

st.markdown("---")

# ── GMV Trend Chart ──
st.subheader("📈 GMV Trend")

if (
    not unified_f.empty
    and "month" in unified_f.columns
    and "revenue" in unified_f.columns
):
    if selected_app != "All Apps":
        # Single coach: stacked by revenue source
        monthly = (
            unified_f.groupby(["month", "revenue_source"])["revenue"]
            .sum()
            .reset_index()
        )
        fig = px.bar(
            monthly,
            x="month",
            y="revenue",
            color="revenue_source",
            title=f"Monthly GMV — {selected_app} (by Source)",
            labels={"revenue": "GMV ($)", "month": "Month"},
            barmode="stack",
            color_discrete_map={"Stripe": GREEN, "iOS App Store": TANGERINE},
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        # All coaches — aggregate by month, stacked by source
        monthly_total = (
            unified_rev.groupby(["month", "revenue_source"])["revenue"]
            .sum()
            .reset_index()
        )
        fig = px.bar(
            monthly_total,
            x="month",
            y="revenue",
            color="revenue_source",
            title="Total Monthly GMV (Stripe + Apple IAP)",
            labels={"revenue": "GMV ($)", "month": "Month"},
            barmode="stack",
            color_discrete_map={"Stripe": GREEN, "iOS App Store": TANGERINE},
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

        # Top coaches stacked
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
        fig2 = px.bar(
            top_monthly,
            x="month",
            y="revenue",
            color="application_name",
            title="Monthly GMV — Top 10 Coaches",
            labels={"revenue": "GMV ($)", "month": "Month"},
            barmode="stack",
        )
        fig2.update_layout(height=450)
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── Coach Revenue Summary Table ──
st.subheader("📋 Coach Revenue Summary")

if not stages_f.empty:
    display_cols = [
        "application_name",
        "total_gmv",
        "kliq_revenue",
        "mrr",
        "total_subs",
        "avg_sub_price",
        "active_months",
        "growth_stage",
    ]
    available = [c for c in display_cols if c in stages_f.columns]
    if available:
        summary = stages_f[available].sort_values(
            "total_gmv" if "total_gmv" in available else available[0], ascending=False
        )
        st.dataframe(summary, use_container_width=True, hide_index=True)
    else:
        st.dataframe(stages_f, use_container_width=True, hide_index=True)
else:
    st.info("No coach growth stage data available.")

# ── Raw Data ──
with st.expander("📋 View Raw GMV Data"):
    tab1, tab2 = st.tabs(
        ["Unified Revenue (Stripe + Apple)", "Stripe Only (GMV Timeline)"]
    )
    with tab1:
        st.dataframe(unified_f, use_container_width=True)
    with tab2:
        st.dataframe(gmv_f, use_container_width=True)
