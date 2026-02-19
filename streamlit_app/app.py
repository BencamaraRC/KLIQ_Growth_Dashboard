"""
KLIQ Growth Dashboard — Streamlit App
Multi-page dashboard for the KLIQ growth team.
Pulls live data from BigQuery (rcwl-data.powerbi_dashboard).
"""

import streamlit as st
from kliq_ui_kit import (
    inject_css,
    register_plotly_template,
    GREEN,
    DARK,
    IVORY,
    TANGERINE,
    LIME,
    ALPINE,
    BG_CARD,
    NEUTRAL,
    SHADOW_CARD,
    CARD_RADIUS,
    section_header,
)
from auth import require_auth, show_admin_panel, logout_button

st.set_page_config(
    page_title="KLIQ Command Centre",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
register_plotly_template()

# ── Auth Gate ──
require_auth()
logout_button()

# ── Home Page ──
st.title("KLIQ Command Centre")
show_admin_panel()
st.markdown("---")

# ── Hero Cards ──
_hero_card = """
<div style="
    background:{bg}; padding:24px; border-radius:{r}px;
    color:{fg}; text-align:center;
    box-shadow:{shadow};
    transition:all 0.25s cubic-bezier(0.4,0,0.2,1);
">
    <p style="margin:0;font-size:12px;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;opacity:0.7;">{label}</p>
    <h2 style="margin:8px 0;font-size:2rem;font-weight:700;line-height:1.1;">{value}</h2>
    <p style="margin:0;font-size:13px;opacity:0.75;">{desc}</p>
</div>
"""

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        _hero_card.format(
            bg=GREEN,
            fg=IVORY,
            r=CARD_RADIUS,
            shadow=SHADOW_CARD,
            label="Navigate Using The Sidebar",
            value="10 Pages",
            desc="Growth + Outreach",
        ),
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        _hero_card.format(
            bg=GREEN,
            fg=IVORY,
            r=CARD_RADIUS,
            shadow=SHADOW_CARD,
            label="Live From BigQuery",
            value="54 Tables",
            desc="Real-time data",
        ),
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        _hero_card.format(
            bg=GREEN,
            fg=IVORY,
            r=CARD_RADIUS,
            shadow=SHADOW_CARD,
            label="Integrations",
            value="Meta + Apple + Play",
            desc="Ads, analytics & store data",
        ),
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        _hero_card.format(
            bg=TANGERINE,
            fg=DARK,
            r=CARD_RADIUS,
            shadow=SHADOW_CARD,
            label="Prospect Outreach",
            value="Email + SMS",
            desc="Automated sequences",
        ),
        unsafe_allow_html=True,
    )

st.markdown("")

# ── Growth Dashboard Section ──
st.markdown(
    section_header("📊 Growth Dashboard", "Analytics & performance tracking"),
    unsafe_allow_html=True,
)
st.markdown(
    """
| Page | Description |
|------|-------------|
| **1 — Acquisition** | Signups, new customers, country breakdown, website traffic by channel, GA4 sessions, signup funnel with drop-offs, device breakdown |
| **2 — Activation** | Onboarding steps, content created & published, cohort retention, retention curve |
| **3 — Coach Snapshot** | Total GMV, paid to KLIQ, hosting fee, currency, months active, KLIQ fee %, GMV timeline, MAU/DAU, app opens |
| **4 — Coach Deep Dive** | Growth stages, top coaches by GMV, GMV timeline, retention curve, feature impact |
| **5 — App Health** | MAU/DAU, user overview, engagement, subscriptions, device breakdown, user location |
| **6 — GMV Table** | Per-coach monthly GMV revenue, total GMV, avg LTV per app, avg rev per app last month |
| **7 — Leads & Sales** | Meta Ads leads, demo calls, acquisition funnel, revenue, cancellations, weekly data table |
| **8 — Growth Strategy** | Clusters, retention, LTV, paid ad ROI simulator, growth ladder, revenue projections |
| **9 — Feature Adoption** | Per-app feature usage, platform-wide adoption, category breakdown, monthly trends, app vs platform comparison |
"""
)

st.markdown("")

# ── Outreach Section ──
st.markdown(
    section_header("📧 Prospect Outreach", "Email sequences & prospect management"),
    unsafe_allow_html=True,
)
st.markdown(
    """
| Section | Description |
|---------|-------------|
| **10 — Outreach** | Email draft queue, prospect management, sent message history, phone import, cheat sheet generator, BigQuery sync |
"""
)
