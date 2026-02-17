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
)
from auth import require_auth, show_admin_panel, logout_button

st.set_page_config(
    page_title="KLIQ Growth Dashboard",
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
st.title("KLIQ Growth Dashboard")
show_admin_panel()
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f"""
    <div style="background:{GREEN}; padding:28px; border-radius:12px; color:{IVORY}; text-align:center;">
        <p style="margin:0; font-size:13px; opacity:0.75; font-weight:600; letter-spacing:0.5px;">NAVIGATE USING THE SIDEBAR</p>
        <h2 style="margin:8px 0; font-size:2.4rem; font-weight:700;">7 Pages</h2>
        <p style="margin:0; font-size:14px; opacity:0.8;">Full growth analytics suite</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""
    <div style="background:{GREEN}; padding:28px; border-radius:12px; color:{IVORY}; text-align:center;">
        <p style="margin:0; font-size:13px; opacity:0.75; font-weight:600; letter-spacing:0.5px;">LIVE FROM BIGQUERY</p>
        <h2 style="margin:8px 0; font-size:2.4rem; font-weight:700;">54 Tables</h2>
        <p style="margin:0; font-size:14px; opacity:0.8;">Real-time data</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""
    <div style="background:{GREEN}; padding:28px; border-radius:12px; color:{IVORY}; text-align:center;">
        <p style="margin:0; font-size:13px; opacity:0.75; font-weight:600; letter-spacing:0.5px;">INTEGRATIONS</p>
        <h2 style="margin:8px 0; font-size:2.4rem; font-weight:700;">Meta + Calendar</h2>
        <p style="margin:0; font-size:14px; opacity:0.8;">Ads & demo call tracking</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("")
st.markdown("### Pages")
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
"""
)
