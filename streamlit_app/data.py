"""
Shared data loading functions for KLIQ Growth Dashboard.
All queries hit rcwl-data.powerbi_dashboard via BigQuery.

Table schemas (from actual BigQuery):
  d1_growth_metrics:       date, metric_name, metric_value
  d1_revenue_summary:      date, metric_name, metric_value
  d1_cohort_retention:     cohort_month, months_since_signup, retained_users, cohort_size, retention_rate
  d1_churn_analysis:       application_name, application_id, ... (wide table, per-app)
  d1_onboarding_funnel:    date, funnel_step, step_order, value
  d1_device_type:          date, device_type, value
  d1_coach_summary:        application_name, application_id, total_gmv, total_app_fee_to_kliq, latest_mau, ...
  d1_coach_growth_stages:  application_name, total_gmv, mrr, total_subs, growth_stage, ...
  d1_coach_gmv_timeline:   application_name, month, gmv
  d1_coach_engagement:     application_name, month, metric, value
  d1_app_health_score:     application_name, ... (wide table)
  d1_feature_retention_impact: application_name, feature, retention_if_used, retention_if_not_used, lift_pp
  d1_firstweek_retention:  application_name, active_days_first_week, retention_30d_pct, users
  d1_coach_onboarding_funnel: step, stage, coaches, pct_of_total, drop_off_pct
  d1_coach_retention_curve: period, coaches, pct
  d2_app_lookup:           application_id, application_name, created_at
  d2_engagement:           application_id, date, metric, value
  d2_subscriptions_revenue: application_id, date, metric, value
  d1_engagement_funnel:    date, funnel_step, step_order, value
  d2_user_overview:        application_id, application_name, total_users, talent_users, regular_users, web_users, app_users
  d2_dau:                  application_id, date, dau
  d2_mau:                  application_id, month, mau
  d1_ga4_acquisition:      date, source, medium, campaign, device_type, os, country, unique_users
  d1_ga4_traffic:          date, channel, medium, device_type, country, sessions
  d1_ga4_funnel:           date, funnel_step, step_order, device_type, source, unique_users
  d1_three_source_revenue: application_name, month, revenue_source, transactions, unique_invoices, gmv, kliq_revenue
  d1_revenue_by_channel:   (check at runtime)
  d1_kliq_revenue:         (check at runtime)
  d1_unified_revenue:      application_name, application_id, month, month_label, month_sort, revenue, revenue_source
                           ** This is the source of truth for Total GMV (Stripe $787K + Apple IAP $268K = ~$1.05M) **
  d1_inapp_purchases:      application_name, month, purchases, unique_buyers, ...
  d1_recurring_payments:   application_name, month, platform_type, recurring_payments, unique_users
  d1_ios_downloads:        application_name, month, ios_downloads, first_downloads, redownloads
  d1_app_device_breakdown: application_name, device, unique_users, total_events
  d1_app_downloads:        application_name, ios_first_downloads, ios_redownloads, ios_total_downloads, kliq_registered_users
"""

import os
import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import google.auth

JOB_PROJECT = (
    "rcwl-development"  # project where jobs run (SA has bigquery.jobs.create here)
)
DATA_PROJECT = "rcwl-data"  # project where data lives
DATASET = "powerbi_dashboard"

# Locate service account key: env var → project root → fallback to ADC
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_KEY = os.path.join(_PROJECT_ROOT, "rcwl-development-0c013e9b5c2b.json")
SERVICE_ACCOUNT_KEY = os.environ.get("GCP_SERVICE_ACCOUNT_KEY", "") or (
    _DEFAULT_KEY if os.path.exists(_DEFAULT_KEY) else ""
)


@st.cache_resource
def get_client(location="EU"):
    if SERVICE_ACCOUNT_KEY and os.path.exists(SERVICE_ACCOUNT_KEY):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_KEY
        )
    else:
        creds, _ = google.auth.default()
    return bigquery.Client(credentials=creds, project=JOB_PROJECT, location=location)


@st.cache_data(ttl=600)
def query(sql, location="EU"):
    """Run a BigQuery query and return a DataFrame. Cached for 10 minutes."""
    client = get_client(location)
    return client.query(sql).to_dataframe()


def T(name):
    """Shorthand for full table reference."""
    return f"`{DATA_PROJECT}.{DATASET}.{name}`"


# ── Growth Overview ──


def load_growth_metrics():
    return query(f"SELECT * FROM {T('d1_growth_metrics')} ORDER BY date")


def load_revenue_summary():
    return query(f"SELECT * FROM {T('d1_revenue_summary')} ORDER BY date")


def load_retention_analysis():
    return query(f"SELECT * FROM {T('d1_retention_analysis')}")


def load_cohort_retention():
    return query(
        f"SELECT * FROM {T('d1_cohort_retention')} ORDER BY cohort, months_since_join"
    )


def load_churn_analysis():
    return query(f"SELECT * FROM {T('d1_churn_analysis')}")


def load_onboarding_funnel():
    return query(f"SELECT * FROM {T('d1_onboarding_funnel')} ORDER BY date, step_order")


def load_engagement_funnel():
    return query(f"SELECT * FROM {T('d1_engagement_funnel')} ORDER BY date, step_order")


def load_activation_score():
    return query(
        f"SELECT * FROM {T('d1_activation_score')} ORDER BY activation_score DESC"
    )


def load_leads_sales():
    return query(f"SELECT * FROM {T('d1_leads_sales')} ORDER BY week_start")


def load_demo_calls():
    return query(f"SELECT * FROM {T('d1_demo_calls')} ORDER BY week_start")


def load_meta_ads():
    return query(f"SELECT * FROM {T('d1_meta_ads')} ORDER BY week_start")


def load_tiktok_ads():
    return query(f"SELECT * FROM {T('d1_tiktok_ads')} ORDER BY week_start")


def load_device_type():
    return query(f"SELECT * FROM {T('d1_device_type')} ORDER BY date")


# ── Coach Deep Dive ──


def load_coach_summary():
    return query(f"SELECT * FROM {T('d1_coach_summary')} ORDER BY total_gmv DESC")


def load_coach_growth_stages():
    return query(f"SELECT * FROM {T('d1_coach_growth_stages')}")


def load_coach_gmv_timeline():
    return query(f"SELECT * FROM {T('d1_coach_gmv_timeline')} ORDER BY month")


def load_coach_engagement():
    return query(f"SELECT * FROM {T('d1_coach_engagement')}")


def load_app_health_score():
    return query(f"SELECT * FROM {T('d1_app_health_score')}")


def load_feature_retention_impact():
    return query(f"SELECT * FROM {T('d1_feature_retention_impact')}")


def load_firstweek_retention():
    return query(f"SELECT * FROM {T('d1_firstweek_retention')}")


# ── Coach Activation ──


def load_coach_onboarding_funnel():
    return query(f"SELECT * FROM {T('d1_coach_onboarding_funnel')} ORDER BY step")


def load_coach_retention_curve():
    return query(f"SELECT * FROM {T('d1_coach_retention_curve')}")


def load_coach_signup_patterns():
    return query(f"SELECT * FROM {T('d1_coach_signup_patterns')}")


def load_coach_first_action():
    return query(f"SELECT * FROM {T('d1_coach_first_action')}")


def load_coach_time_to_action():
    return query(f"SELECT * FROM {T('d1_coach_time_to_action')}")


def load_coach_action_impact():
    return query(f"SELECT * FROM {T('d1_coach_action_impact')}")


def load_coach_device_impact():
    return query(f"SELECT * FROM {T('d1_coach_device_impact')}")


# ── App Health ──


def load_app_lookup():
    return query(f"SELECT * FROM {T('d2_app_lookup')}")


def load_app_engagement_d2():
    return query(f"SELECT * FROM {T('d2_engagement')} ORDER BY date")


def load_app_subscriptions():
    return query(f"SELECT * FROM {T('d2_subscriptions_revenue')} ORDER BY date")


def load_app_user_overview():
    return query(f"SELECT * FROM {T('d2_user_overview')}")


def load_app_dau():
    return query(f"SELECT * FROM {T('d2_dau')} ORDER BY date")


def load_app_mau():
    return query(f"SELECT * FROM {T('d2_mau')} ORDER BY month")


def load_app_device_breakdown():
    return query(f"SELECT * FROM {T('d1_app_device_breakdown')}")


def load_app_downloads():
    return query(f"SELECT * FROM {T('d1_app_downloads')}")


# ── Acquisition (GA4) ──


def load_ga4_acquisition():
    return query(f"SELECT * FROM {T('d1_ga4_acquisition')} ORDER BY date")


def load_ga4_traffic():
    return query(f"SELECT * FROM {T('d1_ga4_traffic')} ORDER BY date")


def load_ga4_funnel():
    return query(f"SELECT * FROM {T('d1_ga4_funnel')} ORDER BY date")


# ── Revenue ──


def load_three_source_revenue():
    return query(f"SELECT * FROM {T('d1_three_source_revenue')}")


def load_unified_revenue():
    """Combined Stripe + Apple IAP revenue per app per month. This is the source of truth for Total GMV."""
    return query(f"SELECT * FROM {T('d1_unified_revenue')} ORDER BY month_sort DESC")


def load_inapp_purchases():
    return query(f"SELECT * FROM {T('d1_inapp_purchases')} ORDER BY month")


def load_revenue_by_channel():
    return query(f"SELECT * FROM {T('d1_revenue_by_channel')}")


def load_recurring_payments():
    return query(f"SELECT * FROM {T('d1_recurring_payments')} ORDER BY month")


def load_appstore_sales():
    return query(f"SELECT * FROM {T('d1_appstore_sales')} LIMIT 5000")


def load_ios_downloads():
    return query(f"SELECT * FROM {T('d1_ios_downloads')} ORDER BY month")


def load_kliq_revenue():
    return query(f"SELECT * FROM {T('d1_kliq_revenue')}")


def load_invoice_revenue():
    return query(f"SELECT * FROM {T('d1_invoice_revenue')}")


def load_appfee_revenue():
    return query(f"SELECT * FROM {T('d1_appfee_revenue')}")


# ── Coach Growth Strategy ──

_FX_CTE = """
    fx_rates AS (
        SELECT currency, rate FROM UNNEST([
            STRUCT("USD" AS currency, 1.0 AS rate),
            STRUCT("GBP", 1.27), STRUCT("EUR", 1.08), STRUCT("AUD", 0.64),
            STRUCT("CAD", 0.72), STRUCT("CHF", 1.13), STRUCT("DKK", 0.145),
            STRUCT("NOK", 0.093), STRUCT("SEK", 0.095), STRUCT("NZD", 0.60),
            STRUCT("SGD", 0.75), STRUCT("HUF", 0.0027), STRUCT("CLP", 0.00105),
            STRUCT("COP", 0.00024), STRUCT("CZK", 0.042), STRUCT("PLN", 0.25),
            STRUCT("BRL", 0.19), STRUCT("MXN", 0.055), STRUCT("TRY", 0.031),
            STRUCT("RUB", 0.011), STRUCT("ILS", 0.28), STRUCT("SAR", 0.267),
            STRUCT("AED", 0.272), STRUCT("INR", 0.012), STRUCT("ZAR", 0.054),
            STRUCT("RON", 0.22)
        ])
    )
"""


@st.cache_data(ttl=600)
def load_growth_strategy_app_stats():
    """Per-app stats for growth strategy: revenue, engagement, retention, LTV."""
    sql = f"""
    WITH {_FX_CTE},
    sku_map AS (
        SELECT DISTINCT product_id, application_name
        FROM {T('d1_inapp_products')}
    ),
    apple_rev AS (
        SELECT COALESCE(m.application_name, 'Unknown') AS app,
               ROUND(SUM(SAFE_CAST(s.customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0) * SAFE_CAST(s.units AS INT64)), 2) AS apple_sales,
               COUNT(DISTINCT FORMAT_DATE('%Y-%m', s.report_date)) AS apple_months
        FROM {T('d1_appstore_sales')} s
        LEFT JOIN sku_map m ON s.sku = m.product_id
        LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
        WHERE s.product_type_identifier IN ('IA1', 'IAY') AND SAFE_CAST(s.customer_price AS FLOAT64) > 0
        GROUP BY app
    ),
    apple_sku_prices AS (
        SELECT sku,
            ROUND(AVG(SAFE_CAST(customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0)), 2) AS avg_price_usd
        FROM {T('d1_appstore_sales')} s
        LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
        WHERE s.product_type_identifier IN ('IA1', 'IAY') AND SAFE_CAST(customer_price AS FLOAT64) > 0
        GROUP BY sku
    ),
    ios_avg AS (
        SELECT ROUND(AVG(SAFE_CAST(customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0)), 2) AS fallback_price
        FROM {T('d1_appstore_sales')} s
        LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
        WHERE s.product_type_identifier IN ('IA1', 'IAY') AND SAFE_CAST(customer_price AS FLOAT64) > 0
    ),
    google_rev AS (
        SELECT a.application_name AS app,
               ROUND(SUM(COALESCE(ap.avg_price_usd, iavg.fallback_price)), 2) AS google_sales,
               COUNT(DISTINCT FORMAT_DATE('%Y-%m', DATE(e.event_date))) AS google_months
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        LEFT JOIN apple_sku_prices ap ON JSON_VALUE(e.data, '$.in_app_product_id') = ap.sku
        CROSS JOIN ios_avg iavg
        WHERE e.event_name = 'purchase_success' AND a.application_name IS NOT NULL
        GROUP BY app
    ),
    app_events AS (
        SELECT a.application_name AS app,
            COUNTIF(e.event_name = 'purchase_success') AS purchases,
            COUNTIF(e.event_name = 'recurring_payment') AS recurring_payments,
            COUNTIF(e.event_name = 'user_subscribed') AS new_subscribers,
            COUNTIF(e.event_name = 'cancels_subscription') AS cancellations,
            COUNTIF(e.event_name = 'live_session_created') AS livestreams,
            COUNTIF(e.event_name = 'live_session_joined') AS live_joins,
            COUNTIF(e.event_name = 'completes_program_workout') AS workouts,
            COUNTIF(e.event_name IN ('post_on_community', 'post_on_community_feed_with_photo', 'post_on_community_feed_with_voice_notes')) AS community_posts,
            COUNTIF(e.event_name = 'app_opened') AS app_opens,
            COUNTIF(e.event_name = 'publish_module') AS modules_published,
            COUNTIF(e.event_name = 'publishes_program') AS programs_published,
            COUNT(DISTINCT FORMAT_DATE('%Y-%m', DATE(e.event_date))) AS event_months
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        WHERE a.application_name IS NOT NULL
        GROUP BY app
    ),
    apps_meta AS (
        SELECT application_name AS app, DATE(created_at) AS created_date
        FROM `{DATA_PROJECT}.prod_dataset.applications`
        WHERE application_name IS NOT NULL
    ),
    fees AS (
        SELECT application_name AS app, kliq_fee_pct
        FROM {T('d1_app_fee_lookup')}
        WHERE kliq_fee_pct IS NOT NULL
    )
    SELECT
        COALESCE(ae.app, ar.app, gr.app) AS app,
        am.created_date,
        COALESCE(ar.apple_sales, 0) + COALESCE(gr.google_sales, 0) AS iap_revenue,
        COALESCE(ar.apple_sales, 0) AS apple_sales,
        COALESCE(gr.google_sales, 0) AS google_sales,
        GREATEST(COALESCE(ar.apple_months, 0), COALESCE(gr.google_months, 0)) AS active_rev_months,
        COALESCE(ae.purchases, 0) AS purchases,
        COALESCE(ae.recurring_payments, 0) AS recurring_payments,
        COALESCE(ae.new_subscribers, 0) AS new_subscribers,
        COALESCE(ae.cancellations, 0) AS cancellations,
        COALESCE(ae.livestreams, 0) AS livestreams,
        COALESCE(ae.live_joins, 0) AS live_joins,
        COALESCE(ae.workouts, 0) AS workouts,
        COALESCE(ae.community_posts, 0) AS community_posts,
        COALESCE(ae.app_opens, 0) AS app_opens,
        COALESCE(ae.modules_published, 0) AS modules_published,
        COALESCE(ae.programs_published, 0) AS programs_published,
        COALESCE(ae.event_months, 0) AS event_months,
        COALESCE(f.kliq_fee_pct, 0) AS kliq_fee_pct
    FROM app_events ae
    FULL OUTER JOIN apple_rev ar ON ae.app = ar.app
    FULL OUTER JOIN google_rev gr ON COALESCE(ae.app, ar.app) = gr.app
    LEFT JOIN apps_meta am ON COALESCE(ae.app, ar.app, gr.app) = am.app
    LEFT JOIN fees f ON COALESCE(ae.app, ar.app, gr.app) = f.app
    WHERE COALESCE(ae.app_opens, 0) > 0
    ORDER BY iap_revenue DESC
    """
    return query(sql)


@st.cache_data(ttl=600)
def load_growth_strategy_monthly():
    """Monthly revenue + engagement for cohort/retention analysis."""
    sql = f"""
    WITH {_FX_CTE},
    sku_map AS (
        SELECT DISTINCT product_id, application_name
        FROM {T('d1_inapp_products')}
    ),
    apple_monthly AS (
        SELECT COALESCE(m.application_name, 'Unknown') AS app,
               FORMAT_DATE('%Y-%m', s.report_date) AS month,
               ROUND(SUM(SAFE_CAST(s.customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0) * SAFE_CAST(s.units AS INT64)), 2) AS sales
        FROM {T('d1_appstore_sales')} s
        LEFT JOIN sku_map m ON s.sku = m.product_id
        LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
        WHERE s.product_type_identifier IN ('IA1', 'IAY') AND SAFE_CAST(s.customer_price AS FLOAT64) > 0
        GROUP BY app, month
    ),
    apple_sku_prices AS (
        SELECT sku,
            ROUND(AVG(SAFE_CAST(customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0)), 2) AS avg_price_usd
        FROM {T('d1_appstore_sales')} s
        LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
        WHERE s.product_type_identifier IN ('IA1', 'IAY') AND SAFE_CAST(customer_price AS FLOAT64) > 0
        GROUP BY sku
    ),
    ios_avg AS (
        SELECT ROUND(AVG(SAFE_CAST(customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0)), 2) AS fallback_price
        FROM {T('d1_appstore_sales')} s
        LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
        WHERE s.product_type_identifier IN ('IA1', 'IAY') AND SAFE_CAST(customer_price AS FLOAT64) > 0
    ),
    google_monthly AS (
        SELECT a.application_name AS app,
               FORMAT_DATE('%Y-%m', DATE(e.event_date)) AS month,
               ROUND(SUM(COALESCE(ap.avg_price_usd, iavg.fallback_price)), 2) AS sales
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        LEFT JOIN apple_sku_prices ap ON JSON_VALUE(e.data, '$.in_app_product_id') = ap.sku
        CROSS JOIN ios_avg iavg
        WHERE e.event_name = 'purchase_success' AND a.application_name IS NOT NULL
        GROUP BY app, month
    ),
    combined_rev AS (
        SELECT app, month, SUM(sales) AS total_sales FROM (
            SELECT * FROM apple_monthly UNION ALL SELECT * FROM google_monthly
        ) GROUP BY app, month
    ),
    monthly_events AS (
        SELECT a.application_name AS app,
            FORMAT_DATE('%Y-%m', DATE(e.event_date)) AS month,
            COUNTIF(e.event_name = 'user_subscribed') AS new_subs,
            COUNTIF(e.event_name = 'cancels_subscription') AS cancels,
            COUNTIF(e.event_name = 'purchase_success') AS purchases,
            COUNTIF(e.event_name = 'recurring_payment') AS recurring,
            COUNTIF(e.event_name = 'live_session_created') AS livestreams,
            COUNTIF(e.event_name = 'app_opened') AS app_opens
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        WHERE a.application_name IS NOT NULL
        GROUP BY app, month
    )
    SELECT
        COALESCE(r.app, e.app) AS app,
        COALESCE(r.month, e.month) AS month,
        COALESCE(r.total_sales, 0) AS total_sales,
        COALESCE(e.new_subs, 0) AS new_subs,
        COALESCE(e.cancels, 0) AS cancels,
        COALESCE(e.purchases, 0) AS purchases,
        COALESCE(e.recurring, 0) AS recurring,
        COALESCE(e.livestreams, 0) AS livestreams,
        COALESCE(e.app_opens, 0) AS app_opens
    FROM combined_rev r
    FULL OUTER JOIN monthly_events e ON r.app = e.app AND r.month = e.month
    WHERE COALESCE(r.total_sales, 0) > 0 OR COALESCE(e.app_opens, 0) > 0
    ORDER BY app, month
    """
    return query(sql)


# ── Feature Adoption ──

# Friendly labels for raw event names
FEATURE_LABELS = {
    "app_opened": "App Opens",
    "visits_community_page": "Community Page Visits",
    "engage_with_blog_post": "Blog Engagement",
    "visits_blog": "Blog Visits",
    "visits_library_page": "Library Page Visits",
    "completes_program_workout": "Workout Completions",
    "like_on_community_post": "Community Likes",
    "visits_program_detail_page": "Program Detail Views",
    "completes_library_video": "Library Video Completions",
    "visits_program_page": "Program Page Visits",
    "starts_library_video": "Library Video Starts",
    "engages_with_recipe": "Recipe Engagement",
    "ends_library_video": "Library Video Ends",
    "starts_past_session": "Past Session Starts",
    "replies_on_community": "Community Replies",
    "ends_past_session": "Past Session Ends",
    "commented_in_live_session": "Live Session Comments",
    "post_on_community_feed_with_photo": "Community Photo Posts",
    "visits_nutrition_page": "Nutrition Page Visits",
    "recurring_payment": "Recurring Payments",
    "live_session_joined": "Live Session Joins",
    "post_comment_in_past_session": "Past Session Comments",
    "checkout_completion": "Checkout Completions",
    "completes_past_session": "Past Session Completions",
    "start_purchase": "Purchase Starts",
    "acknowledge_purchase": "Purchase Acknowledged",
    "starts_program": "Program Starts",
    "user_subscribed": "New Subscriptions",
    "favourited_session_video": "Favourited Sessions",
    "create_module": "Modules Created",
    "favourites_recipe": "Favourited Recipes",
    "cancels_subscription": "Cancellations",
    "post_on_community": "Community Posts",
    "edit_module": "Modules Edited",
    "publish_module": "Modules Published",
    "purchase_cancelled": "Purchase Cancelled",
    "verify_purchase": "Purchase Verified",
    "live_session_created": "Live Sessions Created",
    "purchase_success": "Successful Purchases",
    "valid_purchase": "Valid Purchases",
    "saved_post": "Saved Posts",
    "logged_in_visitor": "Logged-In Visitors",
    "promo_code_used_talent": "Promo Code Used",
    "connects_health_device": "Health Device Connected",
    "visits_course_blog": "Course Blog Visits",
    "completes_program": "Program Completions",
    "publishes_program": "Programs Published",
    "post_on_community_feed_with_voice_notes": "Community Voice Notes",
    "completed_1_to_1_session": "1-to-1 Sessions Completed",
    "creates_program": "Programs Created",
    "1_to_1_session_schedule": "1-to-1 Sessions Scheduled",
}


@st.cache_data(ttl=600)
def load_feature_adoption_platform():
    """Platform-wide feature adoption: event counts, unique apps, monthly span."""
    sql = f"""
    WITH events AS (
        SELECT
            e.event_name,
            a.application_name,
            FORMAT_DATE('%Y-%m', DATE(e.event_date)) AS month,
            COUNT(*) AS cnt
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        WHERE a.application_name IS NOT NULL
          AND e.event_name NOT LIKE 'onboarding%'
          AND e.event_name NOT LIKE 'self_serve%'
        GROUP BY e.event_name, a.application_name, month
    )
    SELECT
        event_name,
        SUM(cnt) AS total_events,
        COUNT(DISTINCT application_name) AS apps_using,
        COUNT(DISTINCT month) AS months_active,
        MIN(month) AS first_seen,
        MAX(month) AS last_seen
    FROM events
    GROUP BY event_name
    ORDER BY total_events DESC
    """
    return query(sql)


@st.cache_data(ttl=600)
def load_feature_adoption_per_app():
    """Per-app feature usage: which features each app uses and how much."""
    sql = f"""
    SELECT
        a.application_name AS app,
        e.event_name,
        COUNT(*) AS event_count,
        COUNT(DISTINCT FORMAT_DATE('%Y-%m', DATE(e.event_date))) AS months_used
    FROM `{DATA_PROJECT}.prod_dataset.events` e
    LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
    WHERE a.application_name IS NOT NULL
      AND e.event_name NOT LIKE 'onboarding%'
      AND e.event_name NOT LIKE 'self_serve%'
    GROUP BY app, e.event_name
    ORDER BY app, event_count DESC
    """
    return query(sql)


@st.cache_data(ttl=600)
def load_feature_monthly_trend():
    """Monthly event counts for top features across the platform."""
    sql = f"""
    SELECT
        e.event_name,
        FORMAT_DATE('%Y-%m', DATE(e.event_date)) AS month,
        COUNT(*) AS event_count,
        COUNT(DISTINCT a.application_name) AS apps_active
    FROM `{DATA_PROJECT}.prod_dataset.events` e
    LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
    WHERE a.application_name IS NOT NULL
      AND e.event_name IN (
        'app_opened', 'visits_community_page', 'engage_with_blog_post',
        'completes_program_workout', 'live_session_joined', 'live_session_created',
        'user_subscribed', 'recurring_payment', 'purchase_success',
        'starts_library_video', 'completes_library_video', 'engages_with_recipe',
        'post_on_community', 'post_on_community_feed_with_photo',
        'publish_module', 'publishes_program', 'starts_program',
        'connects_health_device', 'completed_1_to_1_session'
      )
    GROUP BY e.event_name, month
    ORDER BY month, event_count DESC
    """
    return query(sql)


@st.cache_data(ttl=600)
def load_total_coach_apps():
    """Total number of coach apps on the platform (for uptake % calculation)."""
    sql = f"""
    SELECT COUNT(DISTINCT application_name) AS total_apps
    FROM `{DATA_PROJECT}.prod_dataset.applications`
    WHERE application_name IS NOT NULL
    """
    df = query(sql)
    return int(df.iloc[0]["total_apps"]) if not df.empty else 0


@st.cache_data(ttl=600)
def load_feature_frequency():
    """Avg days between feature usage per app — measures engagement cadence."""
    sql = f"""
    WITH event_dates AS (
        SELECT
            a.application_name AS app,
            e.event_name,
            DATE(e.event_date) AS event_date
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        WHERE a.application_name IS NOT NULL
          AND e.event_name NOT LIKE 'onboarding%'
          AND e.event_name NOT LIKE 'self_serve%'
        GROUP BY app, e.event_name, event_date
    ),
    date_gaps AS (
        SELECT
            app,
            event_name,
            event_date,
            DATE_DIFF(event_date, LAG(event_date) OVER (PARTITION BY app, event_name ORDER BY event_date), DAY) AS days_gap
        FROM event_dates
    )
    SELECT
        event_name,
        ROUND(AVG(days_gap), 1) AS avg_days_between,
        COUNT(DISTINCT app) AS apps_with_repeat,
        ROUND(AVG(days_gap) / 7.0, 1) AS avg_weeks_between
    FROM date_gaps
    WHERE days_gap IS NOT NULL AND days_gap > 0
    GROUP BY event_name
    ORDER BY avg_days_between ASC
    """
    return query(sql)


# Module-type mapping: entity_name values → friendly module names
MODULE_MAP = {
    "live_session": "Live Stream",
    "live_stream": "Live Stream",
    "past_session": "Live Stream",
    "session": "Live Stream",
    "1_to_1": "1-to-1",
    "program": "Program",
    "program_workout": "Program",
    "programs": "Program",
    "workout_program": "Program",
    "ecourse": "eCourse",
    "course": "eCourse",
    "library": "Collections",
    "wellness": "Blog",
    "blog": "Blog",
    "nutrition": "Recipe",
    "recipe": "Recipe",
    "community": "Community",
    "health_device_connected": "Integrations",
    "product": "Subscriptions",
    "inapp_purchase_detail_page": "Subscriptions",
}


@st.cache_data(ttl=600)
def load_module_adoption():
    """Module-level adoption: which apps use which KLIQ modules, event counts, and uptake."""
    sql = f"""
    SELECT
        e.entity_name,
        a.application_name,
        COUNT(*) AS event_count,
        COUNT(DISTINCT FORMAT_DATE('%Y-%m', DATE(e.event_date))) AS months_active,
        MIN(DATE(e.event_date)) AS first_used,
        MAX(DATE(e.event_date)) AS last_used
    FROM `{DATA_PROJECT}.prod_dataset.events` e
    LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
    WHERE a.application_name IS NOT NULL
      AND e.entity_name IS NOT NULL
      AND e.entity_name != ''
      AND e.entity_name NOT IN ('app_opened', 'onboarding', 'self_serve', 'temp_self_serve',
                                 'self_serve_product', 'user', 'customer_behaviour',
                                 'application', 'package')
    GROUP BY e.entity_name, a.application_name
    ORDER BY event_count DESC
    """
    return query(sql)


@st.cache_data(ttl=600)
def load_module_monthly_trend():
    """Monthly event counts per module type across the platform."""
    sql = f"""
    SELECT
        e.entity_name,
        FORMAT_DATE('%Y-%m', DATE(e.event_date)) AS month,
        COUNT(*) AS event_count,
        COUNT(DISTINCT a.application_name) AS apps_active
    FROM `{DATA_PROJECT}.prod_dataset.events` e
    LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
    WHERE a.application_name IS NOT NULL
      AND e.entity_name IS NOT NULL
      AND e.entity_name != ''
      AND e.entity_name NOT IN ('app_opened', 'onboarding', 'self_serve', 'temp_self_serve',
                                 'self_serve_product', 'user', 'customer_behaviour',
                                 'application', 'package')
    GROUP BY e.entity_name, month
    ORDER BY month, event_count DESC
    """
    return query(sql)


@st.cache_data(ttl=600)
def load_coach_types():
    """Coach type from onboarding (coach_type_updated event, data.coach_type field)."""
    sql = f"""
    SELECT
        DATE(event_date) AS event_date,
        JSON_EXTRACT_SCALAR(data, '$.coach_type') AS coach_type
    FROM `{DATA_PROJECT}.prod_dataset.events`
    WHERE event_name = 'coach_type_updated'
      AND data IS NOT NULL
    """
    return query(sql)
