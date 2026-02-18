"""
Page 8 — Coach Growth Strategy
Clusters, retention, LTV, paid ad ROI model, and growth ladder.
Combines live BigQuery data with KLIQ's growth services framework.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth, logout_button
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
    POSITIVE,
    NEGATIVE,
    BG_CARD,
    SHADOW_CARD,
    CARD_RADIUS,
    section_header,
)
from data import (
    load_growth_strategy_app_stats,
    load_growth_strategy_monthly,
)

st.set_page_config(page_title="Growth Strategy — KLIQ", page_icon="🚀", layout="wide")
inject_css()
register_plotly_template()
require_auth()
logout_button()
st.title("Coach Growth Strategy")
st.caption("Clusters · Retention · LTV · Paid Ad ROI · Growth Ladder")
st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
#  LOAD DATA
# ═══════════════════════════════════════════════════════════════════
with st.spinner("Loading growth strategy data..."):
    df = load_growth_strategy_app_stats()
    monthly = load_growth_strategy_monthly()

if df.empty:
    st.error("No data available.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════
#  DERIVED COLUMNS
# ═══════════════════════════════════════════════════════════════════
df["kliq_revenue"] = (df["iap_revenue"] * df["kliq_fee_pct"] / 100).round(2)
df["active_months"] = df["active_rev_months"].clip(lower=1)
df["monthly_rev"] = (df["iap_revenue"] / df["active_months"]).round(2)
df["monthly_kliq"] = (df["kliq_revenue"] / df["active_months"]).round(2)
df["total_payments"] = df["purchases"] + df["recurring_payments"]
df["ltv_per_buyer"] = np.where(df["purchases"] > 0, (df["iap_revenue"] / df["purchases"]).round(2), 0)
df["renewal_ratio"] = np.where(df["purchases"] > 0, (df["recurring_payments"] / df["purchases"]).round(1), 0)
df["retention_rate"] = np.where(
    df["new_subscribers"] > 0,
    ((1 - df["cancellations"] / df["new_subscribers"]).clip(0, 1) * 100).round(0),
    0,
)
df["conversion_rate"] = np.where(
    df["new_subscribers"] > 0,
    (df["purchases"] / df["new_subscribers"] * 100).round(1),
    0,
)

# ── Cluster assignment ──
def assign_cluster(row):
    if row["iap_revenue"] >= 5000 and row["renewal_ratio"] >= 1.5 and row["active_months"] >= 6:
        return "PRIME"
    elif row["iap_revenue"] >= 1000 and row["active_months"] >= 3:
        return "GROWTH"
    elif row["iap_revenue"] >= 100 and row["active_months"] >= 3:
        return "EMERGING"
    elif row["iap_revenue"] > 0:
        return "EARLY"
    else:
        return "INACTIVE"

df["cluster"] = df.apply(assign_cluster, axis=1)

CLUSTER_COLORS = {
    "PRIME": "#15803D",
    "GROWTH": "#2563EB",
    "EMERGING": "#D97706",
    "EARLY": "#8A9494",
    "INACTIVE": "#D1D5DB",
}
CLUSTER_EMOJI = {
    "PRIME": "🟢",
    "GROWTH": "🔵",
    "EMERGING": "🟠",
    "EARLY": "⚪",
    "INACTIVE": "⬜",
}
CLUSTER_ORDER = ["PRIME", "GROWTH", "EMERGING", "EARLY", "INACTIVE"]

# Only show revenue-generating apps for most sections
rev_df = df[df["iap_revenue"] > 0].copy()

# ═══════════════════════════════════════════════════════════════════
#  SECTION 1: KPI HERO CARDS
# ═══════════════════════════════════════════════════════════════════
_card = """
<div style="background:{bg};padding:20px;border-radius:{r}px;text-align:center;box-shadow:{shadow};">
    <p style="margin:0;font-size:11px;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;color:{fg};opacity:0.7;">{label}</p>
    <h2 style="margin:6px 0;font-size:1.8rem;font-weight:700;color:{fg};line-height:1.1;">{value}</h2>
    <p style="margin:0;font-size:12px;color:{fg};opacity:0.75;">{desc}</p>
</div>
"""

total_iap = rev_df["iap_revenue"].sum()
total_kliq = rev_df["kliq_revenue"].sum()
total_buyers = rev_df["purchases"].sum()
weighted_ltv = total_iap / total_buyers if total_buyers > 0 else 0
avg_renewal = rev_df.loc[rev_df["purchases"] > 0, "renewal_ratio"].mean()
n_prime = len(rev_df[rev_df["cluster"] == "PRIME"])
n_growth = len(rev_df[rev_df["cluster"] == "GROWTH"])

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(_card.format(bg=GREEN, fg=IVORY, r=CARD_RADIUS, shadow=SHADOW_CARD,
        label="Total IAP Revenue", value=f"${total_iap:,.0f}", desc="Apple + Google (FX-adjusted)"), unsafe_allow_html=True)
with c2:
    st.markdown(_card.format(bg=GREEN, fg=IVORY, r=CARD_RADIUS, shadow=SHADOW_CARD,
        label="KLIQ Revenue", value=f"${total_kliq:,.0f}", desc=f"From {len(rev_df)} apps"), unsafe_allow_html=True)
with c3:
    st.markdown(_card.format(bg=GREEN, fg=IVORY, r=CARD_RADIUS, shadow=SHADOW_CARD,
        label="LTV per Buyer", value=f"${weighted_ltv:,.2f}", desc=f"{total_buyers:,} total purchases"), unsafe_allow_html=True)
with c4:
    st.markdown(_card.format(bg=GREEN, fg=IVORY, r=CARD_RADIUS, shadow=SHADOW_CARD,
        label="Avg Renewals", value=f"{avg_renewal:.1f}x", desc="Per paying user"), unsafe_allow_html=True)
with c5:
    st.markdown(_card.format(bg=GREEN, fg=IVORY, r=CARD_RADIUS, shadow=SHADOW_CARD,
        label="Ad-Ready Apps", value=f"{n_prime + n_growth}", desc=f"{n_prime} Prime + {n_growth} Growth"), unsafe_allow_html=True)

st.markdown("")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 2: STRATEGIC CLUSTERS
# ═══════════════════════════════════════════════════════════════════
st.markdown(section_header("Strategic Clusters", "Apps grouped by revenue, retention, and ad-readiness"), unsafe_allow_html=True)

# Cluster summary table
cluster_summary = []
for cl in CLUSTER_ORDER:
    sub = rev_df[rev_df["cluster"] == cl] if cl != "INACTIVE" else df[df["cluster"] == cl]
    if len(sub) == 0:
        continue
    cluster_summary.append({
        "Cluster": f"{CLUSTER_EMOJI[cl]} {cl}",
        "Apps": len(sub),
        "Total Revenue": sub["iap_revenue"].sum(),
        "KLIQ Revenue": sub["kliq_revenue"].sum(),
        "Avg Monthly Rev": sub["monthly_rev"].mean(),
        "Avg LTV/Buyer": sub.loc[sub["purchases"] > 0, "ltv_per_buyer"].mean() if (sub["purchases"] > 0).any() else 0,
        "Avg Renewal": sub.loc[sub["purchases"] > 0, "renewal_ratio"].mean() if (sub["purchases"] > 0).any() else 0,
        "Avg Retention": sub["retention_rate"].mean(),
    })
cs_df = pd.DataFrame(cluster_summary)

col_l, col_r = st.columns([2, 3])
with col_l:
    # Pie chart
    pie_data = cs_df[cs_df["Total Revenue"] > 0]
    fig_pie = px.pie(
        pie_data, names="Cluster", values="Total Revenue",
        title="Revenue by Cluster",
        color="Cluster",
        color_discrete_map={f"{CLUSTER_EMOJI[c]} {c}": CLUSTER_COLORS[c] for c in CLUSTER_ORDER},
    )
    fig_pie.update_layout(height=350, margin=dict(t=40, b=0))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_r:
    fmt_df = cs_df.copy()
    for col in ["Total Revenue", "KLIQ Revenue", "Avg Monthly Rev", "Avg LTV/Buyer"]:
        fmt_df[col] = fmt_df[col].apply(lambda x: f"${x:,.0f}")
    fmt_df["Avg Renewal"] = fmt_df["Avg Renewal"].apply(lambda x: f"{x:.1f}x" if isinstance(x, (int, float)) else x)
    fmt_df["Avg Retention"] = fmt_df["Avg Retention"].apply(lambda x: f"{x:.0f}%" if isinstance(x, (int, float)) else x)
    st.dataframe(fmt_df, use_container_width=True, hide_index=True)

# Strategy cards per cluster
_strat_card = """
<div style="background:{bg};border-left:4px solid {accent};padding:16px 20px;border-radius:8px;margin-bottom:12px;">
    <div style="font-size:14px;font-weight:700;color:{accent};margin-bottom:6px;">{emoji} {title}</div>
    <div style="font-size:13px;color:#333;line-height:1.6;">{body}</div>
</div>
"""

st.markdown("")
strategies = {
    "PRIME": {
        "title": "PRIME — Scale with Paid Ads",
        "body": "<b>Strategy:</b> Aggressively scale with KLIQ-managed PPC. These apps have proven product-market fit and strong renewals.<br>"
                "<b>Ad Budget:</b> £1,000–2,000/mo per app<br>"
                "<b>KLIQ Model:</b> £49/mo + £5 per new subscriber (hybrid)<br>"
                "<b>Target:</b> 50+ new paying subscribers/month per app",
        "bg": "#DCFCE7",
        "accent": "#15803D",
    },
    "GROWTH": {
        "title": "GROWTH — Accelerate with Moderate Spend",
        "body": "<b>Strategy:</b> Moderate ad spend + funnel optimisation. Good revenue but needs more scale.<br>"
                "<b>Ad Budget:</b> £500–1,000/mo per app<br>"
                "<b>KLIQ Model:</b> £49/mo + £5 per new subscriber<br>"
                "<b>Target:</b> Hit 250 subscribers → unlock brand deals & affiliates",
        "bg": "#DBEAFE",
        "accent": "#2563EB",
    },
    "EMERGING": {
        "title": "EMERGING — Activate Before Spending",
        "body": "<b>Strategy:</b> Fix content & engagement before paid ads. Help coaches build content library, start livestreaming.<br>"
                "<b>Ad Budget:</b> £0–250/mo (retargeting only)<br>"
                "<b>KLIQ Focus:</b> Success coaching, activation checklist, livestream cadence<br>"
                "<b>Target:</b> Graduate to GROWTH cluster within 3 months",
        "bg": "#FEF3C7",
        "accent": "#D97706",
    },
    "EARLY": {
        "title": "EARLY — Onboard Properly",
        "body": "<b>Strategy:</b> Not ready for paid acquisition. Focus on 30/60 day milestones.<br>"
                "<b>Ad Budget:</b> £0<br>"
                "<b>KLIQ Focus:</b> AI Blog Writer, Store in 5 Minutes, Social Share Templates<br>"
                "<b>Target:</b> First 50 paying users via organic",
        "bg": "#F3F4F6",
        "accent": "#6B7280",
    },
}

cols = st.columns(2)
for i, (cl, s) in enumerate(strategies.items()):
    with cols[i % 2]:
        st.markdown(_strat_card.format(emoji=CLUSTER_EMOJI[cl], **s), unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 3: APP PORTFOLIO TABLE
# ═══════════════════════════════════════════════════════════════════
st.markdown(section_header("App Portfolio", "All revenue-generating apps with key metrics"), unsafe_allow_html=True)

display_df = rev_df[[
    "app", "cluster", "iap_revenue", "kliq_revenue", "kliq_fee_pct",
    "active_months", "monthly_rev", "purchases", "recurring_payments",
    "renewal_ratio", "ltv_per_buyer", "new_subscribers", "retention_rate",
    "livestreams", "workouts", "community_posts",
]].copy()
display_df = display_df.sort_values("iap_revenue", ascending=False)
display_df.columns = [
    "App", "Cluster", "IAP Revenue", "KLIQ Revenue", "KLIQ %",
    "Active Mo", "Monthly Rev", "Purchases", "Recurring",
    "Renewal Ratio", "LTV/Buyer", "Subscribers", "Retention %",
    "Livestreams", "Workouts", "Community Posts",
]

# Format
for col in ["IAP Revenue", "KLIQ Revenue", "Monthly Rev", "LTV/Buyer"]:
    display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}")
display_df["KLIQ %"] = display_df["KLIQ %"].apply(lambda x: f"{x:.1f}%")
display_df["Renewal Ratio"] = display_df["Renewal Ratio"].apply(lambda x: f"{x:.1f}x")
display_df["Retention %"] = display_df["Retention %"].apply(lambda x: f"{x:.0f}%")

st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 4: LTV & UNIT ECONOMICS
# ═══════════════════════════════════════════════════════════════════
st.markdown(section_header("Unit Economics & LTV", "Revenue per paying user and renewal behaviour"), unsafe_allow_html=True)

paying_apps = rev_df[rev_df["purchases"] >= 5].copy().sort_values("iap_revenue", ascending=False)

col_l, col_r = st.columns(2)

with col_l:
    fig_ltv = px.bar(
        paying_apps.head(15),
        x="app", y="ltv_per_buyer",
        title="LTV per Paying User (Top 15 Apps)",
        labels={"ltv_per_buyer": "LTV ($)", "app": ""},
        color="cluster",
        color_discrete_map=CLUSTER_COLORS,
    )
    fig_ltv.update_layout(height=400, xaxis_tickangle=-45, showlegend=True)
    st.plotly_chart(fig_ltv, use_container_width=True)

with col_r:
    fig_renew = px.scatter(
        paying_apps,
        x="renewal_ratio", y="ltv_per_buyer",
        size="iap_revenue", color="cluster",
        hover_name="app",
        title="Renewal Ratio vs LTV per Buyer",
        labels={"renewal_ratio": "Renewals per Buyer", "ltv_per_buyer": "LTV ($)"},
        color_discrete_map=CLUSTER_COLORS,
    )
    fig_renew.update_layout(height=400)
    st.plotly_chart(fig_renew, use_container_width=True)

# Platform-wide unit economics
st.markdown("")
ue_col1, ue_col2, ue_col3, ue_col4 = st.columns(4)
total_recurring = rev_df["recurring_payments"].sum()
avg_renewals_all = total_recurring / total_buyers if total_buyers > 0 else 0
total_subs = rev_df["new_subscribers"].sum()
conversion = total_buyers / total_subs * 100 if total_subs > 0 else 0

with ue_col1:
    st.metric("Avg Revenue per Purchase", f"${total_iap / total_buyers:,.2f}" if total_buyers > 0 else "$0")
with ue_col2:
    st.metric("Platform Avg Renewals", f"{avg_renewals_all:.1f}x")
with ue_col3:
    st.metric("Purchase Conversion", f"{conversion:.1f}%", help="Purchases / Free Subscribers")
with ue_col4:
    st.metric("Total Recurring Payments", f"{total_recurring:,}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 5: ENGAGEMENT PATTERNS BY CLUSTER
# ═══════════════════════════════════════════════════════════════════
st.markdown(section_header("Engagement Patterns", "What separates successful apps from the rest"), unsafe_allow_html=True)

eng_metrics = ["livestreams", "live_joins", "workouts", "community_posts", "modules_published", "programs_published"]
eng_labels = ["Livestreams", "Live Joins", "Workouts", "Community Posts", "Modules", "Programs"]

eng_data = []
for cl in ["PRIME", "GROWTH", "EMERGING", "EARLY"]:
    sub = rev_df[rev_df["cluster"] == cl]
    if len(sub) == 0:
        continue
    months = sub["event_months"].clip(lower=1)
    for metric, label in zip(eng_metrics, eng_labels):
        avg_per_month = (sub[metric] / months).mean()
        eng_data.append({"Cluster": cl, "Metric": label, "Avg/Month/App": round(avg_per_month, 1)})

eng_df = pd.DataFrame(eng_data)
if not eng_df.empty:
    fig_eng = px.bar(
        eng_df, x="Metric", y="Avg/Month/App", color="Cluster",
        barmode="group", title="Monthly Engagement per App by Cluster",
        color_discrete_map=CLUSTER_COLORS,
    )
    fig_eng.update_layout(height=400)
    st.plotly_chart(fig_eng, use_container_width=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 6: SUBSCRIBER RETENTION FLOW
# ═══════════════════════════════════════════════════════════════════
st.markdown(section_header("Subscriber Retention", "Net subscriber flow over time for revenue apps"), unsafe_allow_html=True)

if not monthly.empty:
    rev_apps_list = rev_df["app"].unique()
    monthly_rev_apps = monthly[monthly["app"].isin(rev_apps_list)]
    sub_flow = monthly_rev_apps.groupby("month").agg(
        new_subs=("new_subs", "sum"),
        cancels=("cancels", "sum"),
    ).reset_index().sort_values("month")

    sub_flow["net"] = sub_flow["new_subs"] - sub_flow["cancels"]
    sub_flow["cumulative_net"] = sub_flow["net"].cumsum()

    col_l, col_r = st.columns(2)
    with col_l:
        fig_sub = go.Figure()
        fig_sub.add_trace(go.Bar(x=sub_flow["month"], y=sub_flow["new_subs"], name="New Subs", marker_color=POSITIVE))
        fig_sub.add_trace(go.Bar(x=sub_flow["month"], y=-sub_flow["cancels"], name="Cancellations", marker_color=NEGATIVE))
        fig_sub.update_layout(title="Monthly Subscriber Flow", barmode="relative", height=400,
                              yaxis_title="Subscribers", xaxis_title="")
        st.plotly_chart(fig_sub, use_container_width=True)

    with col_r:
        fig_cum = px.area(
            sub_flow, x="month", y="cumulative_net",
            title="Cumulative Net Subscribers",
            labels={"cumulative_net": "Net Subscribers", "month": ""},
        )
        fig_cum.update_layout(height=400)
        fig_cum.update_traces(line_color=GREEN, fillcolor="rgba(28,56,56,0.15)")
        st.plotly_chart(fig_cum, use_container_width=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 7: PAID AD ROI SIMULATOR
# ═══════════════════════════════════════════════════════════════════
st.markdown(section_header("Paid Ad ROI Simulator", "Model KLIQ-managed PPC economics"), unsafe_allow_html=True)

st.markdown("""
<div style="background:#F0FDF4;border-left:4px solid #15803D;padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:13px;">
    <b>How it works:</b> KLIQ manages Meta/TikTok ads on behalf of coaches. The coach sets a monthly ad budget.
    KLIQ charges a hybrid fee: <b>£49/month base + £5 per new subscriber acquired</b>.
    Each new subscriber generates LTV over 12 months through renewals.
</div>
""", unsafe_allow_html=True)

sim_col1, sim_col2, sim_col3 = st.columns(3)
with sim_col1:
    ad_spend = st.slider("Monthly Ad Spend (£)", 200, 5000, 1000, 100, key="ad_spend")
with sim_col2:
    cpa = st.slider("Cost per Subscriber (£)", 2, 25, 8, 1, key="cpa",
                     help="Industry benchmark: £5-15 for fitness apps")
with sim_col3:
    kliq_total_pct = st.slider("KLIQ Total Take (%)", 5, 30, 15, 1, key="kliq_pct",
                               help="KLIQ % fee + ad management fee combined")

# Use actual platform LTV
new_subs = ad_spend / cpa
platform_fee_pct = 30
coach_net_pct = 100 - platform_fee_pct - kliq_total_pct

# 12-month LTV model with retention decay
retention_curve = [1.0, 0.85, 0.72, 0.65, 0.58, 0.52, 0.47, 0.43, 0.40, 0.37, 0.35, 0.33]
avg_monthly_price = weighted_ltv / (1 + avg_renewal) if avg_renewal > 0 else weighted_ltv / 4

ltv_12m = sum(avg_monthly_price * r for r in retention_curve)
kliq_ltv = ltv_12m * kliq_total_pct / 100
coach_ltv = ltv_12m * coach_net_pct / 100

# Monthly new cohort economics
monthly_new_gmv = new_subs * ltv_12m / 12
monthly_kliq_from_cohort = new_subs * kliq_ltv / 12
monthly_coach_from_cohort = new_subs * coach_ltv / 12
kliq_mgmt_fee = 49 + 5 * new_subs  # hybrid model
kliq_total_monthly = monthly_kliq_from_cohort + kliq_mgmt_fee
kliq_net = kliq_total_monthly - ad_spend
coach_net_monthly = monthly_coach_from_cohort

# Results
r1, r2, r3, r4 = st.columns(4)
with r1:
    st.metric("New Subscribers/Month", f"{new_subs:.0f}")
with r2:
    st.metric("12-Month LTV/Sub", f"${ltv_12m:,.2f}")
with r3:
    color = "normal" if kliq_net >= 0 else "inverse"
    st.metric("KLIQ Net Monthly", f"${kliq_net:,.0f}", delta=f"{'Profitable' if kliq_net >= 0 else 'Loss'}", delta_color=color)
with r4:
    st.metric("Coach Net Monthly", f"${coach_net_monthly:,.0f}")

# Detailed breakdown
st.markdown("")
with st.expander("Detailed ROI Breakdown", expanded=True):
    breakdown_data = {
        "Metric": [
            "New subscribers acquired",
            "12-month LTV per subscriber",
            "Monthly GMV from cohort",
            f"Platform fee ({platform_fee_pct}%)",
            f"KLIQ % revenue ({kliq_total_pct}%)",
            "KLIQ management fee (£49 + £5/sub)",
            "KLIQ total monthly income",
            "Ad spend",
            "KLIQ net (income - ad spend)",
            f"Coach payout ({coach_net_pct}%)",
            "Break-even CPA for KLIQ",
            "Break-even CPA for Coach",
        ],
        "Value": [
            f"{new_subs:.0f}",
            f"${ltv_12m:,.2f}",
            f"${monthly_new_gmv:,.0f}",
            f"${monthly_new_gmv * platform_fee_pct / 100:,.0f}",
            f"${monthly_kliq_from_cohort:,.0f}",
            f"${kliq_mgmt_fee:,.0f}",
            f"${kliq_total_monthly:,.0f}",
            f"${ad_spend:,.0f}",
            f"${kliq_net:,.0f}",
            f"${coach_net_monthly:,.0f}",
            f"${kliq_ltv + (49 + 5) / 1:,.2f}",  # per-sub break-even
            f"${coach_ltv:,.2f}",
        ],
    }
    st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)

# Scenario comparison chart
st.markdown("")
st.markdown("**Scenario Comparison: KLIQ Net by CPA and Ad Spend**")
scenarios = []
for spend in [500, 1000, 2000, 3000, 5000]:
    for c in [3, 5, 8, 12, 15, 20]:
        subs = spend / c
        m_gmv = subs * ltv_12m / 12
        m_kliq = m_gmv * kliq_total_pct / 100 + 49 + 5 * subs
        net = m_kliq - spend
        scenarios.append({"Ad Spend": f"£{spend:,}", "CPA (£)": c, "KLIQ Net ($/mo)": round(net, 0), "New Subs": round(subs, 0)})

scen_df = pd.DataFrame(scenarios)
fig_scen = px.line(
    scen_df, x="CPA (£)", y="KLIQ Net ($/mo)", color="Ad Spend",
    title="KLIQ Net Monthly Revenue by CPA",
    markers=True,
)
fig_scen.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Break-even")
fig_scen.update_layout(height=400)
st.plotly_chart(fig_scen, use_container_width=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 8: GROWTH LADDER
# ═══════════════════════════════════════════════════════════════════
st.markdown(section_header("Growth Ladder", "The path from activation to scale"), unsafe_allow_html=True)

ladder_html = """
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
    <div style="background:#F0FDF4;border:2px solid #15803D;border-radius:12px;padding:20px;">
        <h3 style="color:#15803D;margin:0 0 8px;font-size:15px;">STAGE 4: SCALE (1,000+ subs)</h3>
        <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.8;color:#333;">
            <li>White-label content licensing</li>
            <li>Premium brand deals (managed by KLIQ)</li>
            <li>Cross-promotion network</li>
            <li>KLIQ Creator Fund investment</li>
        </ul>
    </div>
    <div style="background:#DBEAFE;border:2px solid #2563EB;border-radius:12px;padding:20px;">
        <h3 style="color:#2563EB;margin:0 0 8px;font-size:15px;">STAGE 3: MONETISE (250+ subs)</h3>
        <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.8;color:#333;">
            <li>KLIQ Affiliate Marketplace</li>
            <li>Content licensing deals</li>
            <li>Brand partnership introductions</li>
            <li>Premium Coach Badge</li>
        </ul>
    </div>
    <div style="background:#FEF3C7;border:2px solid #D97706;border-radius:12px;padding:20px;">
        <h3 style="color:#D97706;margin:0 0 8px;font-size:15px;">STAGE 2: GROW (50–250 subs)</h3>
        <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.8;color:#333;">
            <li>KLIQ Managed PPC (£49/mo + £5/sub)</li>
            <li>Social media growth toolkit</li>
            <li>Referral program</li>
            <li>Target: Hit 250 = "Brand Ready"</li>
        </ul>
    </div>
    <div style="background:#F3F4F6;border:2px solid #9CA3AF;border-radius:12px;padding:20px;">
        <h3 style="color:#6B7280;margin:0 0 8px;font-size:15px;">STAGE 1: LAUNCH (0–50 subs)</h3>
        <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.8;color:#333;">
            <li>AI Blog Writer + Activation Checklist</li>
            <li>Store in 5 Minutes</li>
            <li>Social Share Templates</li>
            <li>Pricing Benchmarks</li>
        </ul>
    </div>
</div>
"""
st.markdown(ladder_html, unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 9: REVENUE PROJECTIONS
# ═══════════════════════════════════════════════════════════════════
st.markdown(section_header("Revenue Projections", "New KLIQ revenue streams from growth services"), unsafe_allow_html=True)

proj_data = {
    "Service": [
        "Managed PPC (hybrid fee)",
        "Affiliate Marketplace (10-20% of commissions)",
        "Brand Deals (15% agency fee)",
        "Content Licensing (15-25% platform fee)",
        "Creator Fund (25% rev share for 12mo)",
    ],
    "Year 1 Est.": ["£30K", "£6K", "£15K", "£10K", "£5K"],
    "Year 2 Est.": ["£120K", "£36K", "£60K", "£50K", "£30K"],
    "Coaches Needed": ["50", "50", "21 (250+ subs)", "10", "5-10"],
    "Status": ["Ready to pilot", "Build needed", "Outreach ready", "Build needed", "Ready to pilot"],
}
proj_df = pd.DataFrame(proj_data)
st.dataframe(proj_df, use_container_width=True, hide_index=True)

# Total projections
p1, p2, p3 = st.columns(3)
with p1:
    st.metric("Year 1 New Revenue", "£66K", help="From growth services only, on top of existing hosting + app fees")
with p2:
    st.metric("Year 2 New Revenue", "£296K")
with p3:
    st.metric("Current KLIQ IAP Revenue", f"${total_kliq:,.0f}", help="From existing KLIQ % fees on IAP")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
#  SECTION 10: KEY TARGETS
# ═══════════════════════════════════════════════════════════════════
st.markdown(section_header("Key Targets", "Milestones to track"), unsafe_allow_html=True)

targets = {
    "Metric": [
        "Coaches with any revenue",
        "Coaches at 250+ subscribers",
        "Coaches at 1,000+ subscribers",
        "Average coach MRR (top 25)",
        "Platform total GMV/month",
        "PPC cost per subscriber",
        "PPC coaches active",
        "Affiliate marketplace brands",
        "Brand deals closed",
    ],
    "Current": [
        f"{len(rev_df)}",
        "21",
        "12",
        "£432",
        "~£12K",
        "N/A",
        "0",
        "0",
        "0",
    ],
    "6-Month Target": [
        "50",
        "35",
        "18",
        "£600",
        "£25K",
        "<£25",
        "50",
        "25",
        "10",
    ],
    "12-Month Target": [
        "100",
        "50",
        "25",
        "£1,000",
        "£50K",
        "<£15",
        "200",
        "50",
        "25",
    ],
}
st.dataframe(pd.DataFrame(targets), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════
#  RAW DATA
# ═══════════════════════════════════════════════════════════════════
with st.expander("📋 View Raw Data"):
    tab_a, tab_b = st.tabs(["App Stats", "Monthly Data"])
    with tab_a:
        st.dataframe(df, use_container_width=True)
    with tab_b:
        st.dataframe(monthly.head(500), use_container_width=True)
