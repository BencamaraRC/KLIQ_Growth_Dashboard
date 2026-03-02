"""
KLIQ Growth Dashboard · Data Layer (Dash version)
Pulls live data from BigQuery (rcwl-data.powerbi_dashboard).
Uses simple TTL caching instead of Streamlit's @st.cache_data.
"""

import os
import logging
import pandas as pd
from time import time, sleep
from google.cloud import bigquery
from google.oauth2 import service_account

log = logging.getLogger("data")
log.setLevel(logging.INFO)
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(
        logging.Formatter("[%(asctime)s] DATA %(levelname)s  %(message)s", "%H:%M:%S")
    )
    log.addHandler(_h)

# ── BigQuery Config ──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_KEY = os.path.join(_PROJECT_ROOT, "rcwl-development-0c013e9b5c2b.json")
SERVICE_ACCOUNT_KEY = os.environ.get("GCP_SERVICE_ACCOUNT_KEY", "") or (
    _DEFAULT_KEY if os.path.exists(_DEFAULT_KEY) else ""
)

DATA_PROJECT = "rcwl-data"
DATASET = "powerbi_dashboard"
BQ_LOCATION = "EU"

_client = None


def _get_client(force_new=False):
    global _client
    if _client is None or force_new:
        if SERVICE_ACCOUNT_KEY and os.path.exists(SERVICE_ACCOUNT_KEY):
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_KEY
            )
            _client = bigquery.Client(
                credentials=creds, project="rcwl-development", location=BQ_LOCATION
            )
        else:
            _client = bigquery.Client(location=BQ_LOCATION)
    return _client


def T(name):
    return f"`{DATA_PROJECT}.{DATASET}.{name}`"


_MAX_RETRIES = 3
_RETRY_BACKOFF = [1, 3, 8]  # seconds


def query(sql, _retries=_MAX_RETRIES):
    """Run a BigQuery SQL query with retry logic. Returns DataFrame or empty DataFrame."""
    last_err = None
    for attempt in range(_retries):
        try:
            client = _get_client(force_new=(attempt > 0))
            df = client.query(sql).to_dataframe()
            if attempt > 0:
                log.info(f"BQ query succeeded on retry {attempt}")
            return df
        except Exception as e:
            last_err = e
            wait = _RETRY_BACKOFF[min(attempt, len(_RETRY_BACKOFF) - 1)]
            log.warning(f"BQ query failed (attempt {attempt + 1}/{_retries}): {e}")
            if attempt < _retries - 1:
                log.info(f"Retrying in {wait}s...")
                sleep(wait)
    log.error(
        f"BQ query FAILED after {_retries} attempts: {last_err}\n  SQL: {sql[:200]}"
    )
    return pd.DataFrame()


def query_ga4(sql, _retries=_MAX_RETRIES):
    """Run a GA4 BigQuery query. Same as query() — GA4 tables are in the same dataset."""
    return query(sql, _retries=_retries)


# ═══════════════════════════════════════════════════════════════════
#  SIMPLE TTL CACHE
# ═══════════════════════════════════════════════════════════════════

_cache = {}
_CACHE_TTL = 600  # 10 minutes
_FAIL_TTL = 30  # Only cache failures for 30 seconds (retry sooner)


def _cached_query(key, sql_fn):
    """Cache a query result. Empty/failed results are cached for a much shorter TTL."""
    now = time()
    if key in _cache:
        ts, df, was_ok = _cache[key]
        ttl = _CACHE_TTL if was_ok else _FAIL_TTL
        if now - ts < ttl:
            return df.copy()
    try:
        df = sql_fn()
    except Exception as e:
        log.error(f"_cached_query({key}): loader raised {e}")
        df = pd.DataFrame()
    is_ok = not df.empty
    _cache[key] = (now, df, is_ok)
    if not is_ok:
        log.warning(f"_cached_query({key}): empty result — will retry in {_FAIL_TTL}s")
    return df.copy()


def clear_cache():
    """Clear all cached data."""
    global _cache
    _cache = {}


# ═══════════════════════════════════════════════════════════════════
#  DATA LOADERS
# ═══════════════════════════════════════════════════════════════════

# ── Activation ──


def load_activation_score():
    return _cached_query(
        "activation_score",
        lambda: query(
            f"SELECT * FROM {T('d1_activation_score')} ORDER BY activation_score DESC"
        ),
    )


def load_coach_onboarding_funnel():
    return _cached_query(
        "coach_onboarding_funnel",
        lambda: query(f"SELECT * FROM {T('d1_coach_onboarding_funnel')} ORDER BY step"),
    )


def load_coach_retention_curve():
    return _cached_query(
        "coach_retention_curve",
        lambda: query(f"SELECT * FROM {T('d1_coach_retention_curve')}"),
    )


def load_cohort_retention():
    return _cached_query(
        "cohort_retention", lambda: query(f"SELECT * FROM {T('d1_cohort_retention')}")
    )


def load_churn_analysis():
    return _cached_query(
        "churn_analysis", lambda: query(f"SELECT * FROM {T('d1_churn_analysis')}")
    )


# ── Leads & Sales ──


def load_leads_sales():
    return _cached_query(
        "leads_sales",
        lambda: query(f"SELECT * FROM {T('d1_leads_sales')} ORDER BY week_start"),
    )


def load_demo_calls():
    return _cached_query(
        "demo_calls",
        lambda: query(f"SELECT * FROM {T('d1_demo_calls')} ORDER BY week_start"),
    )


def load_meta_ads():
    return _cached_query(
        "meta_ads",
        lambda: query(f"SELECT * FROM {T('d1_meta_ads')} ORDER BY week_start"),
    )


def load_tiktok_ads():
    return _cached_query(
        "tiktok_ads",
        lambda: query(f"SELECT * FROM {T('d1_tiktok_ads')} ORDER BY week_start"),
    )


def load_revenue_split():
    """New sales (hosting fee from new app signups) vs recurring (Stripe app fees).

    New sales = first hosting payment per app from KLIQ_Hosting_Revenue_paid_details.
    Hosting data stops at Sept 2025 — after that we track new app signups
    from applications.created_at as the new-sales count (revenue TBD).
    Recurring = all Stripe subscription app-fee invoices.
    """
    return _cached_query(
        "revenue_split",
        lambda: query(
            f"""
        -- New sales: first hosting payment per app (= new app starts paying KLIQ)
        WITH first_hosting AS (
            SELECT
                application_name,
                MIN(DATE(invoice_paid_transaction_date)) AS first_pay_date,
                MIN(amount_paid) / 100.0 AS first_hosting_fee
            FROM `{DATA_PROJECT}.prod_dataset.KLIQ_Hosting_Revenue_paid_details`
            WHERE amount_paid > 0
            GROUP BY application_name
        ),
        new_hosting_weekly AS (
            SELECT
                DATE_TRUNC(first_pay_date, WEEK(MONDAY)) AS week_start,
                COUNT(*) AS new_hosting_signups,
                ROUND(SUM(first_hosting_fee), 2) AS new_sales_revenue
            FROM first_hosting
            GROUP BY week_start
        ),
        -- After hosting data ends (Sept 2025), count new app signups
        new_apps_weekly AS (
            SELECT
                DATE_TRUNC(DATE(created_at), WEEK(MONDAY)) AS week_start,
                COUNT(*) AS new_app_signups
            FROM `{DATA_PROJECT}.prod_dataset.applications`
            GROUP BY week_start
        ),
        -- Recurring: all Stripe app-fee invoices
        recurring_weekly AS (
            SELECT
                DATE_TRUNC(DATE(paid_at), WEEK(MONDAY)) AS week_start,
                ROUND(SUM(application_fee) / 100.0, 2) AS recurring_revenue,
                COUNT(*) AS renewal_invoices
            FROM `{DATA_PROJECT}.prod_dataset.user_subscription_invoices`
            WHERE status = 'paid'
            GROUP BY week_start
        ),
        -- Combine
        all_weeks AS (
            SELECT DISTINCT week_start FROM new_hosting_weekly
            UNION DISTINCT
            SELECT DISTINCT week_start FROM new_apps_weekly
            UNION DISTINCT
            SELECT DISTINCT week_start FROM recurring_weekly
        )
        SELECT
            w.week_start,
            COALESCE(h.new_hosting_signups, 0) AS new_hosting_signups,
            COALESCE(h.new_sales_revenue, 0) AS new_sales_revenue,
            COALESCE(a.new_app_signups, 0) AS new_app_signups,
            COALESCE(r.recurring_revenue, 0) AS recurring_revenue,
            COALESCE(r.renewal_invoices, 0) AS renewal_invoices
        FROM all_weeks w
        LEFT JOIN new_hosting_weekly h ON w.week_start = h.week_start
        LEFT JOIN new_apps_weekly a ON w.week_start = a.week_start
        LEFT JOIN recurring_weekly r ON w.week_start = r.week_start
        ORDER BY w.week_start
    """
        ),
    )


# ── Coach Deep Dive ──


def load_coach_summary():
    return _cached_query(
        "coach_summary",
        lambda: query(f"SELECT * FROM {T('d1_coach_summary')} ORDER BY total_gmv DESC"),
    )


def load_coach_growth_stages():
    return _cached_query(
        "coach_growth_stages",
        lambda: query(f"SELECT * FROM {T('d1_coach_growth_stages')}"),
    )


def load_coach_gmv_timeline():
    return _cached_query(
        "coach_gmv_timeline",
        lambda: query(f"SELECT * FROM {T('d1_coach_gmv_timeline')} ORDER BY month"),
    )


def load_coach_engagement():
    return _cached_query(
        "coach_engagement", lambda: query(f"SELECT * FROM {T('d1_coach_engagement')}")
    )


def load_app_health_score():
    return _cached_query(
        "app_health_score", lambda: query(f"SELECT * FROM {T('d1_app_health_score')}")
    )


def load_feature_retention_impact():
    return _cached_query(
        "feature_retention_impact",
        lambda: query(f"SELECT * FROM {T('d1_feature_retention_impact')}"),
    )


def load_firstweek_retention():
    return _cached_query(
        "firstweek_retention",
        lambda: query(f"SELECT * FROM {T('d1_firstweek_retention')}"),
    )


# ── Growth Metrics ──


def load_growth_metrics():
    return _cached_query(
        "growth_metrics",
        lambda: query(f"SELECT * FROM {T('d1_growth_metrics')} ORDER BY week_start"),
    )


def load_device_type():
    return _cached_query(
        "device_type",
        lambda: query(f"SELECT * FROM {T('d1_device_type')} ORDER BY date"),
    )


# ── App Health ──


def load_app_lookup():
    return _cached_query(
        "app_lookup", lambda: query(f"SELECT * FROM {T('d2_app_lookup')}")
    )


def load_app_engagement_d2():
    return _cached_query(
        "app_engagement_d2",
        lambda: query(f"SELECT * FROM {T('d2_engagement')} ORDER BY date"),
    )


def load_app_subscriptions():
    return _cached_query(
        "app_subscriptions",
        lambda: query(f"SELECT * FROM {T('d2_subscriptions_revenue')} ORDER BY date"),
    )


def load_app_user_overview():
    return _cached_query(
        "app_user_overview", lambda: query(f"SELECT * FROM {T('d2_user_overview')}")
    )


def load_app_dau():
    return _cached_query(
        "app_dau", lambda: query(f"SELECT * FROM {T('d2_dau')} ORDER BY date")
    )


def load_app_mau():
    return _cached_query(
        "app_mau", lambda: query(f"SELECT * FROM {T('d2_mau')} ORDER BY month")
    )


def load_app_device_breakdown():
    return _cached_query(
        "app_device_breakdown",
        lambda: query(f"SELECT * FROM {T('d1_app_device_breakdown')}"),
    )


def load_app_downloads():
    return _cached_query(
        "app_downloads", lambda: query(f"SELECT * FROM {T('d1_app_downloads')}")
    )


# ── Coach Types ──


def load_coach_types():
    return _cached_query(
        "coach_types",
        lambda: query(
            f"""
        SELECT DATE(event_date) AS event_date,
               JSON_EXTRACT_SCALAR(data, '$.coach_type') AS coach_type
        FROM `{DATA_PROJECT}.prod_dataset.events`
        WHERE event_name = 'coach_type_updated' AND data IS NOT NULL
    """
        ),
    )


# ── Acquisition (GA4) ──


def load_ga4_acquisition():
    return _cached_query(
        "ga4_acquisition",
        lambda: query_ga4(f"SELECT * FROM {T('d1_ga4_acquisition')} ORDER BY date"),
    )


def load_ga4_traffic():
    return _cached_query(
        "ga4_traffic",
        lambda: query_ga4(f"SELECT * FROM {T('d1_ga4_traffic')} ORDER BY date"),
    )


def load_ga4_funnel():
    return _cached_query(
        "ga4_funnel", lambda: query_ga4(f"SELECT * FROM {T('d1_ga4_funnel')}")
    )


# ── Funnels ──


def load_onboarding_funnel():
    return _cached_query(
        "onboarding_funnel",
        lambda: query(
            f"SELECT * FROM {T('d1_onboarding_funnel')} ORDER BY date, step_order"
        ),
    )


def load_engagement_funnel():
    return _cached_query(
        "engagement_funnel",
        lambda: query(
            f"SELECT * FROM {T('d1_engagement_funnel')} ORDER BY date, step_order"
        ),
    )


# ── Revenue ──


def load_unified_revenue():
    return _cached_query(
        "unified_revenue",
        lambda: query(
            f"SELECT * FROM {T('d1_unified_revenue')} ORDER BY month_sort DESC"
        ),
    )


def load_three_source_revenue():
    return _cached_query(
        "three_source_revenue",
        lambda: query(f"SELECT * FROM {T('d1_three_source_revenue')}"),
    )


def load_inapp_purchases():
    return _cached_query(
        "inapp_purchases",
        lambda: query(f"SELECT * FROM {T('d1_inapp_purchases')} ORDER BY month"),
    )


def load_revenue_by_channel():
    return _cached_query(
        "revenue_by_channel",
        lambda: query(f"SELECT * FROM {T('d1_revenue_by_channel')}"),
    )


def load_recurring_payments():
    return _cached_query(
        "recurring_payments",
        lambda: query(f"SELECT * FROM {T('d1_recurring_payments')} ORDER BY month"),
    )


def load_invoice_revenue():
    return _cached_query(
        "invoice_revenue", lambda: query(f"SELECT * FROM {T('d1_invoice_revenue')}")
    )


def load_appfee_revenue():
    return _cached_query(
        "appfee_revenue", lambda: query(f"SELECT * FROM {T('d1_appfee_revenue')}")
    )


def load_kliq_revenue():
    return _cached_query(
        "kliq_revenue", lambda: query(f"SELECT * FROM {T('d1_kliq_revenue')}")
    )


def load_appstore_sales():
    return _cached_query(
        "appstore_sales",
        lambda: query(f"SELECT * FROM {T('d1_appstore_sales')} LIMIT 5000"),
    )


def load_ios_downloads():
    return _cached_query(
        "ios_downloads",
        lambda: query(f"SELECT * FROM {T('d1_ios_downloads')} ORDER BY month"),
    )


# ── Play Store ──


def load_play_store_performance():
    return _cached_query(
        "play_store_performance",
        lambda: query(f"SELECT * FROM {T('d1_play_store_performance')}"),
    )


def load_play_installs():
    return _cached_query(
        "play_installs", lambda: query(f"SELECT * FROM {T('d1_play_installs')}")
    )


# ── Feature Adoption ──


def load_feature_adoption():
    return _cached_query(
        "feature_adoption", lambda: query(f"SELECT * FROM {T('d1_feature_adoption')}")
    )


# Feature labels
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


def load_feature_adoption_platform():
    return _cached_query(
        "feature_adoption_platform",
        lambda: query(
            f"""
        WITH events AS (
            SELECT e.event_name, a.application_name,
                   FORMAT_DATE('%Y-%m', DATE(e.event_date)) AS month, COUNT(*) AS cnt
            FROM `{DATA_PROJECT}.prod_dataset.events` e
            LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
            WHERE a.application_name IS NOT NULL
              AND e.event_name NOT LIKE 'onboarding%' AND e.event_name NOT LIKE 'self_serve%'
            GROUP BY e.event_name, a.application_name, month
        )
        SELECT event_name, SUM(cnt) AS total_events, COUNT(DISTINCT application_name) AS apps_using,
               COUNT(DISTINCT month) AS months_active, MIN(month) AS first_seen, MAX(month) AS last_seen
        FROM events GROUP BY event_name ORDER BY total_events DESC
    """
        ),
    )


def load_feature_adoption_per_app():
    return _cached_query(
        "feature_adoption_per_app",
        lambda: query(
            f"""
        SELECT a.application_name AS app, e.event_name, COUNT(*) AS event_count,
               COUNT(DISTINCT FORMAT_DATE('%Y-%m', DATE(e.event_date))) AS months_used
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        WHERE a.application_name IS NOT NULL
          AND e.event_name NOT LIKE 'onboarding%' AND e.event_name NOT LIKE 'self_serve%'
        GROUP BY app, e.event_name ORDER BY app, event_count DESC
    """
        ),
    )


def load_feature_monthly_trend():
    return _cached_query(
        "feature_monthly_trend",
        lambda: query(
            f"""
        SELECT e.event_name, FORMAT_DATE('%Y-%m', DATE(e.event_date)) AS month,
               COUNT(*) AS event_count, COUNT(DISTINCT a.application_name) AS apps_active
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
            'connects_health_device', 'completed_1_to_1_session')
        GROUP BY e.event_name, month ORDER BY month, event_count DESC
    """
        ),
    )


def load_total_coach_apps():
    df = _cached_query(
        "total_coach_apps",
        lambda: query(
            f"""
        SELECT COUNT(DISTINCT application_name) AS total_apps
        FROM `{DATA_PROJECT}.prod_dataset.applications`
        WHERE application_name IS NOT NULL
    """
        ),
    )
    return int(df.iloc[0]["total_apps"]) if not df.empty else 0


def load_module_adoption():
    return _cached_query(
        "module_adoption",
        lambda: query(
            f"""
        SELECT e.entity_name, a.application_name, COUNT(*) AS event_count,
               COUNT(DISTINCT FORMAT_DATE('%Y-%m', DATE(e.event_date))) AS months_active,
               MIN(DATE(e.event_date)) AS first_used, MAX(DATE(e.event_date)) AS last_used
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        WHERE a.application_name IS NOT NULL AND e.entity_name IS NOT NULL AND e.entity_name != ''
          AND e.entity_name NOT IN ('app_opened','onboarding','self_serve','temp_self_serve',
                                     'self_serve_product','user','customer_behaviour','application','package')
        GROUP BY e.entity_name, a.application_name ORDER BY event_count DESC
    """
        ),
    )


def load_module_monthly_trend():
    return _cached_query(
        "module_monthly_trend",
        lambda: query(
            f"""
        SELECT e.entity_name, FORMAT_DATE('%Y-%m', DATE(e.event_date)) AS month,
               COUNT(*) AS event_count, COUNT(DISTINCT a.application_name) AS apps_active
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        WHERE a.application_name IS NOT NULL AND e.entity_name IS NOT NULL AND e.entity_name != ''
          AND e.entity_name NOT IN ('app_opened','onboarding','self_serve','temp_self_serve',
                                     'self_serve_product','user','customer_behaviour','application','package')
        GROUP BY e.entity_name, month ORDER BY month, event_count DESC
    """
        ),
    )


# ── Growth Strategy (complex queries) ──

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


def load_growth_strategy_app_stats():
    return _cached_query(
        "growth_strategy_app_stats",
        lambda: query(
            f"""
    WITH {_FX_CTE},
    sku_map AS (SELECT DISTINCT product_id, application_name FROM {T('d1_inapp_products')}),
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
        SELECT sku, ROUND(AVG(SAFE_CAST(customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0)), 2) AS avg_price_usd
        FROM {T('d1_appstore_sales')} s LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
        WHERE s.product_type_identifier IN ('IA1', 'IAY') AND SAFE_CAST(customer_price AS FLOAT64) > 0 GROUP BY sku
    ),
    ios_avg AS (
        SELECT ROUND(AVG(SAFE_CAST(customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0)), 2) AS fallback_price
        FROM {T('d1_appstore_sales')} s LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
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
        WHERE e.event_name = 'purchase_success' AND a.application_name IS NOT NULL GROUP BY app
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
            COUNTIF(e.event_name IN ('post_on_community','post_on_community_feed_with_photo','post_on_community_feed_with_voice_notes')) AS community_posts,
            COUNTIF(e.event_name = 'app_opened') AS app_opens,
            COUNTIF(e.event_name = 'publish_module') AS modules_published,
            COUNTIF(e.event_name = 'publishes_program') AS programs_published,
            COUNT(DISTINCT FORMAT_DATE('%Y-%m', DATE(e.event_date))) AS event_months
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        WHERE a.application_name IS NOT NULL GROUP BY app
    ),
    apps_meta AS (
        SELECT application_name AS app, DATE(created_at) AS created_date
        FROM `{DATA_PROJECT}.prod_dataset.applications` WHERE application_name IS NOT NULL
    ),
    fees AS (
        SELECT application_name AS app, kliq_fee_pct FROM {T('d1_app_fee_lookup')} WHERE kliq_fee_pct IS NOT NULL
    )
    SELECT COALESCE(ae.app, ar.app, gr.app) AS app, am.created_date,
        COALESCE(ar.apple_sales, 0) + COALESCE(gr.google_sales, 0) AS iap_revenue,
        COALESCE(ar.apple_sales, 0) AS apple_sales, COALESCE(gr.google_sales, 0) AS google_sales,
        GREATEST(COALESCE(ar.apple_months, 0), COALESCE(gr.google_months, 0)) AS active_rev_months,
        COALESCE(ae.purchases, 0) AS purchases, COALESCE(ae.recurring_payments, 0) AS recurring_payments,
        COALESCE(ae.new_subscribers, 0) AS new_subscribers, COALESCE(ae.cancellations, 0) AS cancellations,
        COALESCE(ae.livestreams, 0) AS livestreams, COALESCE(ae.live_joins, 0) AS live_joins,
        COALESCE(ae.workouts, 0) AS workouts, COALESCE(ae.community_posts, 0) AS community_posts,
        COALESCE(ae.app_opens, 0) AS app_opens, COALESCE(ae.modules_published, 0) AS modules_published,
        COALESCE(ae.programs_published, 0) AS programs_published,
        COALESCE(ae.event_months, 0) AS event_months, COALESCE(f.kliq_fee_pct, 0) AS kliq_fee_pct
    FROM app_events ae
    FULL OUTER JOIN apple_rev ar ON ae.app = ar.app
    FULL OUTER JOIN google_rev gr ON COALESCE(ae.app, ar.app) = gr.app
    LEFT JOIN apps_meta am ON COALESCE(ae.app, ar.app, gr.app) = am.app
    LEFT JOIN fees f ON COALESCE(ae.app, ar.app, gr.app) = f.app
    WHERE COALESCE(ae.app_opens, 0) > 0 ORDER BY iap_revenue DESC
    """
        ),
    )


def load_growth_strategy_monthly():
    return _cached_query(
        "growth_strategy_monthly",
        lambda: query(
            f"""
    WITH {_FX_CTE},
    sku_map AS (SELECT DISTINCT product_id, application_name FROM {T('d1_inapp_products')}),
    apple_monthly AS (
        SELECT COALESCE(m.application_name, 'Unknown') AS app,
               FORMAT_DATE('%Y-%m', s.report_date) AS month,
               ROUND(SUM(SAFE_CAST(s.customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0) * SAFE_CAST(s.units AS INT64)), 2) AS sales
        FROM {T('d1_appstore_sales')} s
        LEFT JOIN sku_map m ON s.sku = m.product_id LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
        WHERE s.product_type_identifier IN ('IA1', 'IAY') AND SAFE_CAST(s.customer_price AS FLOAT64) > 0
        GROUP BY app, month
    ),
    apple_sku_prices AS (
        SELECT sku, ROUND(AVG(SAFE_CAST(customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0)), 2) AS avg_price_usd
        FROM {T('d1_appstore_sales')} s LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
        WHERE s.product_type_identifier IN ('IA1', 'IAY') AND SAFE_CAST(customer_price AS FLOAT64) > 0 GROUP BY sku
    ),
    ios_avg AS (
        SELECT ROUND(AVG(SAFE_CAST(customer_price AS FLOAT64) * COALESCE(fx.rate, 1.0)), 2) AS fallback_price
        FROM {T('d1_appstore_sales')} s LEFT JOIN fx_rates fx ON s.customer_currency = fx.currency
        WHERE s.product_type_identifier IN ('IA1', 'IAY') AND SAFE_CAST(customer_price AS FLOAT64) > 0
    ),
    google_monthly AS (
        SELECT a.application_name AS app, FORMAT_DATE('%Y-%m', DATE(e.event_date)) AS month,
               ROUND(SUM(COALESCE(ap.avg_price_usd, iavg.fallback_price)), 2) AS sales
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        LEFT JOIN apple_sku_prices ap ON JSON_VALUE(e.data, '$.in_app_product_id') = ap.sku
        CROSS JOIN ios_avg iavg
        WHERE e.event_name = 'purchase_success' AND a.application_name IS NOT NULL GROUP BY app, month
    ),
    combined_rev AS (
        SELECT app, month, SUM(sales) AS total_sales FROM (
            SELECT * FROM apple_monthly UNION ALL SELECT * FROM google_monthly
        ) GROUP BY app, month
    ),
    monthly_events AS (
        SELECT a.application_name AS app, FORMAT_DATE('%Y-%m', DATE(e.event_date)) AS month,
            COUNTIF(e.event_name = 'user_subscribed') AS new_subs,
            COUNTIF(e.event_name = 'cancels_subscription') AS cancels,
            COUNTIF(e.event_name = 'purchase_success') AS purchases,
            COUNTIF(e.event_name = 'recurring_payment') AS recurring,
            COUNTIF(e.event_name = 'live_session_created') AS livestreams,
            COUNTIF(e.event_name = 'app_opened') AS app_opens
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        WHERE a.application_name IS NOT NULL GROUP BY app, month
    )
    SELECT COALESCE(r.app, e.app) AS app, COALESCE(r.month, e.month) AS month,
        COALESCE(r.total_sales, 0) AS total_sales, COALESCE(e.new_subs, 0) AS new_subs,
        COALESCE(e.cancels, 0) AS cancels, COALESCE(e.purchases, 0) AS purchases,
        COALESCE(e.recurring, 0) AS recurring, COALESCE(e.livestreams, 0) AS livestreams,
        COALESCE(e.app_opens, 0) AS app_opens
    FROM combined_rev r FULL OUTER JOIN monthly_events e ON r.app = e.app AND r.month = e.month
    WHERE COALESCE(r.total_sales, 0) > 0 OR COALESCE(e.app_opens, 0) > 0
    ORDER BY app, month
    """
        ),
    )


def load_feature_frequency():
    return _cached_query(
        "feature_frequency",
        lambda: query(
            f"""
    WITH event_dates AS (
        SELECT a.application_name AS app, e.event_name, DATE(e.event_date) AS event_date
        FROM `{DATA_PROJECT}.prod_dataset.events` e
        LEFT JOIN `{DATA_PROJECT}.prod_dataset.applications` a ON e.application_id = a.id
        WHERE a.application_name IS NOT NULL
          AND e.event_name NOT LIKE 'onboarding%' AND e.event_name NOT LIKE 'self_serve%'
        GROUP BY app, e.event_name, event_date
    ),
    date_gaps AS (
        SELECT app, event_name, event_date,
            DATE_DIFF(event_date, LAG(event_date) OVER (PARTITION BY app, event_name ORDER BY event_date), DAY) AS days_gap
        FROM event_dates
    )
    SELECT event_name, ROUND(AVG(days_gap), 1) AS avg_days_between,
           COUNT(DISTINCT app) AS apps_with_repeat, ROUND(AVG(days_gap) / 7.0, 1) AS avg_weeks_between
    FROM date_gaps WHERE days_gap IS NOT NULL AND days_gap > 0
    GROUP BY event_name ORDER BY avg_days_between ASC
    """
        ),
    )
