"""
Page 2 — Activation
Coach activation score: measures whether new apps complete key setup actions
in their first 30 days. Predicts churn risk based on data-driven weights.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    load_activation_score,
    load_coach_onboarding_funnel,
    load_coach_retention_curve,
    load_cohort_retention,
    load_churn_analysis,
    load_app_lookup,
)

st.set_page_config(page_title="Activation — KLIQ", page_icon="🚀", layout="wide")
inject_css()
register_plotly_template()
st.title("Activation & Churn Prediction")
st.markdown("---")

# ── Load Data ──
with st.spinner("Loading activation data..."):
    score_df = load_activation_score()
    apps = load_app_lookup()

app_names = []
if not apps.empty and "application_name" in apps.columns:
    app_names = sorted([n for n in apps["application_name"].dropna().unique() if n])

selected_app = st.sidebar.selectbox(
    "Filter by App", ["All Apps"] + app_names, key="act_app"
)

st.sidebar.markdown("---")
st.sidebar.markdown("**New Apps Time Filter**")
time_filter = st.sidebar.radio(
    "Show apps created in:",
    ["Last 7 days", "Last 14 days", "Last 30 days", "Last 90 days", "All Time"],
    index=2,
    key="act_time",
)
time_days = {
    "Last 7 days": 7,
    "Last 14 days": 14,
    "Last 30 days": 30,
    "Last 90 days": 90,
    "All Time": 99999,
}[time_filter]

# Action columns and their labels/weights
ACTION_CONFIG = {
    "added_profile_image": {"label": "Profile Image", "weight": 10, "icon": "🖼️"},
    "created_module": {"label": "Created Module", "weight": 10, "icon": "📦"},
    "created_livestream": {"label": "Created Livestream", "weight": 10, "icon": "🎥"},
    "created_program": {"label": "Created Program", "weight": 10, "icon": "📋"},
    "previewed_app": {"label": "Previewed App", "weight": 15, "icon": "👁️"},
    "published_app": {"label": "Published App", "weight": 10, "icon": "🚀"},
    "added_blog_content": {"label": "Blog Content", "weight": 10, "icon": "📝"},
    "added_nutrition": {"label": "Nutrition Content", "weight": 10, "icon": "🥗"},
    "posted_community": {"label": "Community Post", "weight": 5, "icon": "💬"},
    "copied_url": {"label": "Copied URL", "weight": 5, "icon": "🔗"},
    "created_1to1": {"label": "1-to-1 Booking", "weight": 5, "icon": "📅"},
}

ACTION_COLS = list(ACTION_CONFIG.keys())


def filter_df(df):
    if selected_app == "All Apps" or df.empty or "application_name" not in df.columns:
        return df
    return df[df["application_name"] == selected_app]


df = filter_df(score_df)

if df.empty:
    st.warning("No activation data available.")
    st.stop()

# ── KPI Cards ──
total_apps = len(df)
active_apps = int(df["is_active"].sum())
churned_apps = total_apps - active_apps
avg_score = df["activation_score"].mean()
avg_actions = df["actions_completed"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Apps", f"{total_apps:,}")
k2.metric("Active (90d)", f"{active_apps:,}", f"{active_apps/total_apps*100:.1f}%")
k3.metric(
    "Churned",
    f"{churned_apps:,}",
    f"{churned_apps/total_apps*100:.1f}%",
    delta_color="inverse",
)
k4.metric("Avg Activation Score", f"{avg_score:.0f}/100")
k5.metric("Avg Actions Done", f"{avg_actions:.1f}/11")

st.markdown("---")

# ── Activation Score vs Churn ──
st.subheader("📊 Activation Score vs Retention")
st.caption(
    "Apps that complete more setup actions in their first 30 days are far more likely to stay active"
)

col1, col2 = st.columns(2)

with col1:
    # Score distribution by active/churned
    score_bins = pd.cut(
        df["activation_score"],
        bins=[-1, 0, 10, 25, 50, 75, 100],
        labels=["0", "1-10", "11-25", "26-50", "51-75", "76-100"],
    )
    df_binned = df.copy()
    df_binned["score_bin"] = score_bins
    df_binned["status"] = df_binned["is_active"].map({1: "Active", 0: "Churned"})

    bin_counts = (
        df_binned.groupby(["score_bin", "status"]).size().reset_index(name="count")
    )
    fig_dist = px.bar(
        bin_counts,
        x="score_bin",
        y="count",
        color="status",
        title="Score Distribution: Active vs Churned",
        labels={"score_bin": "Activation Score", "count": "Apps"},
        barmode="group",
        color_discrete_map={"Active": GREEN, "Churned": ERROR},
    )
    fig_dist.update_layout(height=400)
    st.plotly_chart(fig_dist, use_container_width=True)

with col2:
    # Retention rate by score bucket
    retention_by_score = (
        df_binned.groupby("score_bin")
        .agg(total=("is_active", "count"), active=("is_active", "sum"))
        .reset_index()
    )
    retention_by_score["retention_pct"] = (
        retention_by_score["active"] / retention_by_score["total"] * 100
    ).round(1)

    fig_ret = px.bar(
        retention_by_score,
        x="score_bin",
        y="retention_pct",
        title="Retention Rate by Activation Score",
        labels={"score_bin": "Activation Score", "retention_pct": "Retention %"},
        text="retention_pct",
    )
    fig_ret.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside", marker_color=GREEN
    )
    fig_ret.update_layout(height=400, yaxis_range=[0, 105])
    st.plotly_chart(fig_ret, use_container_width=True)

st.markdown("---")

# ── Action Impact Analysis ──
st.subheader("⚡ Action Impact on Retention")
st.caption(
    "Each action's retention lift: how much more likely an app is to stay active if the coach did this action"
)

impact_data = []
for col, cfg in ACTION_CONFIG.items():
    if col in df.columns:
        did = df[df[col] == 1]
        didnt = df[df[col] == 0]
        did_rate = did["is_active"].mean() * 100 if len(did) > 0 else 0
        didnt_rate = didnt["is_active"].mean() * 100 if len(didnt) > 0 else 0
        lift = did_rate - didnt_rate
        impact_data.append(
            {
                "Action": f"{cfg['icon']} {cfg['label']}",
                "Weight": cfg["weight"],
                "Apps Did It": len(did),
                "Retention If Done": f"{did_rate:.1f}%",
                "Retention If Not": f"{didnt_rate:.1f}%",
                "Lift": f"+{lift:.1f}pp",
                "lift_val": lift,
            }
        )

impact_df = pd.DataFrame(impact_data).sort_values("lift_val", ascending=True)

col1, col2 = st.columns([2, 1])
with col1:
    fig_impact = px.bar(
        impact_df,
        x="lift_val",
        y="Action",
        orientation="h",
        title="Retention Lift by Action (percentage points)",
        labels={"lift_val": "Retention Lift (pp)", "Action": ""},
        text="lift_val",
    )
    fig_impact.update_traces(
        texttemplate="+%{text:.1f}pp", textposition="outside", marker_color=GREEN
    )
    fig_impact.update_layout(height=450)
    st.plotly_chart(fig_impact, use_container_width=True)

with col2:
    st.markdown("**Action Scorecard Weights**")
    display_impact = impact_df[
        ["Action", "Weight", "Apps Did It", "Retention If Done", "Lift"]
    ].copy()
    display_impact = display_impact.sort_values("Weight", ascending=False)
    st.dataframe(display_impact, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Action Completion Rates ──
st.subheader("✅ Action Completion Rates (First 30 Days)")

completion_data = []
for col, cfg in ACTION_CONFIG.items():
    if col in df.columns:
        rate = df[col].mean() * 100
        completion_data.append({"Action": cfg["label"], "Completion %": round(rate, 1)})

comp_df = pd.DataFrame(completion_data).sort_values("Completion %", ascending=True)
fig_comp = px.bar(
    comp_df,
    x="Completion %",
    y="Action",
    orientation="h",
    title="% of Apps Completing Each Action in First 30 Days",
    text="Completion %",
)
fig_comp.update_traces(
    texttemplate="%{text:.1f}%", textposition="outside", marker_color=TANGERINE
)
fig_comp.update_layout(height=400, xaxis_range=[0, 105])
st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("---")

# ── Risk Breakdown ──
st.subheader("🚦 Risk Level Breakdown")

col1, col2 = st.columns(2)
with col1:
    if "risk_level" in df.columns:
        risk_order = ["Critical", "High Risk", "Medium Risk", "Low Risk"]
        risk_counts = (
            df["risk_level"]
            .value_counts()
            .reindex(risk_order, fill_value=0)
            .reset_index()
        )
        risk_counts.columns = ["Risk Level", "Apps"]
        fig_risk = px.pie(
            risk_counts,
            names="Risk Level",
            values="Apps",
            title="Apps by Risk Level",
            color="Risk Level",
            color_discrete_map={
                "Critical": ERROR,
                "High Risk": TANGERINE,
                "Medium Risk": ALPINE,
                "Low Risk": GREEN,
            },
        )
        fig_risk.update_layout(height=400)
        st.plotly_chart(fig_risk, use_container_width=True)

with col2:
    if "risk_level" in df.columns:
        risk_retention = (
            df.groupby("risk_level")
            .agg(
                total=("is_active", "count"),
                active=("is_active", "sum"),
                avg_score=("activation_score", "mean"),
                avg_revenue=("total_revenue_usd", "mean"),
            )
            .reindex(risk_order)
            .reset_index()
        )
        risk_retention["retention_pct"] = (
            risk_retention["active"] / risk_retention["total"] * 100
        ).round(1)
        risk_retention["avg_score"] = risk_retention["avg_score"].round(0)
        risk_retention["avg_revenue"] = risk_retention["avg_revenue"].round(0)
        risk_retention.columns = [
            "Risk Level",
            "Total Apps",
            "Active Apps",
            "Avg Score",
            "Avg Revenue ($)",
            "Retention %",
        ]
        st.markdown("**Risk Level Summary**")
        st.dataframe(risk_retention, use_container_width=True, hide_index=True)

        st.markdown("**Interpretation:**")
        st.markdown(
            """
        - **Critical** (0 actions): Almost certain to churn
        - **High Risk** (1-3 actions): Very likely to churn
        - **Medium Risk** (4-6 actions): Needs nudging to complete setup
        - **Low Risk** (7+ actions): Healthy activation, likely to retain
        """
        )

st.markdown("---")

# ── New Apps Detail (Time-Filtered) ──
st.subheader(f"� New Apps — {time_filter}")
st.caption(
    "All apps created in the selected time period with their activation actions and coach contact email"
)

time_filtered = (
    df[df["app_age_days"] <= time_days].copy()
    if "app_age_days" in df.columns
    else pd.DataFrame()
)

if not time_filtered.empty:
    time_filtered = time_filtered.sort_values("created_date", ascending=False)

    # Summary KPIs for this time period
    tc1, tc2, tc3, tc4 = st.columns(4)
    tc1.metric(f"New Apps ({time_filter})", f"{len(time_filtered):,}")
    critical_count = (
        len(time_filtered[time_filtered["risk_level"] == "Critical"])
        if "risk_level" in time_filtered.columns
        else 0
    )
    high_count = (
        len(time_filtered[time_filtered["risk_level"] == "High Risk"])
        if "risk_level" in time_filtered.columns
        else 0
    )
    tc2.metric("Critical Risk", f"{critical_count:,}", delta_color="inverse")
    tc3.metric("High Risk", f"{high_count:,}", delta_color="inverse")
    avg_s = (
        time_filtered["activation_score"].mean()
        if "activation_score" in time_filtered.columns
        else 0
    )
    tc4.metric("Avg Score", f"{avg_s:.0f}/100")

    # Build display with checkmarks for each action
    display = time_filtered.copy()
    for col, cfg in ACTION_CONFIG.items():
        if col in display.columns:
            display[cfg["label"]] = display[col].map({1: "✅", 0: "❌"})

    # Build missing actions column
    missing_list = []
    for _, row in display.iterrows():
        missing = [
            ACTION_CONFIG[c]["label"]
            for c in ACTION_COLS
            if c in row.index and row[c] == 0
        ]
        missing_list.append(", ".join(missing) if missing else "All done!")
    display["Missing Actions"] = missing_list

    # Select columns for display
    base_cols = [
        "application_name",
        "coach_email",
        "created_date",
        "activation_score",
        "actions_completed",
        "risk_level",
        "is_active",
    ]
    action_labels = [cfg["label"] for cfg in ACTION_CONFIG.values()]
    show_cols = (
        [c for c in base_cols if c in display.columns]
        + [lbl for lbl in action_labels if lbl in display.columns]
        + ["Missing Actions"]
    )

    st.dataframe(
        display[show_cols].rename(
            columns={
                "application_name": "App Name",
                "coach_email": "Coach Email",
                "created_date": "Created",
                "activation_score": "Score",
                "actions_completed": "Actions Done",
                "risk_level": "Risk Level",
                "is_active": "Active?",
            }
        ),
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    # At-risk outreach list (just emails)
    at_risk = time_filtered[time_filtered["risk_level"].isin(["Critical", "High Risk"])]
    if not at_risk.empty and "coach_email" in at_risk.columns:
        emails = at_risk["coach_email"].dropna().unique().tolist()
        if emails:
            with st.expander(
                f"📧 At-Risk Coach Emails for Outreach ({len(emails)} coaches)"
            ):
                st.code("; ".join(emails), language=None)
                st.caption("Copy the above to paste into your email client")
else:
    st.info(f"No apps created in the {time_filter.lower()}.")

st.markdown("---")

# ── Cohort Retention ──
st.subheader("📊 Cohort Retention")

try:
    cohort = load_cohort_retention()
    if (
        not cohort.empty
        and "cohort" in cohort.columns
        and "months_since_join" in cohort.columns
        and "retention_rate" in cohort.columns
    ):
        pivot = cohort.pivot_table(
            index="cohort",
            columns="months_since_join",
            values="retention_rate",
            aggfunc="mean",
        )
        fig_heat = px.imshow(
            pivot.values,
            x=[f"M{int(c)}" for c in pivot.columns],
            y=[str(r) for r in pivot.index],
            color_continuous_scale="RdYlGn",
            title="Retention Rate by Cohort (%)",
            labels={"color": "Retention %"},
            aspect="auto",
            text_auto=".0f",
        )
        fig_heat.update_layout(height=500)
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("No cohort retention data available.")
except Exception as e:
    st.warning(f"Could not load cohort retention: {e}")

st.markdown("---")

# ── Retention Curve ──
st.subheader("📉 Coach Retention Curve")

try:
    curve = load_coach_retention_curve()
    if not curve.empty and "period" in curve.columns and "pct" in curve.columns:
        fig_curve = px.line(
            curve,
            x="period",
            y="pct",
            title="Coach Retention Curve",
            markers=True,
            labels={"pct": "Retention %", "period": "Period"},
        )
        fig_curve.update_layout(height=400)
        st.plotly_chart(fig_curve, use_container_width=True)
    else:
        st.info("No retention curve data available.")
except Exception as e:
    st.warning(f"Could not load retention curve: {e}")

# ── Full Activation Table ──
with st.expander("📋 View Full Activation Score Table"):
    show_cols = [
        "application_name",
        "created_date",
        "app_age_days",
        "activation_score",
        "actions_completed",
        "risk_level",
        "is_active",
        "total_revenue_usd",
        "last_active_date",
    ] + ACTION_COLS
    available = [c for c in show_cols if c in df.columns]
    st.dataframe(df[available], use_container_width=True, hide_index=True)
