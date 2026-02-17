"""
Page 4 — Coach Deep Dive
Growth stages, top coaches by GMV, GMV timeline, retention curve, feature impact.
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
    load_coach_growth_stages,
    load_coach_gmv_timeline,
    load_unified_revenue,
    load_coach_retention_curve,
    load_feature_retention_impact,
    load_firstweek_retention,
    load_app_health_score,
)

st.set_page_config(page_title="Coach Deep Dive — KLIQ", page_icon="🏋️", layout="wide")
inject_css()
register_plotly_template()
require_auth()
logout_button()
st.title("Coach Deep Dive")
st.markdown("---")

# ── Load Data ──
with st.spinner("Loading coach data..."):
    stages = load_coach_growth_stages()
    gmv_timeline = load_coach_gmv_timeline()
    unified_rev = load_unified_revenue()

# Total GMV from unified revenue (Stripe + Apple IAP)
total_unified_gmv = (
    unified_rev["revenue"].sum()
    if not unified_rev.empty and "revenue" in unified_rev.columns
    else 0
)

# ── KPI Cards ──
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Coaches", f"{len(stages):,}" if not stages.empty else "0")
with col2:
    st.metric("Total GMV (Stripe + Apple)", f"${total_unified_gmv:,.0f}")
with col3:
    if not stages.empty and "total_gmv" in stages.columns:
        revenue_coaches = len(stages[stages["total_gmv"] > 0])
        st.metric("Coaches with Revenue", f"{revenue_coaches}")
    else:
        st.metric("Coaches with Revenue", "N/A")
with col4:
    if not stages.empty and "mrr" in stages.columns:
        st.metric("Total MRR", f"${stages['mrr'].sum():,.0f}")
    else:
        st.metric("Total MRR", "N/A")

st.markdown("---")

# ── Growth Stages ──
st.subheader("📊 Coach Growth Stages")

if not stages.empty and "growth_stage" in stages.columns:
    stage_counts = stages["growth_stage"].value_counts().reset_index()
    stage_counts.columns = ["Stage", "Count"]

    col1, col2 = st.columns([1, 2])
    with col1:
        st.dataframe(stage_counts, use_container_width=True, hide_index=True)
    with col2:
        fig = px.pie(
            stage_counts,
            names="Stage",
            values="Count",
            title="Coach Distribution by Growth Stage",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No growth stage data available.")

st.markdown("---")

# ── Top Coaches by GMV ──
st.subheader("🏆 Top Coaches by GMV")

if (
    not stages.empty
    and "total_gmv" in stages.columns
    and "application_name" in stages.columns
):
    n_coaches = st.slider("Number of coaches to show", 10, 50, 20, key="top_n")
    top = stages.nlargest(n_coaches, "total_gmv")
    fig2 = px.bar(
        top,
        x="application_name",
        y="total_gmv",
        title=f"Top {n_coaches} Coaches by Total GMV",
        labels={"total_gmv": "GMV ($)", "application_name": "Coach"},
        color="total_gmv",
        color_continuous_scale=[[0, "#9CF0FF"], [0.5, "#1C3838"], [1, "#021111"]],
    )
    fig2.update_layout(height=500, xaxis_tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)

    # Show table
    display_cols = [
        "application_name",
        "total_gmv",
        "mrr",
        "total_subs",
        "growth_stage",
        "active_months",
    ]
    available = [c for c in display_cols if c in top.columns]
    st.dataframe(top[available], use_container_width=True, hide_index=True)
else:
    st.info("No GMV data available.")

st.markdown("---")

# ── GMV Timeline ──
st.subheader("📈 GMV Timeline")

if not gmv_timeline.empty and "application_name" in gmv_timeline.columns:
    gmv_col = None
    for c in ["monthly_gmv", "gmv", "total_gmv"]:
        if c in gmv_timeline.columns:
            gmv_col = c
            break

    if gmv_col:
        top_coaches = (
            gmv_timeline.groupby("application_name")[gmv_col]
            .sum()
            .nlargest(10)
            .index.tolist()
        )
        all_coaches = sorted(gmv_timeline["application_name"].unique().tolist())
        selected = st.multiselect(
            "Select coaches", all_coaches, default=top_coaches, key="dd_coaches"
        )
        filtered = gmv_timeline[gmv_timeline["application_name"].isin(selected)]
        if not filtered.empty:
            fig3 = px.line(
                filtered,
                x="month",
                y=gmv_col,
                color="application_name",
                title="Monthly GMV by Coach",
                labels={gmv_col: "GMV ($)", "month": "Month"},
            )
            fig3.update_layout(height=500)
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.dataframe(gmv_timeline.head(50), use_container_width=True)
else:
    st.info("No GMV timeline data available.")

st.markdown("---")

# ── Retention Curve ──
st.subheader("📉 Coach Retention Curve")

try:
    curve = load_coach_retention_curve()
    if not curve.empty and "period" in curve.columns and "pct" in curve.columns:
        fig4 = px.line(
            curve,
            x="period",
            y="pct",
            title="Coach Retention Curve",
            markers=True,
            labels={"pct": "Retention %", "period": "Period"},
        )
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)

        if "coaches" in curve.columns:
            st.dataframe(curve, use_container_width=True, hide_index=True)
    else:
        st.info("No retention curve data available.")
except Exception as e:
    st.warning(f"Could not load retention curve: {e}")

st.markdown("---")

# ── Feature Impact ──
st.subheader("⚡ Feature Impact on Retention")

tab1, tab2 = st.tabs(["Feature Retention Lift", "First Week Activity"])

with tab1:
    try:
        impact = load_feature_retention_impact()
        if (
            not impact.empty
            and "feature" in impact.columns
            and "lift_pp" in impact.columns
        ):
            agg = (
                impact.groupby("feature")
                .agg(
                    avg_lift=("lift_pp", "mean"),
                    avg_retention_used=("retention_if_used", "mean"),
                    avg_retention_not_used=("retention_if_not_used", "mean"),
                )
                .reset_index()
                .sort_values("avg_lift", ascending=False)
            )
            fig_imp = px.bar(
                agg,
                x="feature",
                y="avg_lift",
                title="Average Retention Lift by Feature (pp)",
                labels={"avg_lift": "Lift (pp)", "feature": "Feature"},
                color="avg_lift",
                color_continuous_scale="RdYlGn",
            )
            fig_imp.update_layout(height=400)
            st.plotly_chart(fig_imp, use_container_width=True)
            st.dataframe(agg, use_container_width=True, hide_index=True)
        else:
            st.info("No feature impact data available.")
    except Exception as e:
        st.warning(f"Could not load feature impact: {e}")

with tab2:
    try:
        firstweek = load_firstweek_retention()
        if not firstweek.empty and "active_days_first_week" in firstweek.columns:
            agg_fw = (
                firstweek.groupby("active_days_first_week")
                .agg(
                    avg_retention=("retention_30d_pct", "mean"),
                    total_users=("users", "sum"),
                )
                .reset_index()
            )
            fig_fw = px.bar(
                agg_fw,
                x="active_days_first_week",
                y="avg_retention",
                title="Active Days in Week 1 → 30-Day Retention",
                labels={
                    "avg_retention": "Retention %",
                    "active_days_first_week": "Active Days",
                },
                text="total_users",
            )
            fig_fw.update_layout(height=350)
            st.plotly_chart(fig_fw, use_container_width=True)
        else:
            st.info("No first-week retention data available.")
    except Exception as e:
        st.warning(f"Could not load first-week retention: {e}")

# ── App Health Scores ──
st.markdown("---")
st.subheader("🏥 App Health Scores")

try:
    health = load_app_health_score()
    if not health.empty:
        st.dataframe(health, use_container_width=True, hide_index=True)
    else:
        st.info("No health score data available.")
except Exception as e:
    st.warning(f"Could not load health scores: {e}")

# ── Raw Data ──
with st.expander("📋 View Raw Data"):
    tab_a, tab_b = st.tabs(["Growth Stages", "GMV Timeline"])
    with tab_a:
        st.dataframe(stages, use_container_width=True)
    with tab_b:
        st.dataframe(gmv_timeline, use_container_width=True)
