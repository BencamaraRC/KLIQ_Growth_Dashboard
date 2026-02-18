"""
KLIQ In-App Purchase Revenue Dashboard
Standalone Streamlit app — NOT part of the main KLIQ Growth Dashboard.

Shows month-by-month breakdown of Apple App Store & Google Play revenue per app:
  • Sales (customer price)
  • Proceeds (after platform fee)
  • Platform fee %
  • KLIQ fee %
  • Invoice owed to KLIQ

Data sources (BigQuery):
  - d1_appstore_sales        → raw Apple daily sales
  - d1_inapp_products        → SKU → app name mapping
  - d1_app_fee_lookup        → KLIQ fee % per app
  - d1_three_source_revenue  → Google Play aggregated data
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from google.cloud import bigquery

# ── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KLIQ · IAP Revenue",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

JOB_PROJECT = "rcwl-development"
DATA_PROJECT = "rcwl-data"
DATASET = "powerbi_dashboard"

# Tokens (matching KLIQ UI Kit v2.0)
GREEN = "#1C3838"
DARK = "#021111"
IVORY = "#FFFDFA"
TANGERINE = "#FF9F88"
LIME = "#DEFE9C"
ALPINE = "#9CF0FF"
ERROR = "#E85D4A"
NEUTRAL = "#8A9494"
BG_CARD = "#FFFFFF"
SHADOW_CARD = "0 2px 8px rgba(2,17,17,.06)"

APPLE_COLOR = "#007AFF"
GOOGLE_COLOR = "#34A853"
KLIQ_COLOR = GREEN

# Platform fee rates
APPLE_FEE_PCT = 30.0  # Apple takes 30% (or 15% for small business program)
GOOGLE_FEE_PCT = 30.0  # Google takes 30% (or 15% for first $1M)

# ── Styling ─────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background: {IVORY}; }}
    section[data-testid="stSidebar"] {{ background: {GREEN}; }}
    section[data-testid="stSidebar"] * {{ color: {IVORY} !important; }}
    .metric-card {{
        background: {BG_CARD};
        border-radius: 16px;
        padding: 22px 24px 18px;
        box-shadow: {SHADOW_CARD};
        text-align: center;
    }}
    .metric-card .label {{ font-size: 12px; font-weight: 600; color: {NEUTRAL}; text-transform: uppercase; letter-spacing: .5px; }}
    .metric-card .value {{ font-size: 28px; font-weight: 700; color: {DARK}; margin-top: 4px; }}
    .metric-card .sub {{ font-size: 12px; color: {NEUTRAL}; margin-top: 2px; }}
    .section-hdr {{ font-size: 15px; font-weight: 700; color: {DARK}; margin: 32px 0 12px; padding-bottom: 8px; border-bottom: 2px solid {GREEN}; }}
    div[data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden; box-shadow: {SHADOW_CARD}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ── BigQuery Client ─────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _key = os.path.join(_root, "rcwl-development-0c013e9b5c2b.json")
    key_path = os.environ.get("GCP_SERVICE_ACCOUNT_KEY", "") or (
        _key if os.path.exists(_key) else ""
    )
    if key_path and os.path.exists(key_path):
        creds = service_account.Credentials.from_service_account_file(key_path)
    else:
        import google.auth

        creds, _ = google.auth.default()
    return bigquery.Client(credentials=creds, project=JOB_PROJECT, location="EU")


def T(name):
    return f"`{DATA_PROJECT}.{DATASET}.{name}`"


@st.cache_data(ttl=600)
def run_query(sql):
    return get_client().query(sql).to_dataframe()


# ── Data Loading ────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_apple_monthly():
    """
    Aggregate raw Apple sales by app and month.
    Uses d1_inapp_products to map SKU → application_name.
    Converts local-currency prices to USD using approximate FX rates.
    """
    sql = f"""
    WITH fx_rates AS (
        SELECT currency, rate FROM UNNEST([
            STRUCT('USD' AS currency, 1.0 AS rate),
            STRUCT('GBP', 1.27),
            STRUCT('EUR', 1.08),
            STRUCT('AUD', 0.64),
            STRUCT('CAD', 0.72),
            STRUCT('CHF', 1.13),
            STRUCT('DKK', 0.145),
            STRUCT('NOK', 0.093),
            STRUCT('SEK', 0.095),
            STRUCT('NZD', 0.60),
            STRUCT('SGD', 0.75),
            STRUCT('HUF', 0.0027),
            STRUCT('CLP', 0.00105),
            STRUCT('COP', 0.00024),
            STRUCT('CZK', 0.042),
            STRUCT('PLN', 0.25),
            STRUCT('BRL', 0.19),
            STRUCT('MXN', 0.055),
            STRUCT('TRY', 0.031),
            STRUCT('RUB', 0.011),
            STRUCT('ILS', 0.28),
            STRUCT('SAR', 0.267),
            STRUCT('AED', 0.272),
            STRUCT('INR', 0.012),
            STRUCT('ZAR', 0.054),
            STRUCT('RON', 0.22)
        ])
    ),
    sku_map AS (
        SELECT DISTINCT product_id, application_name
        FROM {T('d1_inapp_products')}
    ),
    sales AS (
        SELECT
            s.sku,
            s.report_date,
            SAFE_CAST(s.units AS INT64) AS units,
            SAFE_CAST(s.customer_price AS FLOAT64) AS customer_price,
            SAFE_CAST(s.developer_proceeds AS FLOAT64) AS developer_proceeds,
            s.customer_currency
        FROM {T('d1_appstore_sales')} s
        WHERE s.product_type_identifier IN ('IA1', 'IAY')
    ),
    joined AS (
        SELECT
            COALESCE(m.application_name, 'Unknown') AS application_name,
            FORMAT_DATE("%Y-%m", s.report_date) AS month,
            s.units,
            s.customer_price * COALESCE(fx.rate, 1.0) AS customer_price_usd,
            s.developer_proceeds * COALESCE(fx.rate, 1.0) AS developer_proceeds_usd,
            s.customer_currency
        FROM sales s
        LEFT JOIN sku_map m ON s.sku = m.product_id
        LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
    )
    SELECT
        application_name,
        month,
        SUM(units) AS total_units,
        ROUND(SUM(customer_price_usd * units), 2) AS sales,
        ROUND(SUM(developer_proceeds_usd * units), 2) AS proceeds
    FROM joined
    WHERE customer_price_usd > 0
    GROUP BY application_name, month
    ORDER BY application_name, month
    """
    return run_query(sql)


@st.cache_data(ttl=600)
def load_google_monthly():
    """Google Play monthly data.

    purchase_success events don't carry dollar amounts, so we price each
    event using the matching Apple App Store SKU average price.  Where no
    Apple match exists we fall back to the overall iOS avg revenue per
    purchase.  Google takes the same 30 % commission as Apple, so
    proceeds = sales × 0.70.
    """
    sql = f"""
    WITH fx_rates AS (
        SELECT currency, rate FROM UNNEST([
            STRUCT('USD' AS currency, 1.0 AS rate),
            STRUCT('GBP', 1.27), STRUCT('EUR', 1.08), STRUCT('AUD', 0.64),
            STRUCT('CAD', 0.72), STRUCT('CHF', 1.13), STRUCT('DKK', 0.145),
            STRUCT('NOK', 0.093), STRUCT('SEK', 0.095), STRUCT('NZD', 0.60),
            STRUCT('SGD', 0.75), STRUCT('HUF', 0.0027), STRUCT('CLP', 0.00105),
            STRUCT('COP', 0.00024), STRUCT('CZK', 0.042), STRUCT('PLN', 0.25),
            STRUCT('BRL', 0.19), STRUCT('MXN', 0.055), STRUCT('TRY', 0.031),
            STRUCT('RUB', 0.011), STRUCT('ILS', 0.28), STRUCT('SAR', 0.267),
            STRUCT('AED', 0.272), STRUCT('INR', 0.012), STRUCT('ZAR', 0.054),
            STRUCT('RON', 0.22)
        ])
    ),
    apple_sku_prices AS (
        SELECT
            sku,
            ROUND(AVG(SAFE_CAST(customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0)), 2) AS avg_price
        FROM {T('d1_appstore_sales')} s
        LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
        WHERE s.product_type_identifier IN ('IA1', 'IAY')
          AND SAFE_CAST(customer_price AS FLOAT64) > 0
        GROUP BY sku
    ),
    ios_avg AS (
        SELECT ROUND(AVG(SAFE_CAST(customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0)), 2) AS fallback_price
        FROM {T('d1_appstore_sales')} s
        LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
        WHERE s.product_type_identifier IN ('IA1', 'IAY')
          AND SAFE_CAST(customer_price AS FLOAT64) > 0
    ),
    gplay_events AS (
        SELECT
            a.application_name,
            DATE_TRUNC(DATE(e.event_date), MONTH) AS month_dt,
            JSON_VALUE(e.data, '$.in_app_product_id') AS product_id
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a
            ON e.application_id = a.id
        WHERE e.event_name = 'purchase_success'
    )
    SELECT
        g.application_name,
        FORMAT_DATE("%Y-%m", g.month_dt) AS month,
        COUNT(*) AS total_units,
        ROUND(SUM(COALESCE(ap.avg_price, iavg.fallback_price)), 2) AS sales,
        ROUND(SUM(COALESCE(ap.avg_price, iavg.fallback_price)) * 0.70, 2) AS proceeds
    FROM gplay_events g
    LEFT JOIN apple_sku_prices ap ON g.product_id = ap.sku
    CROSS JOIN ios_avg iavg
    WHERE g.application_name IS NOT NULL
    GROUP BY g.application_name, g.month_dt
    ORDER BY g.application_name, month
    """
    return run_query(sql)


@st.cache_data(ttl=600)
def load_fee_lookup():
    """KLIQ fee % per app."""
    sql = f"SELECT application_name, kliq_fee_pct FROM {T('d1_app_fee_lookup')}"
    return run_query(sql)


# ── Helpers ─────────────────────────────────────────────────────────────────
def metric_card(label, value, sub=""):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="metric-card"><div class="label">{label}</div>'
        f'<div class="value">{value}</div>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def section(title):
    st.markdown(f'<div class="section-hdr">{title}</div>', unsafe_allow_html=True)


def fmt_currency(val, prefix="$"):
    if pd.isna(val) or val == 0:
        return f"{prefix}0.00"
    return f"{prefix}{val:,.2f}"


def compute_breakdown(df_platform, fee_lookup, platform_fee_pct, platform_name):
    """
    Given monthly platform data (application_name, month, sales, proceeds),
    compute the full breakdown:
      - Platform Fee  = Sales × platform_fee_pct (e.g. 30%)
      - Proceeds      = Sales − Platform Fee
      - KLIQ Fee      = Sales × KLIQ %  (KLIQ's cut of gross sales)
      - Payout        = Sales − Platform Fee − KLIQ Fee
    """
    if df_platform.empty:
        return pd.DataFrame()

    df = df_platform.merge(fee_lookup, on="application_name", how="left")

    # Platform fee (Apple/Google 30%)
    df["platform_fee_pct"] = platform_fee_pct
    df["platform_fee"] = (df["sales"] * platform_fee_pct / 100).round(2)
    df["proceeds"] = (df["sales"] - df["platform_fee"]).round(2)

    # KLIQ fee on gross sales
    df["kliq_fee_pct"] = df["kliq_fee_pct"].fillna(0)
    df["kliq_fee"] = (df["sales"] * df["kliq_fee_pct"] / 100).round(2)

    # Payout = Sales - Platform Fee - KLIQ Fee
    df["payout"] = (df["sales"] - df["platform_fee"] - df["kliq_fee"]).round(2)

    df["platform"] = platform_name
    return df


# ── Load Data ───────────────────────────────────────────────────────────────
try:
    apple_raw = load_apple_monthly()
    google_raw = load_google_monthly()
    fee_lookup = load_fee_lookup()
except Exception as e:
    st.error(f"Failed to load data from BigQuery: {e}")
    st.stop()

apple = compute_breakdown(apple_raw, fee_lookup, APPLE_FEE_PCT, "Apple")
google = compute_breakdown(google_raw, fee_lookup, GOOGLE_FEE_PCT, "Google")
combined = pd.concat([apple, google], ignore_index=True)

# ── Sidebar Filters ─────────────────────────────────────────────────────────
st.sidebar.markdown("## 💰 IAP Revenue")
st.sidebar.markdown("---")

all_apps = sorted(combined["application_name"].unique()) if not combined.empty else []
all_months = sorted(combined["month"].unique()) if not combined.empty else []

selected_apps = st.sidebar.multiselect(
    "Filter by App",
    options=all_apps,
    default=[],
    help="Leave empty to show all apps",
)

if all_months:
    month_range = st.sidebar.select_slider(
        "Month Range",
        options=all_months,
        value=(all_months[0], all_months[-1]),
    )
else:
    month_range = (None, None)

platform_filter = st.sidebar.radio("Platform", ["All", "Apple", "Google"], index=0)

# Apply filters
df = combined.copy()
if selected_apps:
    df = df[df["application_name"].isin(selected_apps)]
if month_range[0] and month_range[1]:
    df = df[(df["month"] >= month_range[0]) & (df["month"] <= month_range[1])]
if platform_filter != "All":
    df = df[df["platform"] == platform_filter]

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="text-align:center; padding:24px 0 8px;">
        <h1 style="font-size:22px; font-weight:700; color:{DARK}; margin:0;">
            KLIQ · In-App Purchase Revenue
        </h1>
        <p style="color:{NEUTRAL}; font-size:13px; margin-top:6px;">
            Apple & Google Play · Month-by-Month Breakdown
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── KPI Cards ───────────────────────────────────────────────────────────────
if not df.empty:
    total_sales = df["sales"].sum()
    total_platform_fee = df["platform_fee"].sum()
    total_proceeds = df["proceeds"].sum()
    total_kliq_fee = df["kliq_fee"].sum()
    total_payout = df["payout"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("Total Sales", fmt_currency(total_sales), "Gross sales")
    with c2:
        metric_card(
            "Platform Fees", fmt_currency(total_platform_fee), "Apple/Google 30%"
        )
    with c3:
        metric_card(
            "Total Proceeds", fmt_currency(total_proceeds), "After platform fee"
        )
    with c4:
        metric_card(
            "KLIQ Fee Total", fmt_currency(total_kliq_fee), "KLIQ % of gross sales"
        )
    with c5:
        metric_card("Total Payout", fmt_currency(total_payout), "Sales − fees")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Monthly Trend Chart ─────────────────────────────────────────────────
    section("Monthly Revenue Trend")

    monthly_agg = (
        df.groupby(["month", "platform"])
        .agg(
            sales=("sales", "sum"),
            proceeds=("proceeds", "sum"),
            kliq_fee=("kliq_fee", "sum"),
        )
        .reset_index()
        .sort_values("month")
    )

    fig = go.Figure()
    color_map = {"Apple": APPLE_COLOR, "Google": GOOGLE_COLOR}

    for platform in monthly_agg["platform"].unique():
        pdata = monthly_agg[monthly_agg["platform"] == platform]
        fig.add_trace(
            go.Bar(
                x=pdata["month"],
                y=pdata["sales"],
                name=f"{platform} Sales",
                marker_color=color_map.get(platform, NEUTRAL),
                opacity=0.85,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=pdata["month"],
                y=pdata["kliq_fee"],
                name=f"{platform} KLIQ Fee",
                mode="lines+markers",
                line=dict(color=TANGERINE, width=2),
                marker=dict(size=6),
            )
        )

    fig.update_layout(
        barmode="stack",
        plot_bgcolor=IVORY,
        paper_bgcolor=IVORY,
        font=dict(family="Inter", color=DARK),
        height=380,
        margin=dict(l=40, r=20, t=30, b=40),
        legend=dict(orientation="h", y=-0.15),
        yaxis=dict(gridcolor="#E8E8E8", title="USD"),
        xaxis=dict(title=""),
    )
    st.plotly_chart(fig, use_container_width=True, key="monthly_trend")

    # ── Month-by-Month Breakdown Table ──────────────────────────────────────
    section("Month-by-Month Breakdown")

    # Pivot: one row per app per month, Apple & Google as separate column groups
    pivot_cols = [
        "sales",
        "platform_fee",
        "proceeds",
        "kliq_fee_pct",
        "kliq_fee",
        "payout",
    ]

    apple_df = df[df["platform"] == "Apple"][
        ["application_name", "month"] + pivot_cols
    ].copy()
    apple_df = apple_df.rename(
        columns={
            "sales": "Apple Sales",
            "platform_fee": "Apple Fee (30%)",
            "proceeds": "Apple Proceeds",
            "kliq_fee_pct": "KLIQ %",
            "kliq_fee": "Apple KLIQ Fee",
            "payout": "Apple Payout",
        }
    )

    google_df = df[df["platform"] == "Google"][
        ["application_name", "month"] + pivot_cols
    ].copy()
    google_df = google_df.rename(
        columns={
            "sales": "Google Sales",
            "platform_fee": "Google Fee (30%)",
            "proceeds": "Google Proceeds",
            "kliq_fee_pct": "KLIQ % (G)",
            "kliq_fee": "Google KLIQ Fee",
            "payout": "Google Payout",
        }
    )

    pivoted = apple_df.merge(google_df, on=["application_name", "month"], how="outer")
    pivoted = pivoted.sort_values(
        ["month", "application_name"], ascending=[False, True]
    )

    # Fill NaN with 0 for numeric cols, keep KLIQ % from whichever side has it
    pivoted["KLIQ %"] = pivoted["KLIQ %"].fillna(pivoted.get("KLIQ % (G)", 0))
    if "KLIQ % (G)" in pivoted.columns:
        pivoted = pivoted.drop(columns=["KLIQ % (G)"])

    money_cols = [
        "Apple Sales",
        "Apple Fee (30%)",
        "Apple Proceeds",
        "Apple KLIQ Fee",
        "Apple Payout",
        "Google Sales",
        "Google Fee (30%)",
        "Google Proceeds",
        "Google KLIQ Fee",
        "Google Payout",
    ]
    for c in money_cols:
        if c in pivoted.columns:
            pivoted[c] = pivoted[c].fillna(0)
    pivoted["KLIQ %"] = pivoted["KLIQ %"].fillna(0)

    # Total Payout = Apple Payout + Google Payout
    pivoted["Apple Payout"] = pivoted.get("Apple Payout", 0)
    pivoted["Google Payout"] = pivoted.get("Google Payout", 0)
    pivoted["Total Payout"] = (
        pivoted["Apple Payout"] + pivoted["Google Payout"]
    ).round(2)

    # Reorder columns
    pivoted = pivoted.rename(columns={"application_name": "App", "month": "Month"})
    col_order = [
        "App",
        "Month",
        "KLIQ %",
        "Apple Sales",
        "Apple Fee (30%)",
        "Apple Proceeds",
        "Apple KLIQ Fee",
        "Apple Payout",
        "Google Sales",
        "Google Fee (30%)",
        "Google Proceeds",
        "Google KLIQ Fee",
        "Google Payout",
        "Total Payout",
    ]
    col_order = [c for c in col_order if c in pivoted.columns]
    pivoted = pivoted[col_order]

    # Month selector for detailed view
    months_available = sorted(df["month"].unique(), reverse=True)
    selected_month = st.selectbox("Select Month", months_available, index=0)

    month_data_raw = df[df["month"] == selected_month]
    month_pivot = pivoted[pivoted["Month"] == selected_month].copy()

    if not month_pivot.empty:
        # Summary for selected month
        m_sales = month_data_raw["sales"].sum()
        m_kliq_fee = month_data_raw["kliq_fee"].sum()
        m_payout = month_data_raw["payout"].sum()

        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            metric_card(f"{selected_month} Sales", fmt_currency(m_sales))
        with mc2:
            metric_card(f"{selected_month} KLIQ Fee", fmt_currency(m_kliq_fee))
        with mc3:
            metric_card(f"{selected_month} Payout", fmt_currency(m_payout))

        st.markdown("<br>", unsafe_allow_html=True)

        # Format for display as colour-coded HTML table
        display_pivot = month_pivot.drop(columns=["Month"]).reset_index(drop=True)

        # Column colour groups
        apple_cols = {
            "Apple Sales",
            "Apple Fee (30%)",
            "Apple Proceeds",
            "Apple KLIQ Fee",
            "Apple Payout",
        }
        google_cols = {
            "Google Sales",
            "Google Fee (30%)",
            "Google Proceeds",
            "Google KLIQ Fee",
            "Google Payout",
        }
        total_cols = {"Total Payout"}

        APPLE_BG = "#EBF5FB"  # light blue
        GOOGLE_BG = "#E8F8F5"  # light green
        TOTAL_BG = "#FEF9E7"  # gold
        HDR_APPLE = "#2E86C1"  # blue header
        HDR_GOOGLE = "#1E8449"  # green header
        HDR_TOTAL = "#B7950B"  # gold header

        def col_bg(col):
            if col in apple_cols:
                return APPLE_BG
            if col in google_cols:
                return GOOGLE_BG
            if col in total_cols:
                return TOTAL_BG
            return "#FFFFFF"

        def hdr_bg(col):
            if col in apple_cols:
                return HDR_APPLE
            if col in google_cols:
                return HDR_GOOGLE
            if col in total_cols:
                return HDR_TOTAL
            return DARK

        def fmt_val(col, val):
            money = apple_cols | google_cols | total_cols
            if col in money:
                return f"${val:,.2f}"
            if col == "KLIQ %":
                return f"{val:.1f}%"
            return str(val)

        # Build HTML table
        cols = [c for c in display_pivot.columns]
        html = '<div style="overflow-x:auto;"><table style="border-collapse:collapse; width:100%; font-family:Inter,sans-serif; font-size:13px;">'
        # Header
        html += "<thead><tr>"
        for c in cols:
            html += f'<th style="background:{hdr_bg(c)}; color:#fff; padding:8px 12px; text-align:right; white-space:nowrap; border:1px solid #ddd;">{c}</th>'
        html += "</tr></thead>"
        # Body
        html += "<tbody>"
        for _, row in display_pivot.iterrows():
            html += "<tr>"
            for c in cols:
                align = "left" if c == "App" else "right"
                bg = col_bg(c)
                html += f'<td style="background:{bg}; padding:6px 12px; text-align:{align}; white-space:nowrap; border:1px solid #eee;">{fmt_val(c, row[c])}</td>'
            html += "</tr>"
        html += "</tbody></table></div>"

        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("No data for the selected month.")

    # ── App Summary Table ───────────────────────────────────────────────────
    section("App Summary (All Time)")

    app_summary = (
        df.groupby(["application_name", "platform"])
        .agg(
            total_sales=("sales", "sum"),
            total_platform_fee=("platform_fee", "sum"),
            total_proceeds=("proceeds", "sum"),
            kliq_pct=("kliq_fee_pct", "first"),
            total_kliq_fee=("kliq_fee", "sum"),
            total_payout=("payout", "sum"),
            months_active=("month", "nunique"),
        )
        .reset_index()
        .sort_values("total_sales", ascending=False)
    )

    app_summary.columns = [
        "App",
        "Platform",
        "Total Sales ($)",
        "Platform Fee ($)",
        "Proceeds ($)",
        "KLIQ %",
        "KLIQ Fee ($)",
        "Payout ($)",
        "Months Active",
    ]

    for col in [
        "Total Sales ($)",
        "Platform Fee ($)",
        "Proceeds ($)",
        "KLIQ Fee ($)",
        "Payout ($)",
    ]:
        app_summary[col] = app_summary[col].apply(lambda x: f"{x:,.2f}")
    app_summary["KLIQ %"] = app_summary["KLIQ %"].apply(lambda x: f"{x:.1f}%")

    st.dataframe(
        app_summary,
        use_container_width=True,
        hide_index=True,
        height=min(len(app_summary) * 38 + 40, 600),
        key="app_summary",
    )

    # ── Top Apps Chart ──────────────────────────────────────────────────────
    section("Top 15 Apps by Sales")

    top_apps = (
        df.groupby("application_name")
        .agg(total_sales=("sales", "sum"), total_kliq=("kliq_fee", "sum"))
        .reset_index()
        .sort_values("total_sales", ascending=True)
        .tail(15)
    )

    fig2 = go.Figure()
    fig2.add_trace(
        go.Bar(
            y=top_apps["application_name"],
            x=top_apps["total_sales"],
            name="Total Sales",
            orientation="h",
            marker_color=ALPINE,
        )
    )
    fig2.add_trace(
        go.Bar(
            y=top_apps["application_name"],
            x=top_apps["total_kliq"],
            name="KLIQ Fee",
            orientation="h",
            marker_color=TANGERINE,
        )
    )
    fig2.update_layout(
        barmode="group",
        plot_bgcolor=IVORY,
        paper_bgcolor=IVORY,
        font=dict(family="Inter", color=DARK),
        height=450,
        margin=dict(l=180, r=20, t=20, b=40),
        legend=dict(orientation="h", y=-0.1),
        xaxis=dict(gridcolor="#E8E8E8", title="USD"),
    )
    st.plotly_chart(fig2, use_container_width=True, key="top_apps")

    # ── Payout Reminder ─────────────────────────────────────────────────────
    section("Payout Schedule Reminder")
    st.markdown(
        f"""
        <div style="background:{BG_CARD}; border-radius:16px; padding:20px 24px; box-shadow:{SHADOW_CARD}; margin-bottom:24px;">
            <p style="color:{DARK}; font-size:14px; font-weight:600; margin:0 0 8px;">⏱ Apple & Google Payout Cycle</p>
            <ul style="color:{NEUTRAL}; font-size:13px; margin:0; padding-left:20px;">
                <li><strong>Apple</strong> pays out approximately <strong>every 33 days</strong> after the end of the fiscal month (effectively ~60 days from sale)</li>
                <li><strong>Google</strong> pays out on the <strong>15th of the following month</strong> (effectively ~45 days from sale)</li>
                <li>Both platforms take a <strong>30% commission</strong> (15% for qualifying small businesses)</li>
                <li>KLIQ fee is calculated on <strong>gross sales</strong> (before platform fee)</li>
                <li>Payout = Total Sales − Platform Fee (30%) − KLIQ Fee</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    st.warning(
        "No IAP data found for the selected filters. Try adjusting the sidebar filters."
    )

# ── Footer ──────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="text-align:center; padding:32px 0 16px; color:{NEUTRAL}; font-size:11px;">
        KLIQ IAP Revenue Dashboard · Data from BigQuery · Updated every 10 min
    </div>
    """,
    unsafe_allow_html=True,
)
