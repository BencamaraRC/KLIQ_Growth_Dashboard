"""
Page 7 — IAP Payouts
In-App Purchase revenue breakdown: Apple/Google sales, platform fees,
KLIQ fee, and coach payout per app per month. PDF receipt generation.
"""

import os
import sys
import base64
import io
import dash
from dash import html, dcc, callback, Input, Output, State, dash_table, no_update, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kliq_ui import (
    GREEN,
    DARK,
    TANGERINE,
    ALPINE,
    NEUTRAL,
    IVORY,
    BG_CARD,
    SHADOW_CARD,
    APPLE_COLOR,
    GOOGLE_COLOR,
    CARD_RADIUS,
    metric_card,
    section_header,
    chart_card,
    card_wrapper,
)
from data import query as run_query, _cached_query, T
from receipt_generator import generate_receipt_pdf

dash.register_page(
    __name__, path="/iap-payouts", name="IAP Payouts", title="IAP Payouts — KLIQ"
)

APPLE_FEE_PCT = 30.0
GOOGLE_FEE_PCT = 30.0

from calendar import month_name as _month_name


def _fiscal_to_apple_month(fiscal_period):
    """Convert Apple fiscal period (e.g. '2026-03') to calendar month ('2025-12')."""
    fy = int(fiscal_period[:4])
    fm = int(fiscal_period[5:7])
    if fm <= 3:
        return f"{fy - 1}-{fm + 9:02d}"
    return f"{fy}-{fm - 3:02d}"


def _compute_payment_due_date(apple_month):
    """KLIQ pays coaches 2 months after Apple's fiscal month."""
    y, m = int(apple_month[:4]), int(apple_month[5:7])
    m += 2
    if m > 12:
        m -= 12
        y += 1
    return f"{_month_name[m]} {y}"


def _load_apple_monthly():
    """Load Apple monthly revenue from Sales Reports (calendar months).
    Uses customer_price_usd / developer_proceeds_usd pre-computed with
    ECB historical rates via frankfurter.app at ingestion time."""
    return _cached_query(
        "iap_apple_monthly",
        lambda: run_query(
            f"""
    WITH sku_map AS (SELECT DISTINCT product_id, application_name FROM {T('d1_inapp_products')})
    SELECT COALESCE(m.application_name, 'Unknown') AS application_name,
           FORMAT_DATE("%Y-%m", s.report_date) AS month,
           SUM(SAFE_CAST(s.units AS INT64)) AS total_units,
           ROUND(SUM(SAFE_CAST(s.customer_price_usd AS FLOAT64) * SAFE_CAST(s.units AS INT64)), 2) AS sales,
           ROUND(SUM(SAFE_CAST(s.developer_proceeds_usd AS FLOAT64) * SAFE_CAST(s.units AS INT64)), 2) AS proceeds
    FROM {T('d1_appstore_sales')} s
    LEFT JOIN sku_map m ON s.sku = m.product_id
    WHERE s.product_type_identifier IN ('IA1', 'IAY')
      AND SAFE_CAST(s.customer_price_usd AS FLOAT64) > 0
    GROUP BY application_name, month ORDER BY application_name, month
    """
        ),
    )


def _load_google_monthly():
    return _cached_query(
        "iap_google_monthly",
        lambda: run_query(
            f"""
    SELECT e.application_name, e.month, COUNT(*) AS total_units,
           ROUND(SUM(SAFE_CAST(e.amount_buyer_usd AS FLOAT64)), 2) AS sales,
           ROUND(SUM(SAFE_CAST(e.amount_buyer_usd AS FLOAT64)) * 0.70, 2) AS proceeds
    FROM {T('d1_google_earnings')} e
    WHERE e.transaction_type = 'Charge' AND e.application_name IS NOT NULL
    GROUP BY e.application_name, e.month ORDER BY e.application_name, e.month
    """
        ),
    )


def _load_apple_refunds():
    return _cached_query(
        "iap_apple_refunds",
        lambda: run_query(
            f"""
    WITH sku_map AS (SELECT DISTINCT product_id, application_name FROM {T('d1_inapp_products')})
    SELECT COALESCE(m.application_name, 'Unknown') AS application_name,
           FORMAT_DATE("%Y-%m", s.report_date) AS month,
           ABS(SUM(SAFE_CAST(s.units AS INT64))) AS refund_units,
           ROUND(ABS(SUM(SAFE_CAST(s.customer_price_usd AS FLOAT64) * SAFE_CAST(s.units AS INT64))), 2) AS refund_amount
    FROM {T('d1_appstore_sales')} s LEFT JOIN sku_map m ON s.sku = m.product_id
    WHERE s.product_type_identifier IN ('IA1', 'IAY') AND SAFE_CAST(s.units AS INT64) < 0
    GROUP BY 1, 2 ORDER BY 1, 2
    """
        ),
    )


def _load_google_refunds():
    return _cached_query(
        "iap_google_refunds",
        lambda: run_query(
            f"""
    SELECT e.application_name, e.month, COUNT(*) AS refund_units,
           ROUND(ABS(SUM(SAFE_CAST(e.amount_buyer_usd AS FLOAT64))), 2) AS refund_amount
    FROM {T('d1_google_earnings')} e
    WHERE e.transaction_type = 'Charge refund' AND e.application_name IS NOT NULL
    GROUP BY 1, 2 ORDER BY 1, 2
    """
        ),
    )


def _load_fee_lookup():
    return _cached_query(
        "iap_fee_lookup",
        lambda: run_query(
            f"SELECT application_name, kliq_fee_pct FROM {T('d1_app_fee_lookup')}"
        ),
    )


def _load_apple_product_details():
    return _cached_query(
        "iap_apple_product_details",
        lambda: run_query(
            f"""
    WITH sku_map AS (SELECT DISTINCT product_id, application_name FROM {T('d1_inapp_products')})
    SELECT
        COALESCE(m.application_name, 'Unknown') AS application_name,
        FORMAT_DATE("%Y-%m", s.report_date) AS month,
        s.sku AS product_id,
        s.title AS product_name,
        s.subscription AS sub_type,
        s.period,
        SUM(SAFE_CAST(s.units AS INT64)) AS units,
        ROUND(SUM(SAFE_CAST(s.customer_price_usd AS FLOAT64)
              * SAFE_CAST(s.units AS INT64)), 2) AS revenue_usd
    FROM {T('d1_appstore_sales')} s
    LEFT JOIN sku_map m ON s.sku = m.product_id
    WHERE s.product_type_identifier IN ('IA1', 'IAY')
      AND SAFE_CAST(s.units AS INT64) > 0
    GROUP BY 1, 2, 3, 4, 5, 6
    ORDER BY 1, 2, revenue_usd DESC
    """
        ),
    )


def _load_google_product_details():
    return _cached_query(
        "iap_google_product_details",
        lambda: run_query(
            f"""
    SELECT
        e.application_name,
        e.month,
        e.sku_id AS product_id,
        e.product_title AS product_name,
        'Purchase' AS sub_type,
        CASE
            WHEN LOWER(e.sku_id) LIKE '%monthly%' OR LOWER(e.sku_id) LIKE '%month%' THEN '1 Month'
            WHEN LOWER(e.sku_id) LIKE '%quarterly%' OR LOWER(e.sku_id) LIKE '%quarter%' THEN '3 Months'
            WHEN LOWER(e.sku_id) LIKE '%sixmonth%' OR LOWER(e.sku_id) LIKE '%6month%' THEN '6 Months'
            WHEN LOWER(e.sku_id) LIKE '%yearly%' OR LOWER(e.sku_id) LIKE '%year%' OR LOWER(e.sku_id) LIKE '%annual%' THEN '1 Year'
            ELSE 'Other'
        END AS period,
        COUNT(*) AS units,
        ROUND(SUM(SAFE_CAST(e.amount_buyer_usd AS FLOAT64)), 2) AS revenue_usd
    FROM {T('d1_google_earnings')} e
    WHERE e.transaction_type = 'Charge'
      AND e.application_name IS NOT NULL
    GROUP BY 1, 2, 3, 4, 5, 6
    ORDER BY 1, 2, revenue_usd DESC
    """
        ),
    )


# ── Apple Financial Reports (settlement / fiscal period) loaders ──


def _load_apple_financial():
    """Load Apple Financial Reports settlement data grouped by app + fiscal period."""
    return _cached_query(
        "iap_apple_financial",
        lambda: run_query(
            f"""
    WITH sku_map AS (SELECT DISTINCT product_id, application_name FROM {T('d1_inapp_products')})
    SELECT COALESCE(m.application_name, 'Unknown') AS application_name,
           f.apple_month, f.fiscal_period,
           MIN(f.period_start) AS period_start,
           MAX(f.period_end) AS period_end,
           SUM(SAFE_CAST(f.quantity AS INT64)) AS total_units,
           ROUND(SUM(f.gross_revenue_usd), 2) AS sales,
           ROUND(SUM(f.extended_partner_share_usd), 2) AS proceeds
    FROM {T('d1_appstore_financial')} f
    LEFT JOIN sku_map m ON f.vendor_identifier = m.product_id
    WHERE f.product_type_identifier IN ('IA1', 'IAY')
      AND UPPER(f.sales_or_return) = 'S'
    GROUP BY 1, 2, 3
    ORDER BY 1, 2
    """
        ),
    )


def _load_apple_financial_refunds():
    """Load refunds from Apple Financial Reports."""
    return _cached_query(
        "iap_apple_financial_refunds",
        lambda: run_query(
            f"""
    WITH sku_map AS (SELECT DISTINCT product_id, application_name FROM {T('d1_inapp_products')})
    SELECT COALESCE(m.application_name, 'Unknown') AS application_name,
           f.apple_month, f.fiscal_period,
           ABS(SUM(SAFE_CAST(f.quantity AS INT64))) AS refund_units,
           ROUND(ABS(SUM(f.gross_revenue_usd)), 2) AS refund_amount
    FROM {T('d1_appstore_financial')} f
    LEFT JOIN sku_map m ON f.vendor_identifier = m.product_id
    WHERE f.product_type_identifier IN ('IA1', 'IAY')
      AND UPPER(f.sales_or_return) = 'R'
    GROUP BY 1, 2, 3
    ORDER BY 1, 2
    """
        ),
    )


def _load_apple_financial_product_details():
    """Load per-product details from Apple Financial Reports."""
    return _cached_query(
        "iap_apple_financial_product_details",
        lambda: run_query(
            f"""
    WITH sku_map AS (SELECT DISTINCT product_id, application_name FROM {T('d1_inapp_products')})
    SELECT COALESCE(m.application_name, 'Unknown') AS application_name,
           f.apple_month, f.fiscal_period,
           f.vendor_identifier AS product_id,
           f.title AS product_name,
           SUM(SAFE_CAST(f.quantity AS INT64)) AS units,
           ROUND(SUM(f.gross_revenue_usd), 2) AS revenue_usd,
           ROUND(SUM(f.extended_partner_share_usd), 2) AS proceeds_usd
    FROM {T('d1_appstore_financial')} f
    LEFT JOIN sku_map m ON f.vendor_identifier = m.product_id
    WHERE f.product_type_identifier IN ('IA1', 'IAY')
      AND UPPER(f.sales_or_return) = 'S'
    GROUP BY 1, 2, 3, 4, 5
    ORDER BY 1, 2, revenue_usd DESC
    """
        ),
    )


def _load_fiscal_periods():
    """Load distinct fiscal periods with date ranges."""
    return _cached_query(
        "iap_fiscal_periods",
        lambda: run_query(
            f"""
    SELECT DISTINCT fiscal_period, apple_month,
           MIN(period_start) AS period_start,
           MAX(period_end) AS period_end
    FROM {T('d1_appstore_financial')}
    GROUP BY fiscal_period, apple_month
    ORDER BY fiscal_period DESC
    """
        ),
    )


def _compute_breakdown(
    df_platform, fee_lookup, platform_fee_pct, platform_name, refunds_df=None
):
    if df_platform.empty:
        return pd.DataFrame()
    df = df_platform.merge(fee_lookup, on="application_name", how="left")
    df["platform_fee_pct"] = platform_fee_pct
    df["platform_fee"] = (df["sales"] * platform_fee_pct / 100).round(2)
    df["proceeds"] = (df["sales"] - df["platform_fee"]).round(2)
    df["kliq_fee_pct"] = df["kliq_fee_pct"].fillna(0)
    df["kliq_fee"] = (df["sales"] * df["kliq_fee_pct"] / 100).round(2)
    df["refund_amount"] = 0.0
    df["refund_units"] = 0
    if refunds_df is not None and not refunds_df.empty:
        ref = refunds_df.rename(
            columns={"refund_amount": "_ref_amt", "refund_units": "_ref_units"}
        )
        df = df.merge(
            ref[["application_name", "month", "_ref_amt", "_ref_units"]],
            on=["application_name", "month"],
            how="left",
        )
        df["refund_amount"] = df["_ref_amt"].fillna(0).round(2)
        df["refund_units"] = df["_ref_units"].fillna(0).astype(int).abs()
        df = df.drop(columns=["_ref_amt", "_ref_units"])
    df["payout"] = (
        df["sales"] - df["platform_fee"] - df["kliq_fee"] - df["refund_amount"]
    ).round(2)
    df["platform"] = platform_name
    return df


def _compute_fiscal_breakdown(df_fiscal, fee_lookup, refunds_df=None):
    """Compute breakdown from Apple Financial Reports.
    Platform fee = sales - proceeds (actual Apple commission, captures 15% SBP vs 30%)."""
    if df_fiscal.empty:
        return pd.DataFrame()
    df = df_fiscal.merge(fee_lookup, on="application_name", how="left")
    df["platform_fee"] = (df["sales"] - df["proceeds"]).round(2)
    df["platform_fee_pct"] = (
        (df["platform_fee"] / df["sales"] * 100).where(df["sales"] > 0, 0).round(1)
    )
    df["kliq_fee_pct"] = df["kliq_fee_pct"].fillna(0)
    df["kliq_fee"] = (df["sales"] * df["kliq_fee_pct"] / 100).round(2)
    df["refund_amount"] = 0.0
    df["refund_units"] = 0
    if refunds_df is not None and not refunds_df.empty:
        ref = refunds_df.rename(
            columns={"refund_amount": "_ref_amt", "refund_units": "_ref_units"}
        )
        df = df.merge(
            ref[["application_name", "fiscal_period", "_ref_amt", "_ref_units"]],
            on=["application_name", "fiscal_period"],
            how="left",
        )
        df["refund_amount"] = df["_ref_amt"].fillna(0).round(2)
        df["refund_units"] = df["_ref_units"].fillna(0).astype(int).abs()
        df = df.drop(columns=["_ref_amt", "_ref_units"])
    df["payout"] = (
        df["sales"] - df["platform_fee"] - df["kliq_fee"] - df["refund_amount"]
    ).round(2)
    df["platform"] = "Apple"
    df["month"] = df["apple_month"]
    return df


def _empty_fig(msg="No data available"):
    fig = go.Figure()
    fig.update_layout(
        annotations=[
            {
                "text": msg,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": NEUTRAL},
            }
        ],
        height=350,
    )
    return fig


def _fmt(val, prefix="$"):
    if pd.isna(val) or val == 0:
        return f"{prefix}0.00"
    return f"{prefix}{val:,.2f}"


layout = html.Div(
    [
        html.H1(
            "💰 IAP Payouts",
            style={"fontSize": "20px", "fontWeight": "700", "color": DARK},
        ),
        html.Hr(),
        # Data View Toggle
        html.Div(
            [
                dbc.Label(
                    "Data View",
                    style={"fontWeight": "600", "fontSize": "13px", "marginRight": "12px"},
                ),
                dbc.RadioItems(
                    id="iap-view-toggle",
                    options=[
                        {"label": "Calendar Month", "value": "calendar"},
                        {"label": "Apple Fiscal Period", "value": "fiscal"},
                    ],
                    value="calendar",
                    inline=True,
                    input_style={"marginRight": "4px"},
                    label_style={"marginRight": "20px", "fontSize": "13px"},
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "marginBottom": "16px",
                "padding": "10px 16px",
                "backgroundColor": "#F2F3EE",
                "borderRadius": "8px",
            },
        ),
        # Filters
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Filter by App",
                            style={"fontWeight": "600", "fontSize": "13px"},
                        ),
                        dcc.Dropdown(
                            id="iap-app-filter",
                            options=[],
                            value=[],
                            multi=True,
                            placeholder="All Apps",
                            style={"fontSize": "13px"},
                        ),
                    ],
                    md=4,
                ),
                dbc.Col(
                    [
                        dbc.Label(
                            "Platform", style={"fontWeight": "600", "fontSize": "13px"}
                        ),
                        dbc.RadioItems(
                            id="iap-platform",
                            options=[
                                {"label": "All", "value": "All"},
                                {"label": "Apple", "value": "Apple"},
                                {"label": "Google", "value": "Google"},
                            ],
                            value="All",
                            inline=True,
                        ),
                    ],
                    md=3,
                ),
                dbc.Col(
                    [
                        dbc.Label(
                            "Month", style={"fontWeight": "600", "fontSize": "13px"}
                        ),
                        dcc.Dropdown(
                            id="iap-month",
                            options=[],
                            clearable=False,
                            style={"fontSize": "13px"},
                        ),
                    ],
                    md=3,
                ),
            ],
            className="mb-4",
        ),
        # KPIs
        dbc.Row(id="iap-kpi-row", className="mb-3"),
        # Fiscal Period Banner (hidden in calendar mode)
        html.Div(id="iap-fiscal-banner"),
        # Monthly Trend
        section_header("📈 Monthly Revenue Trend"),
        chart_card(dcc.Graph(id="iap-trend-chart")),
        # Payout Breakdown Table
        section_header("📊 Payout Breakdown"),
        card_wrapper(html.Div(id="iap-breakdown-table")),
        # Receipt Generation
        section_header("🧾 Generate Payout Receipts"),
        card_wrapper(
            [
                html.P(
                    "Select an app and click Generate to download a detailed PDF payout receipt.",
                    style={
                        "color": NEUTRAL,
                        "fontSize": "13px",
                        "marginBottom": "12px",
                    },
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label(
                                    "Select App",
                                    style={"fontWeight": "600", "fontSize": "13px"},
                                ),
                                dcc.Dropdown(
                                    id="iap-receipt-app",
                                    options=[],
                                    placeholder="Choose an app…",
                                    style={"fontSize": "13px"},
                                ),
                            ],
                            md=5,
                        ),
                        dbc.Col(
                            [
                                html.Div(style={"height": "22px"}),
                                dbc.Button(
                                    "📄 Generate PDF Receipt",
                                    id="iap-gen-receipt-btn",
                                    color="dark",
                                    className="w-100",
                                    style={"fontWeight": "600", "fontSize": "13px"},
                                ),
                            ],
                            md=3,
                        ),
                        dbc.Col(
                            [
                                html.Div(id="iap-receipt-status"),
                            ],
                            md=4,
                        ),
                    ]
                ),
                dcc.Download(id="iap-receipt-download"),
                html.Div(id="iap-receipt-view-note", style={"marginTop": "12px"}),
            ]
        ),
        # Product Details
        section_header("📦 Product & Subscription Details"),
        card_wrapper(html.Div(id="iap-product-details")),
        html.Hr(),
        # App Summary
        section_header("📋 App Summary (All Time)"),
        card_wrapper(html.Div(id="iap-summary-table")),
        # Top Apps
        section_header("🏆 Top 15 Apps by Sales"),
        chart_card(dcc.Graph(id="iap-top-chart")),
        # Payout Schedule
        card_wrapper(
            [
                html.P(
                    "⏱ Apple & Google Payout Cycle",
                    style={"fontWeight": "700", "color": DARK, "marginBottom": "8px"},
                ),
                html.Ul(
                    [
                        html.Li(
                            [
                                html.Strong("Apple"),
                                " pays out ~33 days after fiscal month end (~60 days from sale)",
                            ]
                        ),
                        html.Li(
                            [
                                html.Strong("Google"),
                                " pays out on the 15th of the following month (~45 days from sale)",
                            ]
                        ),
                        html.Li(
                            "Both platforms take a 30% commission (15% for qualifying small businesses)"
                        ),
                        html.Li(
                            "KLIQ fee is calculated on gross sales (before platform fee)"
                        ),
                        html.Li("Refunds are deducted from the coach payout"),
                        html.Li(
                            "Payout = Total Sales − Platform Fee − KLIQ Fee − Refunds"
                        ),
                    ],
                    style={"fontSize": "13px", "color": NEUTRAL},
                ),
            ]
        ),
    ]
)


@callback(
    Output("iap-app-filter", "options"),
    Output("iap-month", "options"),
    Output("iap-month", "value"),
    Output("iap-receipt-app", "options"),
    Input("iap-app-filter", "value"),
    Input("iap-view-toggle", "value"),
)
def populate_filters(_, view_mode):
    is_fiscal = view_mode == "fiscal"

    if is_fiscal:
        # Fiscal mode: use Financial Reports data
        fiscal_raw = _load_apple_financial()
        google_raw = _load_google_monthly()
        fee_lookup = _load_fee_lookup()
        fiscal = _compute_fiscal_breakdown(
            fiscal_raw, fee_lookup, _load_apple_financial_refunds()
        )
        google = _compute_breakdown(
            google_raw, fee_lookup, GOOGLE_FEE_PCT, "Google", _load_google_refunds()
        )
        combined = pd.concat([fiscal, google], ignore_index=True)

        app_opts = (
            [
                {"label": n, "value": n}
                for n in sorted(combined["application_name"].unique())
            ]
            if not combined.empty
            else []
        )

        # Build fiscal period dropdown
        periods = _load_fiscal_periods()
        if not periods.empty:
            period_opts = [{"label": "All Periods", "value": "All Periods"}]
            for _, row in periods.iterrows():
                cal = row["apple_month"]
                fp = row["fiscal_period"]
                y, m = int(cal[:4]), int(cal[5:7])
                try:
                    start_str = pd.to_datetime(row["period_start"]).strftime("%b %d")
                    end_str = pd.to_datetime(row["period_end"]).strftime("%b %d, %Y")
                except Exception:
                    start_str, end_str = "?", "?"
                label = f"{_month_name[m]} {y} ({start_str} - {end_str})"
                period_opts.append({"label": label, "value": f"fiscal:{fp}"})
            default_val = period_opts[1]["value"] if len(period_opts) > 1 else "All Periods"
        else:
            period_opts = [{"label": "No fiscal data", "value": "All Periods"}]
            default_val = "All Periods"

        return app_opts, period_opts, default_val, app_opts
    else:
        # Calendar mode: unchanged
        apple_raw = _load_apple_monthly()
        google_raw = _load_google_monthly()
        fee_lookup = _load_fee_lookup()
        apple = _compute_breakdown(
            apple_raw, fee_lookup, APPLE_FEE_PCT, "Apple", _load_apple_refunds()
        )
        google = _compute_breakdown(
            google_raw, fee_lookup, GOOGLE_FEE_PCT, "Google", _load_google_refunds()
        )
        combined = pd.concat([apple, google], ignore_index=True)

        app_opts = (
            [
                {"label": n, "value": n}
                for n in sorted(combined["application_name"].unique())
            ]
            if not combined.empty
            else []
        )
        months = (
            sorted(combined["month"].unique(), reverse=True)
            if not combined.empty
            else []
        )
        month_opts = [{"label": "All Months", "value": "All Months"}] + [
            {"label": m, "value": m} for m in months
        ]
        default_month = months[0] if months else "All Months"
        return app_opts, month_opts, default_month, app_opts


@callback(
    Output("iap-kpi-row", "children"),
    Output("iap-trend-chart", "figure"),
    Output("iap-breakdown-table", "children"),
    Output("iap-summary-table", "children"),
    Output("iap-top-chart", "figure"),
    Output("iap-fiscal-banner", "children"),
    Output("iap-receipt-view-note", "children"),
    Input("iap-app-filter", "value"),
    Input("iap-platform", "value"),
    Input("iap-month", "value"),
    Input("iap-view-toggle", "value"),
)
def update_iap(selected_apps, platform_filter, selected_month, view_mode):
    is_fiscal = view_mode == "fiscal"
    fee_lookup = _load_fee_lookup()

    # ── Load data based on view mode ──
    if is_fiscal:
        fiscal_raw = _load_apple_financial()
        fiscal_refunds = _load_apple_financial_refunds()
        apple = _compute_fiscal_breakdown(fiscal_raw, fee_lookup, fiscal_refunds)
    else:
        apple_raw = _load_apple_monthly()
        apple = _compute_breakdown(
            apple_raw, fee_lookup, APPLE_FEE_PCT, "Apple", _load_apple_refunds()
        )

    google_raw = _load_google_monthly()
    # Normalise Google names to Apple casing
    apple_names = apple["application_name"].unique() if not apple.empty else []
    _canon = {n.lower(): n for n in apple_names if n}
    for _df in [google_raw]:
        if not _df.empty and "application_name" in _df.columns:
            _df["application_name"] = _df["application_name"].apply(
                lambda x: _canon.get(x.lower(), x) if isinstance(x, str) else x
            )
    google = _compute_breakdown(
        google_raw, fee_lookup, GOOGLE_FEE_PCT, "Google", _load_google_refunds()
    )
    combined = pd.concat([apple, google], ignore_index=True)

    if combined.empty:
        empty = _empty_fig("No IAP data")
        no_data = html.P("No data", style={"color": NEUTRAL})
        return [], empty, no_data, no_data, empty, None, None

    df_all = combined.copy()
    if selected_apps:
        df_all = df_all[df_all["application_name"].isin(selected_apps)]
    if platform_filter != "All":
        df_all = df_all[df_all["platform"] == platform_filter]

    # ── Resolve effective month filter ──
    if is_fiscal and selected_month and selected_month.startswith("fiscal:"):
        fp = selected_month.split(":")[1]
        filter_month = _fiscal_to_apple_month(fp)
    elif is_fiscal:
        filter_month = None  # All Periods
    elif selected_month and selected_month != "All Months":
        filter_month = selected_month
    else:
        filter_month = None  # All Months

    df_trend = df_all.copy()
    df = df_all.copy()
    actual_month = filter_month
    if filter_month:
        df = df[df["month"] == filter_month]
    elif not df.empty:
        actual_month = sorted(df["month"].unique(), reverse=True)[0]
        df = df[df["month"] == actual_month]

    if df.empty:
        empty = _empty_fig("No data for selected filters")
        no_data = html.P("No data for the selected filters.", style={"color": NEUTRAL})
        return [], empty, no_data, no_data, empty, None, None

    # ── KPIs ──
    total_sales = df["sales"].sum()
    total_pf = df["platform_fee"].sum()
    total_kf = df["kliq_fee"].sum()
    total_ref = df["refund_amount"].sum()
    total_pay = df["payout"].sum()

    if is_fiscal and actual_month:
        y, m = int(actual_month[:4]), int(actual_month[5:7])
        kpi_label = f"{_month_name[m]} {y}"
    else:
        kpi_label = actual_month if actual_month else "All Time"

    pf_subtitle = "Apple (actual) / Google 30%" if is_fiscal else "Apple/Google 30%"

    kpi = [
        dbc.Col(
            metric_card(
                f"{kpi_label} Sales", _fmt(total_sales), "Gross customer price"
            ),
            md=2,
        ),
        dbc.Col(metric_card("Platform Fees", _fmt(total_pf), pf_subtitle), md=2),
        dbc.Col(metric_card("KLIQ Fee", _fmt(total_kf), "KLIQ % of gross"), md=2),
        dbc.Col(metric_card("Refunds", _fmt(total_ref), "Customer refunds"), md=2),
        dbc.Col(
            metric_card("Coach Payout", _fmt(total_pay), "Sales − fees − refunds"),
            md=2,
        ),
    ]

    # Trend Chart
    monthly_agg = (
        df_trend.groupby(["month", "platform"])
        .agg(
            sales=("sales", "sum"),
            kliq_fee=("kliq_fee", "sum"),
            payout=("payout", "sum"),
        )
        .reset_index()
        .sort_values("month")
    )

    fig_trend = go.Figure()
    color_map = {"Apple": APPLE_COLOR, "Google": GOOGLE_COLOR}
    for plat in monthly_agg["platform"].unique():
        pdata = monthly_agg[monthly_agg["platform"] == plat]
        fig_trend.add_trace(
            go.Bar(
                x=pdata["month"],
                y=pdata["sales"],
                name=f"{plat} Sales",
                marker_color=color_map.get(plat, NEUTRAL),
                opacity=0.85,
            )
        )
        fig_trend.add_trace(
            go.Scatter(
                x=pdata["month"],
                y=pdata["kliq_fee"],
                name=f"{plat} KLIQ Fee",
                mode="lines+markers",
                line=dict(color=TANGERINE, width=2),
            )
        )
    fig_trend.update_layout(
        barmode="stack",
        height=380,
        legend=dict(orientation="h", y=-0.15),
        yaxis=dict(title="USD"),
    )

    # Breakdown Table
    month_data = df.copy()
    apple_df = month_data[month_data["platform"] == "Apple"][
        [
            "application_name",
            "sales",
            "platform_fee",
            "kliq_fee_pct",
            "kliq_fee",
            "refund_amount",
            "payout",
        ]
    ].copy()
    apple_df = apple_df.rename(
        columns={
            "sales": "Apple Sales",
            "platform_fee": "Apple Fee",
            "kliq_fee_pct": "KLIQ %",
            "kliq_fee": "Apple KLIQ Fee",
            "refund_amount": "Apple Refunds",
            "payout": "Apple Payout",
        }
    )
    google_df = month_data[month_data["platform"] == "Google"][
        [
            "application_name",
            "sales",
            "platform_fee",
            "kliq_fee_pct",
            "kliq_fee",
            "refund_amount",
            "payout",
        ]
    ].copy()
    google_df = google_df.rename(
        columns={
            "sales": "Google Sales",
            "platform_fee": "Google Fee",
            "kliq_fee_pct": "KLIQ % (G)",
            "kliq_fee": "Google KLIQ Fee",
            "refund_amount": "Google Refunds",
            "payout": "Google Payout",
        }
    )
    pivoted = apple_df.merge(google_df, on="application_name", how="outer")
    pivoted["KLIQ %"] = pivoted["KLIQ %"].fillna(pivoted.get("KLIQ % (G)", 0))
    if "KLIQ % (G)" in pivoted.columns:
        pivoted = pivoted.drop(columns=["KLIQ % (G)"])
    for c in [
        "Apple Sales",
        "Apple Fee",
        "Apple KLIQ Fee",
        "Apple Refunds",
        "Apple Payout",
        "Google Sales",
        "Google Fee",
        "Google KLIQ Fee",
        "Google Refunds",
        "Google Payout",
    ]:
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
        "Apple Fee",
        "Apple KLIQ Fee",
        "Apple Refunds",
        "Apple Payout",
        "Google Sales",
        "Google Fee",
        "Google KLIQ Fee",
        "Google Refunds",
        "Google Payout",
        "Total Payout",
    ]
    col_order = [c for c in col_order if c in pivoted.columns]
    pivoted = pivoted[col_order].sort_values("Total Payout", ascending=False)

    money_cols = [c for c in col_order if c not in ("App", "KLIQ %")]
    columns = []
    for c in pivoted.columns:
        if c == "App":
            columns.append({"name": c, "id": c})
        elif c == "KLIQ %":
            columns.append(
                {"name": c, "id": c, "type": "numeric", "format": {"specifier": ".1f"}}
            )
        else:
            columns.append(
                {
                    "name": c,
                    "id": c,
                    "type": "numeric",
                    "format": {"specifier": "$,.2f"},
                }
            )

    breakdown_table = dash_table.DataTable(
        data=pivoted.to_dict("records"),
        columns=columns,
        style_table={"overflowX": "auto"},
        style_cell={
            "fontSize": "11px",
            "padding": "5px 8px",
            "fontFamily": "Sora",
            "textAlign": "right",
            "minWidth": "90px",
        },
        style_header={
            "fontWeight": "600",
            "backgroundColor": "#F2F3EE",
            "textAlign": "center",
        },
        style_data_conditional=[
            {"if": {"column_id": "App"}, "textAlign": "left"},
        ]
        + [
            {"if": {"column_id": c}, "backgroundColor": "#EBF5FB"}
            for c in [
                "Apple Sales",
                "Apple Fee",
                "Apple KLIQ Fee",
                "Apple Refunds",
                "Apple Payout",
            ]
            if c in pivoted.columns
        ]
        + [
            {"if": {"column_id": c}, "backgroundColor": "#E8F8F5"}
            for c in [
                "Google Sales",
                "Google Fee",
                "Google KLIQ Fee",
                "Google Refunds",
                "Google Payout",
            ]
            if c in pivoted.columns
        ]
        + [
            {
                "if": {"column_id": "Total Payout"},
                "backgroundColor": "#FEF9E7",
                "fontWeight": "600",
            },
        ],
        sort_action="native",
        page_size=50,
    )

    # Summary Table
    app_summary = (
        df_all.groupby(["application_name", "platform"])
        .agg(
            total_sales=("sales", "sum"),
            total_pf=("platform_fee", "sum"),
            kliq_pct=("kliq_fee_pct", "first"),
            total_kf=("kliq_fee", "sum"),
            total_pay=("payout", "sum"),
            months=("month", "nunique"),
        )
        .reset_index()
        .sort_values("total_sales", ascending=False)
    )
    app_summary.columns = [
        "App",
        "Platform",
        "Total Sales",
        "Platform Fee",
        "KLIQ %",
        "KLIQ Fee",
        "Payout",
        "Months",
    ]

    summary_table = dash_table.DataTable(
        data=app_summary.to_dict("records"),
        columns=[
            (
                {
                    "name": c,
                    "id": c,
                    "type": "numeric",
                    "format": {"specifier": "$,.2f"},
                }
                if c in ("Total Sales", "Platform Fee", "KLIQ Fee", "Payout")
                else (
                    {
                        "name": c,
                        "id": c,
                        "type": "numeric",
                        "format": {"specifier": ".1f"},
                    }
                    if c == "KLIQ %"
                    else {"name": c, "id": c}
                )
            )
            for c in app_summary.columns
        ],
        style_table={"overflowX": "auto"},
        style_cell={
            "fontSize": "12px",
            "padding": "6px",
            "fontFamily": "Sora",
            "textAlign": "right",
        },
        style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
        style_data_conditional=[
            {"if": {"column_id": c}, "textAlign": "left"} for c in ["App", "Platform"]
        ],
        sort_action="native",
        filter_action="native",
        page_size=25,
    )

    # Top Apps Chart
    top_apps = (
        df_all.groupby("application_name")
        .agg(total_sales=("sales", "sum"), total_kliq=("kliq_fee", "sum"))
        .reset_index()
        .sort_values("total_sales", ascending=True)
        .tail(15)
    )

    fig_top = go.Figure()
    fig_top.add_trace(
        go.Bar(
            y=top_apps["application_name"],
            x=top_apps["total_sales"],
            name="Total Sales",
            orientation="h",
            marker_color=ALPINE,
        )
    )
    fig_top.add_trace(
        go.Bar(
            y=top_apps["application_name"],
            x=top_apps["total_kliq"],
            name="KLIQ Fee",
            orientation="h",
            marker_color=TANGERINE,
        )
    )
    fig_top.update_layout(
        barmode="group",
        height=450,
        margin=dict(l=180),
        legend=dict(orientation="h", y=-0.1),
        xaxis=dict(title="USD"),
    )

    # ── Fiscal banner ──
    banner_content = None
    if is_fiscal and actual_month:
        periods = _load_fiscal_periods()
        fp_match = periods[periods["apple_month"] == actual_month]
        if not fp_match.empty:
            row = fp_match.iloc[0]
            try:
                start_str = pd.to_datetime(row["period_start"]).strftime("%b %d")
                end_str = pd.to_datetime(row["period_end"]).strftime("%b %d, %Y")
            except Exception:
                start_str, end_str = "?", "?"
            due_date = _compute_payment_due_date(actual_month)
            y, m = int(actual_month[:4]), int(actual_month[5:7])
            banner_content = dbc.Alert(
                [
                    html.Strong("Apple Fiscal Period: "),
                    f"{_month_name[m]} {y} ({start_str} - {end_str})",
                    html.Span(" | ", style={"margin": "0 8px"}),
                    html.Strong("Coach Payout Due: "),
                    due_date,
                ],
                color="info",
                className="mb-3",
                style={"fontSize": "13px"},
            )
        else:
            # Fiscal period has no settlement data yet
            banner_content = dbc.Alert(
                "Pending settlement — Apple has not yet published financial data for this period.",
                color="warning",
                className="mb-3",
                style={"fontSize": "13px"},
            )

    # ── Receipt view note ──
    if is_fiscal:
        receipt_note = html.Span(
            "Data source: Apple Financial Reports (settlement amounts) + Google Play earnings",
            style={"color": NEUTRAL, "fontSize": "11px", "fontStyle": "italic"},
        )
    else:
        receipt_note = html.Span(
            "Data source: Apple Sales Reports (ECB FX rates) + Google Play earnings",
            style={"color": NEUTRAL, "fontSize": "11px", "fontStyle": "italic"},
        )

    return kpi, fig_trend, breakdown_table, summary_table, fig_top, banner_content, receipt_note


@callback(
    Output("iap-receipt-download", "data"),
    Output("iap-receipt-status", "children"),
    Input("iap-gen-receipt-btn", "n_clicks"),
    State("iap-receipt-app", "value"),
    State("iap-month", "value"),
    State("iap-view-toggle", "value"),
    prevent_initial_call=True,
)
def generate_receipt(n_clicks, selected_app, selected_month, view_mode):
    if not n_clicks or not selected_app:
        return no_update, html.Span(
            "⚠ Please select an app first.",
            style={
                "color": NEUTRAL,
                "fontSize": "12px",
                "marginTop": "28px",
                "display": "block",
            },
        )

    is_fiscal = view_mode == "fiscal"

    try:
        fee_lookup = _load_fee_lookup()

        if is_fiscal:
            # ── Fiscal mode: settlement data ──
            fiscal_raw = _load_apple_financial()
            fiscal_refunds = _load_apple_financial_refunds()
            fiscal = _compute_fiscal_breakdown(fiscal_raw, fee_lookup, fiscal_refunds)

            # Determine fiscal period
            if selected_month and selected_month.startswith("fiscal:"):
                fp = selected_month.split(":")[1]
            elif not fiscal.empty:
                fp = sorted(fiscal["fiscal_period"].unique(), reverse=True)[0]
            else:
                return no_update, html.Span(
                    "No fiscal data available.",
                    style={"color": NEUTRAL, "fontSize": "12px"},
                )

            apple_month = _fiscal_to_apple_month(fp)

            # Filter Apple data
            app_fiscal = fiscal[
                (fiscal["application_name"] == selected_app)
                & (fiscal["fiscal_period"] == fp)
            ]
            if app_fiscal.empty:
                return no_update, html.Span(
                    f"No settlement data for {selected_app} in fiscal period {fp}.",
                    style={
                        "color": NEUTRAL,
                        "fontSize": "12px",
                        "marginTop": "28px",
                        "display": "block",
                    },
                )

            a_sales = float(app_fiscal["sales"].sum())
            a_units = int(app_fiscal["total_units"].sum())
            a_pf = float(app_fiscal["platform_fee"].sum())
            a_pf_pct = round(a_pf / a_sales * 100, 1) if a_sales > 0 else 0.0
            a_ref = float(app_fiscal["refund_amount"].sum())
            kliq_pct = float(app_fiscal["kliq_fee_pct"].iloc[0])

            # Google data for same month
            google_raw = _load_google_monthly()
            _canon = {n.lower(): n for n in fiscal_raw["application_name"].unique() if n}
            for _df in [google_raw]:
                if not _df.empty and "application_name" in _df.columns:
                    _df["application_name"] = _df["application_name"].apply(
                        lambda x: _canon.get(x.lower(), x) if isinstance(x, str) else x
                    )
            google = _compute_breakdown(
                google_raw, fee_lookup, GOOGLE_FEE_PCT, "Google", _load_google_refunds()
            )
            g_row = google[
                (google["application_name"] == selected_app)
                & (google["month"] == apple_month)
            ]
            g_sales = float(g_row["sales"].sum()) if not g_row.empty else 0.0
            g_units = int(g_row["total_units"].sum()) if not g_row.empty else 0
            g_ref = float(g_row["refund_amount"].sum()) if not g_row.empty else 0.0
            g_payout = float(g_row["payout"].sum()) if not g_row.empty else 0.0

            total_payout = float(app_fiscal["payout"].sum()) + g_payout

            # Period info
            periods = _load_fiscal_periods()
            pr = periods[periods["fiscal_period"] == fp]
            try:
                period_start_str = pd.to_datetime(pr.iloc[0]["period_start"]).strftime(
                    "%b %d, %Y"
                )
                period_end_str = pd.to_datetime(pr.iloc[0]["period_end"]).strftime(
                    "%b %d, %Y"
                )
            except Exception:
                period_start_str, period_end_str = "", ""
            due_date = _compute_payment_due_date(apple_month)

            # Product details (fiscal)
            fiscal_products = _load_apple_financial_product_details()
            google_products = _load_google_product_details()
            for _df in [google_products]:
                if not _df.empty and "application_name" in _df.columns:
                    _df["application_name"] = _df["application_name"].apply(
                        lambda x: _canon.get(x.lower(), x) if isinstance(x, str) else x
                    )

            prod_rows = []
            if not fiscal_products.empty:
                filt = fiscal_products[
                    (fiscal_products["application_name"] == selected_app)
                    & (fiscal_products["fiscal_period"] == fp)
                ]
                for _, r in filt.sort_values("revenue_usd", ascending=False).iterrows():
                    prod_rows.append(
                        {
                            "platform": "Apple",
                            "product_name": r.get("product_name", "—"),
                            "sub_type": "—",
                            "period": "—",
                            "units": int(r.get("units", 0)),
                            "revenue_usd": float(r.get("revenue_usd", 0)),
                        }
                    )
            if not google_products.empty:
                filt = google_products[
                    (google_products["application_name"] == selected_app)
                    & (google_products["month"] == apple_month)
                ]
                for _, r in filt.sort_values("revenue_usd", ascending=False).iterrows():
                    prod_rows.append(
                        {
                            "platform": "Google",
                            "product_name": r.get("product_name", "—"),
                            "sub_type": r.get("sub_type", "—"),
                            "period": r.get("period", "—"),
                            "units": int(r.get("units", 0)),
                            "revenue_usd": float(r.get("revenue_usd", 0)),
                        }
                    )

            pdf_bytes = generate_receipt_pdf(
                app_name=selected_app,
                month=apple_month,
                apple_sales=a_sales,
                apple_units=a_units,
                google_sales=g_sales,
                google_units=g_units,
                kliq_fee_pct=kliq_pct,
                total_payout=total_payout,
                apple_refunds=a_ref,
                google_refunds=g_ref,
                product_details=prod_rows if prod_rows else None,
                is_fiscal=True,
                fiscal_period=fp,
                period_start=period_start_str,
                period_end=period_end_str,
                apple_platform_fee=a_pf,
                apple_platform_fee_pct=a_pf_pct,
                payment_due_date=due_date,
            )

            safe_name = selected_app.replace(" ", "_").replace("/", "_")
            filename = f"KLIQ_Settlement_{safe_name}_{fp}.pdf"
            status = html.Span(
                f"✅ Settlement receipt for {selected_app} (Fiscal {fp})",
                style={
                    "color": GREEN,
                    "fontSize": "12px",
                    "fontWeight": "600",
                    "marginTop": "28px",
                    "display": "block",
                },
            )
            return dcc.send_bytes(pdf_bytes, filename), status

        else:
            # ── Calendar mode: unchanged ──
            apple_raw = _load_apple_monthly()
            google_raw = _load_google_monthly()
            apple_refunds = _load_apple_refunds()
            google_refunds = _load_google_refunds()

            _canon = {n.lower(): n for n in apple_raw["application_name"].unique() if n}
            for _df in [google_raw, google_refunds]:
                if not _df.empty and "application_name" in _df.columns:
                    _df["application_name"] = _df["application_name"].apply(
                        lambda x: _canon.get(x.lower(), x) if isinstance(x, str) else x
                    )

            apple = _compute_breakdown(
                apple_raw, fee_lookup, APPLE_FEE_PCT, "Apple", apple_refunds
            )
            google = _compute_breakdown(
                google_raw, fee_lookup, GOOGLE_FEE_PCT, "Google", google_refunds
            )
            combined = pd.concat([apple, google], ignore_index=True)

            actual_month = selected_month
            if not selected_month or selected_month == "All Months":
                if not combined.empty:
                    actual_month = sorted(combined["month"].unique(), reverse=True)[0]
                else:
                    return no_update, html.Span(
                        "No data available.",
                        style={"color": NEUTRAL, "fontSize": "12px"},
                    )

            month_data = combined[
                (combined["application_name"] == selected_app)
                & (combined["month"] == actual_month)
            ]
            if month_data.empty:
                return no_update, html.Span(
                    f"No data for {selected_app} in {actual_month}.",
                    style={
                        "color": NEUTRAL,
                        "fontSize": "12px",
                        "marginTop": "28px",
                        "display": "block",
                    },
                )

            apple_row = month_data[month_data["platform"] == "Apple"]
            google_row = month_data[month_data["platform"] == "Google"]
            apple_sales = (
                float(apple_row["sales"].sum()) if not apple_row.empty else 0.0
            )
            apple_units = (
                int(apple_row["total_units"].sum()) if not apple_row.empty else 0
            )
            google_sales = (
                float(google_row["sales"].sum()) if not google_row.empty else 0.0
            )
            google_units = (
                int(google_row["total_units"].sum()) if not google_row.empty else 0
            )
            kliq_pct = (
                float(month_data["kliq_fee_pct"].iloc[0])
                if not month_data.empty
                else 0.0
            )
            total_payout = float(month_data["payout"].sum())
            apple_ref = (
                float(apple_row["refund_amount"].sum()) if not apple_row.empty else 0.0
            )
            google_ref = (
                float(google_row["refund_amount"].sum())
                if not google_row.empty
                else 0.0
            )

            apple_products = _load_apple_product_details()
            google_products = _load_google_product_details()
            for _df in [google_products]:
                if not _df.empty and "application_name" in _df.columns:
                    _df["application_name"] = _df["application_name"].apply(
                        lambda x: _canon.get(x.lower(), x) if isinstance(x, str) else x
                    )

            prod_rows = []
            for src, plat in [
                (apple_products, "Apple"),
                (google_products, "Google"),
            ]:
                if src is not None and not src.empty:
                    filt = src[
                        (src["application_name"] == selected_app)
                        & (src["month"] == actual_month)
                    ]
                    for _, pr in filt.sort_values(
                        "revenue_usd", ascending=False
                    ).iterrows():
                        prod_rows.append(
                            {
                                "platform": plat,
                                "product_name": pr.get("product_name", "—"),
                                "sub_type": pr.get("sub_type", "—"),
                                "period": pr.get("period", "—"),
                                "units": int(pr.get("units", 0)),
                                "revenue_usd": float(pr.get("revenue_usd", 0)),
                            }
                        )

            pdf_bytes = generate_receipt_pdf(
                app_name=selected_app,
                month=actual_month,
                apple_sales=apple_sales,
                apple_units=apple_units,
                google_sales=google_sales,
                google_units=google_units,
                kliq_fee_pct=kliq_pct,
                total_payout=total_payout,
                apple_refunds=apple_ref,
                google_refunds=google_ref,
                product_details=prod_rows if prod_rows else None,
            )

            safe_name = selected_app.replace(" ", "_").replace("/", "_")
            filename = f"KLIQ_Receipt_{safe_name}_{actual_month}.pdf"
            status = html.Span(
                f"✅ Receipt generated for {selected_app} ({actual_month})",
                style={
                    "color": GREEN,
                    "fontSize": "12px",
                    "fontWeight": "600",
                    "marginTop": "28px",
                    "display": "block",
                },
            )
            return dcc.send_bytes(pdf_bytes, filename), status

    except Exception as e:
        return no_update, html.Span(
            f"❌ Error: {str(e)[:100]}",
            style={
                "color": "#DC2626",
                "fontSize": "12px",
                "marginTop": "28px",
                "display": "block",
            },
        )


@callback(
    Output("iap-product-details", "children"),
    Input("iap-app-filter", "value"),
    Input("iap-platform", "value"),
    Input("iap-month", "value"),
    Input("iap-view-toggle", "value"),
)
def update_product_details(selected_apps, platform_filter, selected_month, view_mode):
    is_fiscal = view_mode == "fiscal"
    try:
        if is_fiscal:
            apple_products = _load_apple_financial_product_details()
            if not apple_products.empty:
                apple_products["sub_type"] = "—"
                apple_products["period"] = "—"
                apple_products["month"] = apple_products["apple_month"]
        else:
            apple_products = _load_apple_product_details()

        google_products = _load_google_product_details()

        # Normalise Google names
        apple_names = (
            apple_products["application_name"].unique()
            if not apple_products.empty
            else []
        )
        _canon = {n.lower(): n for n in apple_names if n}
        for _df in [google_products]:
            if not _df.empty and "application_name" in _df.columns:
                _df["application_name"] = _df["application_name"].apply(
                    lambda x: _canon.get(x.lower(), x) if isinstance(x, str) else x
                )

        # Determine actual month
        if is_fiscal and selected_month and selected_month.startswith("fiscal:"):
            fp = selected_month.split(":")[1]
            actual_month = _fiscal_to_apple_month(fp)
        elif selected_month and selected_month not in ("All Months", "All Periods"):
            actual_month = selected_month
        else:
            all_months = set()
            if not apple_products.empty:
                all_months.update(apple_products["month"].unique())
            if not google_products.empty:
                all_months.update(google_products["month"].unique())
            if all_months:
                actual_month = sorted(all_months, reverse=True)[0]
            else:
                return html.P("No product data available.", style={"color": NEUTRAL})

        # Filter by month
        ap = (
            apple_products[apple_products["month"] == actual_month].copy()
            if not apple_products.empty
            else pd.DataFrame()
        )
        gp = (
            google_products[google_products["month"] == actual_month].copy()
            if not google_products.empty
            else pd.DataFrame()
        )

        # Filter by selected apps
        if selected_apps:
            if not ap.empty:
                ap = ap[ap["application_name"].isin(selected_apps)]
            if not gp.empty:
                gp = gp[gp["application_name"].isin(selected_apps)]

        # Filter by platform
        if platform_filter == "Apple":
            gp = pd.DataFrame()
        elif platform_filter == "Google":
            ap = pd.DataFrame()

        # Tag and combine
        if not ap.empty:
            ap["platform"] = "Apple"
        if not gp.empty:
            gp["platform"] = "Google"

        all_prods = pd.concat([ap, gp], ignore_index=True)

        if all_prods.empty:
            return html.P(
                f"No product details for {actual_month}.", style={"color": NEUTRAL}
            )

        # Build per-app sections
        sections = []
        for app_name in sorted(all_prods["application_name"].unique()):
            app_data = all_prods[all_prods["application_name"] == app_name].sort_values(
                "revenue_usd", ascending=False
            )
            total_rev = app_data["revenue_usd"].sum()
            total_units = app_data["units"].sum()

            # App header
            sections.append(
                html.Div(
                    [
                        html.Span(
                            app_name,
                            style={
                                "fontWeight": "700",
                                "color": DARK,
                                "fontSize": "15px",
                            },
                        ),
                        html.Span(
                            f"{int(total_units)} units · ${total_rev:,.2f} revenue",
                            style={
                                "float": "right",
                                "color": NEUTRAL,
                                "fontSize": "13px",
                            },
                        ),
                    ],
                    style={
                        "background": BG_CARD,
                        "borderRadius": "12px",
                        "padding": "14px 18px",
                        "margin": "8px 0 4px",
                        "boxShadow": SHADOW_CARD,
                    },
                )
            )

            # Product table
            display_cols = [
                "platform",
                "product_name",
                "sub_type",
                "period",
                "units",
                "revenue_usd",
            ]
            display_cols = [c for c in display_cols if c in app_data.columns]
            display_df = app_data[display_cols].copy()
            col_map = {
                "platform": "Platform",
                "product_name": "Product",
                "sub_type": "Type",
                "period": "Period",
                "units": "Units",
                "revenue_usd": "Revenue (USD)",
            }
            display_df.columns = [col_map.get(c, c) for c in display_df.columns]
            if "Revenue (USD)" in display_df.columns:
                display_df["Revenue (USD)"] = display_df["Revenue (USD)"].round(2)

            sections.append(
                dash_table.DataTable(
                    data=display_df.to_dict("records"),
                    columns=[
                        (
                            {
                                "name": c,
                                "id": c,
                                "type": "numeric",
                                "format": {"specifier": "$,.2f"},
                            }
                            if c == "Revenue (USD)"
                            else {"name": c, "id": c}
                        )
                        for c in display_df.columns
                    ],
                    style_table={"overflowX": "auto", "marginBottom": "16px"},
                    style_cell={
                        "fontSize": "12px",
                        "padding": "5px 10px",
                        "fontFamily": "Sora",
                        "textAlign": "left",
                    },
                    style_header={
                        "fontWeight": "600",
                        "backgroundColor": DARK,
                        "color": "white",
                        "fontSize": "11px",
                    },
                    style_data_conditional=[
                        {
                            "if": {"filter_query": '{Platform} = "Apple"'},
                            "backgroundColor": "#EBF5FB",
                        },
                        {
                            "if": {"filter_query": '{Platform} = "Google"'},
                            "backgroundColor": "#E8F8F5",
                        },
                        {
                            "if": {"column_id": "Revenue (USD)"},
                            "textAlign": "right",
                            "fontWeight": "600",
                        },
                        {"if": {"column_id": "Units"}, "textAlign": "right"},
                    ],
                    page_size=20,
                )
            )

        return html.Div(sections)

    except Exception as e:
        return html.P(
            f"Error loading product details: {str(e)[:100]}", style={"color": NEUTRAL}
        )
