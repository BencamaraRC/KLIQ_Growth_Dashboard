"""
Page 7 — IAP Payouts
In-App Purchase revenue breakdown: Apple/Google sales, platform fees,
KLIQ fee, and coach payout per app per month.
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import require_auth, logout_button
from receipt_generator import generate_receipt_pdf
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
from data import query as run_query

st.set_page_config(page_title="IAP Payouts — KLIQ", page_icon="💰", layout="wide")
inject_css()
register_plotly_template()
require_auth()
logout_button()

# ── Config ──
DATA_PROJECT = "rcwl-data"
DATASET = "powerbi_dashboard"
IVORY = "#FFFDFA"
BG_CARD = "#FFFFFF"
SHADOW_CARD = "0 2px 8px rgba(2,17,17,.06)"
APPLE_COLOR = "#007AFF"
GOOGLE_COLOR = "#34A853"
APPLE_FEE_PCT = 30.0
GOOGLE_FEE_PCT = 30.0


def T(name):
    return f"`{DATA_PROJECT}.{DATASET}.{name}`"


# ── Data Loading ──
@st.cache_data(ttl=600)
def load_apple_monthly():
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
    sql = f"SELECT application_name, kliq_fee_pct FROM {T('d1_app_fee_lookup')}"
    return run_query(sql)


# ── Helpers ──
def metric_card(label, value, sub=""):
    sub_html = (
        f'<div style="font-size:12px; color:{NEUTRAL}; margin-top:2px;">{sub}</div>'
        if sub
        else ""
    )
    st.markdown(
        f'<div style="background:{BG_CARD}; border-radius:16px; padding:22px 24px 18px; box-shadow:{SHADOW_CARD}; text-align:center;">'
        f'<div style="font-size:12px; font-weight:600; color:{NEUTRAL}; text-transform:uppercase; letter-spacing:.5px;">{label}</div>'
        f'<div style="font-size:28px; font-weight:700; color:{DARK}; margin-top:4px;">{value}</div>'
        f"{sub_html}</div>",
        unsafe_allow_html=True,
    )


def fmt_currency(val, prefix="$"):
    if pd.isna(val) or val == 0:
        return f"{prefix}0.00"
    return f"{prefix}{val:,.2f}"


def compute_breakdown(df_platform, fee_lookup, platform_fee_pct, platform_name):
    if df_platform.empty:
        return pd.DataFrame()
    df = df_platform.merge(fee_lookup, on="application_name", how="left")
    df["platform_fee_pct"] = platform_fee_pct
    df["platform_fee"] = (df["sales"] * platform_fee_pct / 100).round(2)
    df["proceeds"] = (df["sales"] - df["platform_fee"]).round(2)
    df["kliq_fee_pct"] = df["kliq_fee_pct"].fillna(0)
    df["kliq_fee"] = (df["sales"] * df["kliq_fee_pct"] / 100).round(2)
    df["payout"] = (df["sales"] - df["platform_fee"] - df["kliq_fee"]).round(2)
    df["platform"] = platform_name
    return df


# ── Load Data ──
st.title("💰 IAP Payouts")

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

if combined.empty:
    st.warning("No IAP data found.")
    st.stop()

# ── Filters ──
fcol1, fcol2, fcol3 = st.columns([3, 2, 1])
with fcol1:
    all_apps = sorted(combined["application_name"].unique())
    selected_apps = st.multiselect("Filter by App", options=all_apps, default=[])
with fcol2:
    platform_filter = st.radio("Platform", ["All", "Apple", "Google"], horizontal=True)
with fcol3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

df = combined.copy()
if selected_apps:
    df = df[df["application_name"].isin(selected_apps)]
if platform_filter != "All":
    df = df[df["platform"] == platform_filter]

if df.empty:
    st.info("No data for the selected filters.")
    st.stop()

# ── KPI Cards ──
total_sales = df["sales"].sum()
total_platform_fee = df["platform_fee"].sum()
total_kliq_fee = df["kliq_fee"].sum()
total_payout = df["payout"].sum()

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Total Sales", fmt_currency(total_sales), "Gross customer price")
with c2:
    metric_card("Platform Fees", fmt_currency(total_platform_fee), "Apple/Google 30%")
with c3:
    metric_card("KLIQ Fee", fmt_currency(total_kliq_fee), "KLIQ % of gross")
with c4:
    metric_card("Coach Payout", fmt_currency(total_payout), "Sales − fees")

st.markdown("<br>", unsafe_allow_html=True)

# ── Monthly Trend ──
st.subheader("📈 Monthly Revenue Trend")

monthly_agg = (
    df.groupby(["month", "platform"])
    .agg(sales=("sales", "sum"), kliq_fee=("kliq_fee", "sum"), payout=("payout", "sum"))
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
st.plotly_chart(fig, use_container_width=True)

# ── Month-by-Month Payout Table ──
st.subheader("📊 Month-by-Month Payout Breakdown")

months_available = sorted(df["month"].unique(), reverse=True)
selected_month = st.selectbox("Select Month", months_available, index=0)

month_data = df[df["month"] == selected_month]

if not month_data.empty:
    # Summary for selected month
    m_sales = month_data["sales"].sum()
    m_kliq_fee = month_data["kliq_fee"].sum()
    m_payout = month_data["payout"].sum()

    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        metric_card(f"{selected_month} Sales", fmt_currency(m_sales))
    with mc2:
        metric_card(f"{selected_month} KLIQ Fee", fmt_currency(m_kliq_fee))
    with mc3:
        metric_card(f"{selected_month} Coach Payout", fmt_currency(m_payout))

    st.markdown("<br>", unsafe_allow_html=True)

    # Build pivot: Apple + Google side by side
    pivot_cols = [
        "sales",
        "platform_fee",
        "proceeds",
        "kliq_fee_pct",
        "kliq_fee",
        "payout",
    ]

    apple_df = month_data[month_data["platform"] == "Apple"][
        ["application_name"] + pivot_cols
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

    google_df = month_data[month_data["platform"] == "Google"][
        ["application_name"] + pivot_cols
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

    pivoted = apple_df.merge(google_df, on="application_name", how="outer")
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

    pivoted["Total Payout"] = (
        pivoted.get("Apple Payout", 0) + pivoted.get("Google Payout", 0)
    ).round(2)

    pivoted = pivoted.rename(columns={"application_name": "App"})
    col_order = [
        "App",
        "KLIQ %",
        "Apple Sales",
        "Apple Fee (30%)",
        "Apple KLIQ Fee",
        "Apple Payout",
        "Google Sales",
        "Google Fee (30%)",
        "Google KLIQ Fee",
        "Google Payout",
        "Total Payout",
    ]
    col_order = [c for c in col_order if c in pivoted.columns]
    pivoted = pivoted[col_order].sort_values("Total Payout", ascending=False)

    # Colour-coded HTML table
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

    APPLE_BG, GOOGLE_BG, TOTAL_BG = "#EBF5FB", "#E8F8F5", "#FEF9E7"
    HDR_APPLE, HDR_GOOGLE, HDR_TOTAL = "#2E86C1", "#1E8449", "#B7950B"

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

    cols = list(pivoted.columns)
    html = '<div style="overflow-x:auto;"><table style="border-collapse:collapse; width:100%; font-family:Inter,sans-serif; font-size:13px;">'
    html += "<thead><tr>"
    for c in cols:
        html += f'<th style="background:{hdr_bg(c)}; color:#fff; padding:8px 12px; text-align:right; white-space:nowrap; border:1px solid #ddd;">{c}</th>'
    html += "</tr></thead><tbody>"
    for _, row in pivoted.iterrows():
        html += "<tr>"
        for c in cols:
            align = "left" if c == "App" else "right"
            html += f'<td style="background:{col_bg(c)}; padding:6px 12px; text-align:{align}; white-space:nowrap; border:1px solid #eee;">{fmt_val(c, row[c])}</td>'
        html += "</tr>"
    html += "</tbody></table></div>"

    st.markdown(html, unsafe_allow_html=True)

    # ── Generate Receipt Buttons ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🧾 Generate Payout Receipts")
    st.caption("Download a branded PDF receipt for any app's payout this month.")

    # Build unit lookup from raw month_data (has total_units per platform)
    _units = {}
    for _, r in month_data.iterrows():
        key = r["application_name"]
        plat = r["platform"]
        if key not in _units:
            _units[key] = {"Apple": 0, "Google": 0}
        _units[key][plat] = int(r.get("total_units", 0))

    rcpt_cols = st.columns(4)
    for idx, (_, row) in enumerate(pivoted.iterrows()):
        app = row["App"]
        kliq_pct = row.get("KLIQ %", 0)
        a_sales = row.get("Apple Sales", 0)
        g_sales = row.get("Google Sales", 0)
        units = _units.get(app, {"Apple": 0, "Google": 0})

        pdf_bytes = generate_receipt_pdf(
            app_name=app,
            month=selected_month,
            apple_sales=a_sales,
            apple_units=units["Apple"],
            google_sales=g_sales,
            google_units=units["Google"],
            kliq_fee_pct=kliq_pct,
        )
        safe_name = app.replace(" ", "_").replace("/", "_")
        filename = f"KLIQ_Receipt_{safe_name}_{selected_month}.pdf"

        with rcpt_cols[idx % 4]:
            st.download_button(
                label=f"📄 {app}",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                key=f"rcpt_{idx}_{selected_month}",
                use_container_width=True,
            )
else:
    st.info("No data for the selected month.")

# ── App Summary (All Time) ──
st.markdown("---")
st.subheader("📋 App Summary (All Time)")

app_summary = (
    df.groupby(["application_name", "platform"])
    .agg(
        total_sales=("sales", "sum"),
        total_platform_fee=("platform_fee", "sum"),
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
    "KLIQ %",
    "KLIQ Fee ($)",
    "Payout ($)",
    "Months Active",
]

for col in ["Total Sales ($)", "Platform Fee ($)", "KLIQ Fee ($)", "Payout ($)"]:
    app_summary[col] = app_summary[col].apply(lambda x: f"{x:,.2f}")
app_summary["KLIQ %"] = app_summary["KLIQ %"].apply(lambda x: f"{x:.1f}%")

st.dataframe(
    app_summary,
    use_container_width=True,
    hide_index=True,
    height=min(len(app_summary) * 38 + 40, 600),
)

# ── Top Apps Chart ──
st.markdown("---")
st.subheader("🏆 Top 15 Apps by Sales")

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
st.plotly_chart(fig2, use_container_width=True)

# ── Payout Schedule Reminder ──
st.markdown("---")
st.markdown(
    f"""
    <div style="background:{BG_CARD}; border-radius:16px; padding:20px 24px; box-shadow:{SHADOW_CARD};">
        <p style="color:{DARK}; font-size:14px; font-weight:600; margin:0 0 8px;">⏱ Apple & Google Payout Cycle</p>
        <ul style="color:{NEUTRAL}; font-size:13px; margin:0; padding-left:20px;">
            <li><strong>Apple</strong> pays out ~33 days after fiscal month end (~60 days from sale)</li>
            <li><strong>Google</strong> pays out on the 15th of the following month (~45 days from sale)</li>
            <li>Both platforms take a <strong>30% commission</strong> (15% for qualifying small businesses)</li>
            <li>KLIQ fee is calculated on <strong>gross sales</strong> (before platform fee)</li>
            <li>Payout = Total Sales − Platform Fee (30%) − KLIQ Fee</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)
