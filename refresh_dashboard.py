"""
KLIQ Dashboard Refresh Script
Reads from rcwl-data.prod_dataset, transforms with Pandas,
writes pre-aggregated tables to a target BigQuery dataset for Power BI.

Usage:
    python refresh_dashboard.py

Requires:
    - Google Cloud BigQuery credentials (service account JSON)
    - pip install google-cloud-bigquery pandas db-dtypes
"""

import os
import io
import gzip
import time
from datetime import date, timedelta
import jwt
import requests
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build as google_build

# ── Configuration ──
SERVICE_ACCOUNT_KEY = os.environ.get(
    "GCP_SERVICE_ACCOUNT_KEY", "rcwl-development-0c013e9b5c2b.json"
)
SOURCE_PROJECT = "rcwl-data"
SOURCE_DATASET = "prod_dataset"
TARGET_PROJECT = "rcwl-data"
TARGET_DATASET = "powerbi_dashboard"
LOCATION = "EU"
GA4_DATASET = "analytics_436239662"
GA4_LOCATION = "US"

# ── Excluded Apps (test/bot/internal) ──
EXCLUDED_APPS = [
    "Jupiter",
    "Remote Coach - Default App",
    "Remote Coach Creators",
    "Dogpound",
    "LDN Fit",
    "Teach2Sweat",
]
EXCLUDED_APPS_SQL = ", ".join(f"'{a}'" for a in EXCLUDED_APPS)

# ── Apple App Store Connect ──
APPLE_ISSUER_ID = os.environ.get(
    "APPLE_ISSUER_ID", "69a6de86-a200-47e3-e053-5b8c7c11a4d1"
)
APPLE_KEY_ID = os.environ.get("APPLE_KEY_ID", "A985D2XN2K")
APPLE_KEY_FILE = os.environ.get("APPLE_KEY_FILE", "AuthKey_A985D2XN2K.p8")
APPLE_VENDOR = os.environ.get("APPLE_VENDOR", "88386165")

# ── Meta (Facebook) Ads ──
META_AD_ACCOUNT_ID = os.environ.get("META_AD_ACCOUNT_ID", "act_472085159972709")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")

# ── TikTok Ads ──
TIKTOK_ADVERTISER_ID = os.environ.get("TIKTOK_ADVERTISER_ID", "7223793908814233602")
TIKTOK_ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN", "")

# ── Google Calendar ──
CALENDAR_ID = os.environ.get("CALENDAR_ID", "ben@joinkliq.io")
DEMO_SEARCH_TERM = os.environ.get("DEMO_SEARCH_TERM", "KLIQ GLOBAL PARTNERSHIP DEMO")

# ── Setup clients ──
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY)
read_client = bigquery.Client(
    credentials=credentials, project=SOURCE_PROJECT, location=LOCATION
)
write_client = bigquery.Client(
    credentials=credentials, project=TARGET_PROJECT, location=LOCATION
)
ga4_client = bigquery.Client(
    credentials=credentials, project=SOURCE_PROJECT, location=GA4_LOCATION
)


def read_query(sql: str) -> pd.DataFrame:
    """Execute a read query against prod."""
    return read_client.query(sql).to_dataframe()


def read_ga4_query(sql: str) -> pd.DataFrame:
    """Execute a read query against GA4 (US region)."""
    return ga4_client.query(sql).to_dataframe()


def write_table(df: pd.DataFrame, table_name: str):
    """Write a DataFrame to the target dataset, replacing existing data."""
    table_id = f"{TARGET_PROJECT}.{TARGET_DATASET}.{table_name}"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = write_client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"  ✅ {table_name} — {len(df)} rows")


def ensure_dataset():
    """Create the target dataset if it doesn't exist."""
    dataset_ref = bigquery.Dataset(f"{TARGET_PROJECT}.{TARGET_DATASET}")
    dataset_ref.location = LOCATION
    try:
        write_client.create_dataset(dataset_ref, exists_ok=True)
        print(f"📦 Dataset {TARGET_PROJECT}.{TARGET_DATASET} ready\n")
    except Exception as e:
        print(f"⚠️  Could not create dataset (may already exist): {e}")
        print(f"   Attempting to write tables anyway...\n")


# ═══════════════════════════════════════════════════════════════
# DASHBOARD 1 — Main Growth
# ═══════════════════════════════════════════════════════════════


def refresh_d1_growth_metrics():
    """Sign-ups, card details, upgrades, subscriptions, cancellations by date."""
    df = read_query(
        f"""
        SELECT DATE(event_date) as date, 'signups' as metric, COUNT(*) as value
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name = 'self_serve_completed_create_account'
        GROUP BY date
        UNION ALL
        SELECT DATE(event_date), 'card_details_added', COUNT(*)
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name = 'self_serve_completed_add_payment_info'
        GROUP BY 1
        UNION ALL
        SELECT DATE(event_date), 'upgrade_started', COUNT(*)
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name = 'upgrade_started'
        GROUP BY 1
        UNION ALL
        SELECT DATE(event_date), 'upgrade_completed', COUNT(*)
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name = 'self_serve_completed_conversion'
        GROUP BY 1
        UNION ALL
        SELECT DATE(event_date), 'new_subscriptions', COUNT(*)
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name = 'user_subscribed'
        GROUP BY 1
        UNION ALL
        SELECT DATE(event_date), 'cancellations', COUNT(*)
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name = 'cancels_subscription'
        GROUP BY 1
    """
    )
    write_table(df, "d1_growth_metrics")


def refresh_d1_onboarding_funnel():
    """Onboarding funnel steps by date with clean names and sort order."""
    df = read_query(
        f"""
        SELECT 
            DATE(event_date) as date,
            CASE event_name
                WHEN 'self_serve_start' THEN '1. Started Sign-up'
                WHEN 'self_serve_completed_create_account' THEN '2. Created Account'
                WHEN 'self_serve_completed_create_password' THEN '3. Created Password'
                WHEN 'self_serve_completed_add_payment_info' THEN '4. Added Payment'
                WHEN 'self_serve_completed_conversion' THEN '5. Completed Conversion'
            END as funnel_step,
            CASE event_name
                WHEN 'self_serve_start' THEN 1
                WHEN 'self_serve_completed_create_account' THEN 2
                WHEN 'self_serve_completed_create_password' THEN 3
                WHEN 'self_serve_completed_add_payment_info' THEN 4
                WHEN 'self_serve_completed_conversion' THEN 5
            END as step_order,
            COUNT(*) as value
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name IN (
            'self_serve_start',
            'self_serve_completed_create_account',
            'self_serve_completed_create_password',
            'self_serve_completed_conversion',
            'self_serve_completed_add_payment_info'
        )
        GROUP BY date, funnel_step, step_order
    """
    )
    write_table(df, "d1_onboarding_funnel")


def refresh_d1_engagement_funnel():
    """Coach engagement funnel: profile uploaded, first livestream created, previewed app, copied URL."""
    df = read_query(
        f"""
        WITH first_livestream AS (
            SELECT user_id, MIN(event_date) as event_date
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
            WHERE event_name = 'live_session_created'
            GROUP BY user_id
        ),
        other_events AS (
            SELECT event_date, event_name
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
            WHERE event_name IN (
                'profile_image_added',
                'profile_image_added_your_store',
                'preview_clicked',
                'copy_url_clicked'
            )
        ),
        combined AS (
            SELECT event_date, event_name FROM other_events
            UNION ALL
            SELECT event_date, 'live_session_created' as event_name FROM first_livestream
        )
        SELECT 
            DATE(event_date) as date,
            CASE event_name
                WHEN 'profile_image_added' THEN '1. Uploaded Profile'
                WHEN 'profile_image_added_your_store' THEN '1. Uploaded Profile'
                WHEN 'live_session_created' THEN '2. Created Livestream'
                WHEN 'preview_clicked' THEN '3. Previewed App'
                WHEN 'copy_url_clicked' THEN '4. Copied URL'
            END as funnel_step,
            CASE event_name
                WHEN 'profile_image_added' THEN 1
                WHEN 'profile_image_added_your_store' THEN 1
                WHEN 'live_session_created' THEN 2
                WHEN 'preview_clicked' THEN 3
                WHEN 'copy_url_clicked' THEN 4
            END as step_order,
            COUNT(*) as value
        FROM combined
        GROUP BY date, funnel_step, step_order
    """
    )
    write_table(df, "d1_engagement_funnel")


def refresh_d1_activation_score():
    """Per-app activation score based on coach setup actions in first 30 days.

    Weights are derived from retention-lift analysis:
    each action's weight reflects how much more likely an app is to remain active
    if the coach performed that action within 30 days of app creation.
    Max score = 100.
    """
    df = read_query(
        f"""
        WITH app_created AS (
            SELECT id as application_id, application_name, DATE(created_at) as created_date
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications`
        ),
        coach_actions AS (
            SELECT
                e.application_id,
                e.event_name,
                DATE_DIFF(DATE(e.event_date), a.created_date, DAY) as days_since_creation
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events` e
            JOIN app_created a ON e.application_id = a.application_id
            WHERE e.event_name IN (
                'profile_image_added', 'profile_image_added_your_store',
                'create_module', 'publish_module',
                'live_session_created',
                'creates_program', 'publishes_program',
                'preview_clicked', 'copy_url_clicked', 'clicks_publish_app',
                'engage_with_blog_post', 'visits_blog',
                'engages_with_recipe', 'visits_nutrition_page',
                'post_on_community', 'post_on_community_feed_with_photo',
                '1_to_1_session_schedule',
                'onboarding_module_completed'
            )
        ),
        still_active AS (
            SELECT DISTINCT application_id
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
            WHERE event_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
            AND event_name = 'app_opened'
        ),
        has_revenue AS (
            SELECT application_id, SUM(amount_paid) as total_revenue
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.user_subscription_invoices`
            WHERE status = 'paid'
            GROUP BY application_id
        ),
        latest_activity AS (
            SELECT application_id, MAX(DATE(event_date)) as last_active_date
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
            WHERE event_name = 'app_opened'
            GROUP BY application_id
        ),
        coach_email AS (
            SELECT application_id, email
            FROM (
                SELECT application_id, email,
                    ROW_NUMBER() OVER (PARTITION BY application_id ORDER BY created_at DESC) as rn
                FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.users`
                WHERE user_type = 4
                AND email IS NOT NULL AND email != ''
            )
            WHERE rn = 1
        ),
        activation AS (
            SELECT
                a.application_id,
                a.application_name,
                a.created_date,
                DATE_DIFF(CURRENT_DATE(), a.created_date, DAY) as app_age_days,
                ce.email as coach_email,
                -- Individual action flags (first 30 days)
                MAX(CASE WHEN ca.event_name IN ('profile_image_added','profile_image_added_your_store') AND ca.days_since_creation <= 30 THEN 1 ELSE 0 END) as added_profile_image,
                MAX(CASE WHEN ca.event_name IN ('create_module','publish_module') AND ca.days_since_creation <= 30 THEN 1 ELSE 0 END) as created_module,
                MAX(CASE WHEN ca.event_name = 'live_session_created' AND ca.days_since_creation <= 30 THEN 1 ELSE 0 END) as created_livestream,
                MAX(CASE WHEN ca.event_name IN ('creates_program','publishes_program') AND ca.days_since_creation <= 30 THEN 1 ELSE 0 END) as created_program,
                MAX(CASE WHEN ca.event_name = 'preview_clicked' AND ca.days_since_creation <= 30 THEN 1 ELSE 0 END) as previewed_app,
                MAX(CASE WHEN ca.event_name = 'clicks_publish_app' AND ca.days_since_creation <= 30 THEN 1 ELSE 0 END) as published_app,
                MAX(CASE WHEN ca.event_name IN ('engage_with_blog_post','visits_blog') AND ca.days_since_creation <= 30 THEN 1 ELSE 0 END) as added_blog_content,
                MAX(CASE WHEN ca.event_name IN ('engages_with_recipe','visits_nutrition_page') AND ca.days_since_creation <= 30 THEN 1 ELSE 0 END) as added_nutrition,
                MAX(CASE WHEN ca.event_name IN ('post_on_community','post_on_community_feed_with_photo') AND ca.days_since_creation <= 30 THEN 1 ELSE 0 END) as posted_community,
                MAX(CASE WHEN ca.event_name = 'copy_url_clicked' AND ca.days_since_creation <= 30 THEN 1 ELSE 0 END) as copied_url,
                MAX(CASE WHEN ca.event_name = '1_to_1_session_schedule' AND ca.days_since_creation <= 30 THEN 1 ELSE 0 END) as created_1to1,
                -- Outcome
                CASE WHEN sa.application_id IS NOT NULL THEN 1 ELSE 0 END as is_active,
                ROUND(COALESCE(hr.total_revenue, 0) / 100.0, 2) as total_revenue_usd,
                la.last_active_date
            FROM app_created a
            LEFT JOIN coach_actions ca ON a.application_id = ca.application_id
            LEFT JOIN still_active sa ON a.application_id = sa.application_id
            LEFT JOIN has_revenue hr ON a.application_id = hr.application_id
            LEFT JOIN latest_activity la ON a.application_id = la.application_id
            LEFT JOIN coach_email ce ON a.application_id = ce.application_id
            GROUP BY a.application_id, a.application_name, a.created_date,
                     sa.application_id, hr.total_revenue, la.last_active_date, ce.email
        )
        SELECT
            *,
            -- Weighted activation score (max 100)
            (added_profile_image * 10
             + created_module * 10
             + created_livestream * 10
             + created_program * 10
             + previewed_app * 15
             + published_app * 10
             + added_blog_content * 10
             + added_nutrition * 10
             + posted_community * 5
             + copied_url * 5
             + created_1to1 * 5) as activation_score,
            -- Count of actions completed
            (added_profile_image + created_module + created_livestream + created_program
             + previewed_app + published_app + added_blog_content + added_nutrition
             + posted_community + copied_url + created_1to1) as actions_completed,
            -- Risk label
            CASE
                WHEN (added_profile_image + created_module + created_livestream + created_program
                      + previewed_app + published_app + added_blog_content + added_nutrition
                      + posted_community + copied_url + created_1to1) >= 7 THEN 'Low Risk'
                WHEN (added_profile_image + created_module + created_livestream + created_program
                      + previewed_app + published_app + added_blog_content + added_nutrition
                      + posted_community + copied_url + created_1to1) >= 4 THEN 'Medium Risk'
                WHEN (added_profile_image + created_module + created_livestream + created_program
                      + previewed_app + published_app + added_blog_content + added_nutrition
                      + posted_community + copied_url + created_1to1) >= 1 THEN 'High Risk'
                ELSE 'Critical'
            END as risk_level
        FROM activation
        ORDER BY activation_score DESC, created_date DESC
    """
    )
    write_table(df, "d1_activation_score")


def refresh_d1_leads_sales():
    """Weekly leads & sales metrics matching the manual tracking spreadsheet.

    Produces one row per week with columns for:
    - applications_created, card_details, card_conversion_pct
    - new_trialers, self_serve_conversion_pct
    - new_customers (paid first invoice), new_failed_signups
    - sales_revenue_usd
    - churn_trial, churn_active
    - total_paying_customers (running)
    - subscribers, free_accounts, active_users
    """
    # Weekly metrics from prod_dataset.events
    events_df = read_query(
        f"""
        WITH weeks AS (
            SELECT
                DATE_TRUNC(DATE(event_date), WEEK(MONDAY)) as week_start,
                event_name,
                COUNT(*) as cnt,
                COUNT(DISTINCT user_id) as unique_users
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
            WHERE event_name IN (
                'self_serve_start',
                'self_serve_completed_create_account',
                'self_serve_completed_add_payment_info',
                'self_serve_completed_conversion',
                'cancels_subscription'
            )
            GROUP BY week_start, event_name
        )
        SELECT
            week_start,
            SUM(CASE WHEN event_name = 'self_serve_start' THEN cnt ELSE 0 END) as signups_started,
            SUM(CASE WHEN event_name = 'self_serve_completed_create_account' THEN cnt ELSE 0 END) as applications_created,
            SUM(CASE WHEN event_name = 'self_serve_completed_add_payment_info' THEN cnt ELSE 0 END) as card_details,
            SUM(CASE WHEN event_name = 'self_serve_completed_conversion' THEN cnt ELSE 0 END) as new_trialers,
            SUM(CASE WHEN event_name = 'cancels_subscription' THEN cnt ELSE 0 END) as cancellations
        FROM weeks
        GROUP BY week_start
        ORDER BY week_start
    """
    )

    # Weekly new paying customers and sales revenue from invoices
    invoice_df = read_query(
        f"""
        WITH weekly_invoices AS (
            SELECT
                DATE_TRUNC(DATE(paid_at), WEEK(MONDAY)) as week_start,
                application_id,
                SUM(amount_paid) as amount_cents,
                SUM(application_fee) as fee_cents,
                COUNT(*) as invoice_count
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.user_subscription_invoices`
            WHERE status = 'paid'
            GROUP BY week_start, application_id
        ),
        -- First invoice per application (new customer)
        first_invoice AS (
            SELECT application_id, MIN(DATE(paid_at)) as first_paid_date
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.user_subscription_invoices`
            WHERE status = 'paid'
            GROUP BY application_id
        ),
        new_customers AS (
            SELECT
                DATE_TRUNC(first_paid_date, WEEK(MONDAY)) as week_start,
                COUNT(*) as new_customers
            FROM first_invoice
            GROUP BY week_start
        )
        SELECT
            w.week_start,
            ROUND(SUM(w.fee_cents) / 100.0, 2) as sales_revenue_usd,
            SUM(w.invoice_count) as total_invoices,
            COALESCE(nc.new_customers, 0) as new_customers
        FROM weekly_invoices w
        LEFT JOIN new_customers nc ON w.week_start = nc.week_start
        GROUP BY w.week_start, nc.new_customers
        ORDER BY w.week_start
    """
    )

    # Active paying coaches per week (apps paying KLIQ: hosting + app fees, trailing 30 days)
    paying_df = read_query(
        f"""
        WITH kliq_payments AS (
            -- Hosting fees (coach pays KLIQ) — data up to Sept 2025
            SELECT
                DATE(invoice_paid_transaction_date) as payment_date,
                application_name as app_key
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.KLIQ_Hosting_Revenue_paid_details`
            WHERE amount_paid > 0

            UNION ALL

            -- App fees from Stripe invoices (live data)
            SELECT
                DATE(paid_at) as payment_date,
                a.application_name as app_key
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.user_subscription_invoices` i
            JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications` a
                ON i.application_id = a.id
            WHERE i.status = 'paid'
            AND i.application_fee > 0
        ),
        weeks AS (
            SELECT DISTINCT DATE_TRUNC(payment_date, WEEK(MONDAY)) as week_start
            FROM kliq_payments
        ),
        paying_per_week AS (
            SELECT
                w.week_start,
                COUNT(DISTINCT p.app_key) as total_paying_customers
            FROM weeks w
            LEFT JOIN kliq_payments p
                ON p.payment_date BETWEEN DATE_SUB(w.week_start, INTERVAL 30 DAY) AND DATE_ADD(w.week_start, INTERVAL 6 DAY)
            GROUP BY w.week_start
        )
        SELECT week_start, total_paying_customers
        FROM paying_per_week
        ORDER BY week_start
    """
    )

    # Total subscribers, free accounts, active users per week
    users_df = read_query(
        f"""
        WITH weekly_users AS (
            SELECT
                DATE_TRUNC(DATE(event_date), WEEK(MONDAY)) as week_start,
                COUNT(DISTINCT user_id) as active_users
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
            WHERE event_name = 'app_opened'
            GROUP BY week_start
        )
        SELECT * FROM weekly_users ORDER BY week_start
    """
    )

    # Cumulative registered users per week
    registered_df = read_query(
        f"""
        SELECT
            DATE_TRUNC(DATE(created_at), WEEK(MONDAY)) as week_start,
            COUNT(*) as new_registrations
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.users`
        GROUP BY week_start
        ORDER BY week_start
    """
    )

    # Merge everything
    import functools

    all_weeks = set()
    for d in [events_df, invoice_df, paying_df, users_df, registered_df]:
        if not d.empty and "week_start" in d.columns:
            all_weeks.update(d["week_start"].dropna().tolist())

    if not all_weeks:
        write_table(pd.DataFrame(), "d1_leads_sales")
        return

    base = pd.DataFrame({"week_start": sorted(all_weeks)})
    base["week_start"] = pd.to_datetime(base["week_start"])

    for d in [events_df, invoice_df, paying_df, users_df, registered_df]:
        if not d.empty:
            d["week_start"] = pd.to_datetime(d["week_start"])

    result = base.copy()
    for d in [events_df, invoice_df, paying_df, users_df, registered_df]:
        if not d.empty:
            result = result.merge(d, on="week_start", how="left")

    result = result.fillna(0)

    # Compute derived metrics
    result["card_conversion_pct"] = (
        (
            result["card_details"]
            / result["applications_created"].replace(0, float("nan"))
            * 100
        )
        .round(1)
        .fillna(0)
    )

    result["self_serve_conversion_pct"] = (
        (result["new_trialers"] / result["card_details"].replace(0, float("nan")) * 100)
        .round(1)
        .fillna(0)
    )

    # total_paying_customers already comes from paying_df (distinct apps with paid invoice in trailing 30 days)

    # Cumulative free accounts
    if "new_registrations" in result.columns:
        result["free_accounts"] = result["new_registrations"].cumsum()

    # Week number (sequential)
    result = result.sort_values("week_start").reset_index(drop=True)
    result["week_number"] = range(1, len(result) + 1)

    # Select and order columns
    final_cols = [
        "week_start",
        "week_number",
        "applications_created",
        "card_details",
        "card_conversion_pct",
        "new_trialers",
        "self_serve_conversion_pct",
        "new_customers",
        "sales_revenue_usd",
        "cancellations",
        "total_paying_customers",
        "active_users",
        "new_registrations",
        "free_accounts",
    ]
    available = [c for c in final_cols if c in result.columns]
    result = result[available]

    write_table(result, "d1_leads_sales")


def refresh_d1_demo_calls():
    """Pull weekly demo call counts from Google Calendar.

    Searches for events matching DEMO_SEARCH_TERM and aggregates by week.
    Requires the calendar to be shared with the service account.
    """
    from datetime import datetime, timezone

    scoped_creds = credentials.with_scopes(
        ["https://www.googleapis.com/auth/calendar.readonly"]
    )
    cal_service = google_build("calendar", "v3", credentials=scoped_creds)

    # Pull up to 2 years of history
    time_min = datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat()
    time_max = datetime.now(timezone.utc).isoformat()

    all_events = []
    page_token = None
    while True:
        result = (
            cal_service.events()
            .list(
                calendarId=CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                q=DEMO_SEARCH_TERM,
                singleEvents=True,
                orderBy="startTime",
                maxResults=2500,
                pageToken=page_token,
            )
            .execute()
        )
        all_events.extend(result.get("items", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    if not all_events:
        print("  ⚠️  No demo call events found in calendar")
        write_table(pd.DataFrame(columns=["week_start", "demo_calls"]), "d1_demo_calls")
        return

    # Parse event dates
    rows = []
    for ev in all_events:
        start = ev.get("start", {})
        dt_str = start.get("dateTime") or start.get("date")
        if dt_str:
            dt = pd.to_datetime(dt_str, utc=True)
            rows.append({"event_date": dt.date(), "summary": ev.get("summary", "")})

    df = pd.DataFrame(rows)
    df["event_date"] = pd.to_datetime(df["event_date"])
    df["week_start"] = df["event_date"] - pd.to_timedelta(
        df["event_date"].dt.weekday, unit="D"
    )

    weekly = df.groupby("week_start").size().reset_index(name="demo_calls")
    weekly = weekly.sort_values("week_start").reset_index(drop=True)

    write_table(weekly, "d1_demo_calls")


def refresh_d1_meta_ads():
    """Pull weekly ad spend, impressions, clicks, and leads from Meta Marketing API.

    Requires META_ACCESS_TOKEN to be set.
    """
    if not META_ACCESS_TOKEN:
        print("  ⏭️  Meta Ads skipped — no access token configured")
        return

    base_url = f"https://graph.facebook.com/v19.0/{META_AD_ACCOUNT_ID}/insights"
    all_rows = []

    # Paginate through weekly data (campaign level to capture lead form actions)
    params = {
        "access_token": META_ACCESS_TOKEN,
        "time_increment": 7,  # weekly
        "date_preset": "maximum",
        "fields": "spend,impressions,clicks,actions",
        "level": "campaign",
        "limit": 500,
    }

    url = base_url
    while url:
        resp = requests.get(url, params=params if url == base_url else None)
        data = resp.json()

        if "error" in data:
            print(
                f"  ❌ Meta Ads API error: {data['error'].get('message', data['error'])}"
            )
            return

        for row in data.get("data", []):
            actions_map = {}
            for action in row.get("actions", []):
                actions_map[action.get("action_type")] = int(action.get("value", 0))
            all_rows.append(
                {
                    "date_start": row["date_start"],
                    "date_stop": row["date_stop"],
                    "meta_spend": float(row.get("spend", 0)),
                    "meta_impressions": int(row.get("impressions", 0)),
                    "meta_clicks": int(row.get("clicks", 0)),
                    "meta_link_clicks": actions_map.get("link_click", 0),
                    "meta_landing_page_views": actions_map.get("landing_page_view", 0),
                    "meta_leads": actions_map.get("lead", 0)
                    + actions_map.get("onsite_conversion.lead_grouped", 0),
                    "meta_video_views": actions_map.get("video_view", 0),
                    "meta_post_reactions": actions_map.get("post_reaction", 0),
                }
            )

        # Handle pagination
        paging = data.get("paging", {})
        url = paging.get("next")
        params = None  # next URL includes params

    if not all_rows:
        print("  ⚠️  No Meta Ads data returned")
        write_table(pd.DataFrame(), "d1_meta_ads")
        return

    df = pd.DataFrame(all_rows)
    df["week_start"] = pd.to_datetime(df["date_start"])
    df = df.drop(columns=["date_start", "date_stop"])

    # Aggregate by week (in case of overlapping windows)
    weekly = (
        df.groupby("week_start")
        .agg(
            {
                "meta_spend": "sum",
                "meta_impressions": "sum",
                "meta_clicks": "sum",
                "meta_link_clicks": "sum",
                "meta_landing_page_views": "sum",
                "meta_leads": "sum",
                "meta_video_views": "sum",
                "meta_post_reactions": "sum",
            }
        )
        .reset_index()
    )

    weekly = weekly.sort_values("week_start").reset_index(drop=True)
    write_table(weekly, "d1_meta_ads")


def refresh_d1_tiktok_ads():
    """Pull weekly ad spend, impressions, clicks, and conversions from TikTok Ads API.

    Uses the TikTok Reporting API v1.3 integrated report endpoint.
    Requires TIKTOK_ACCESS_TOKEN to be set.
    """
    if not TIKTOK_ACCESS_TOKEN:
        print("  ⏭️  TikTok Ads skipped — no access token configured")
        return

    base_url = "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/"
    headers = {"Access-Token": TIKTOK_ACCESS_TOKEN}

    # Pull data from 2024-01-01 to today
    from datetime import datetime, timedelta

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = "2024-01-01"

    all_rows = []
    page = 1
    page_size = 1000

    while True:
        params = {
            "advertiser_id": TIKTOK_ADVERTISER_ID,
            "report_type": "BASIC",
            "dimensions": '["stat_time_day"]',
            "metrics": '["spend", "impressions", "clicks", "conversion", "cpc", "cpm", "ctr", "cost_per_conversion", "reach", "video_views_p25", "video_views_p50", "video_views_p75", "video_views_p100"]',
            "data_level": "AUCTION_ADVERTISER",
            "start_date": start_date,
            "end_date": end_date,
            "page": page,
            "page_size": page_size,
        }

        resp = requests.get(base_url, headers=headers, params=params)
        data = resp.json()

        if data.get("code") != 0:
            print(f"  ❌ TikTok Ads API error: {data.get('message', data)}")
            return

        rows = data.get("data", {}).get("list", [])
        if not rows:
            break

        for row in rows:
            dims = row.get("dimensions", {})
            metrics = row.get("metrics", {})
            all_rows.append(
                {
                    "date": dims.get("stat_time_day"),
                    "tt_spend": float(metrics.get("spend", 0)),
                    "tt_impressions": int(float(metrics.get("impressions", 0))),
                    "tt_clicks": int(float(metrics.get("clicks", 0))),
                    "tt_conversions": int(float(metrics.get("conversion", 0))),
                    "tt_cpc": float(metrics.get("cpc", 0)),
                    "tt_cpm": float(metrics.get("cpm", 0)),
                    "tt_ctr": float(metrics.get("ctr", 0)),
                    "tt_cost_per_conversion": float(
                        metrics.get("cost_per_conversion", 0)
                    ),
                    "tt_reach": int(float(metrics.get("reach", 0))),
                    "tt_video_views_25": int(float(metrics.get("video_views_p25", 0))),
                    "tt_video_views_50": int(float(metrics.get("video_views_p50", 0))),
                    "tt_video_views_75": int(float(metrics.get("video_views_p75", 0))),
                    "tt_video_views_100": int(
                        float(metrics.get("video_views_p100", 0))
                    ),
                }
            )

        total_page = data.get("data", {}).get("page_info", {}).get("total_page", 1)
        if page >= total_page:
            break
        page += 1

    if not all_rows:
        print("  ⚠️  No TikTok Ads data returned")
        write_table(pd.DataFrame(), "d1_tiktok_ads")
        return

    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"])
    df["week_start"] = df["date"].dt.to_period("W-MON").apply(lambda p: p.start_time)

    # Aggregate daily data into weekly
    weekly = (
        df.groupby("week_start")
        .agg(
            {
                "tt_spend": "sum",
                "tt_impressions": "sum",
                "tt_clicks": "sum",
                "tt_conversions": "sum",
                "tt_reach": "sum",
                "tt_video_views_25": "sum",
                "tt_video_views_50": "sum",
                "tt_video_views_75": "sum",
                "tt_video_views_100": "sum",
            }
        )
        .reset_index()
    )

    # Compute weekly averages
    weekly["tt_cpc"] = (
        (weekly["tt_spend"] / weekly["tt_clicks"].replace(0, float("nan")))
        .fillna(0)
        .round(2)
    )
    weekly["tt_cpm"] = (
        (weekly["tt_spend"] / weekly["tt_impressions"].replace(0, float("nan")) * 1000)
        .fillna(0)
        .round(2)
    )
    weekly["tt_ctr"] = (
        (weekly["tt_clicks"] / weekly["tt_impressions"].replace(0, float("nan")) * 100)
        .fillna(0)
        .round(2)
    )
    weekly["tt_cost_per_conversion"] = (
        (weekly["tt_spend"] / weekly["tt_conversions"].replace(0, float("nan")))
        .fillna(0)
        .round(2)
    )

    weekly = weekly.sort_values("week_start").reset_index(drop=True)
    write_table(weekly, "d1_tiktok_ads")


def refresh_d1_device_type():
    """Sign-ups by device type."""
    df = read_query(
        f"""
        SELECT 
            DATE(event_date) as date,
            IFNULL(platform_type, 'unknown') as device_type,
            COUNT(*) as value
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name = 'self_serve_completed_create_account'
        GROUP BY date, device_type
    """
    )
    write_table(df, "d1_device_type")


def refresh_d1_invoice_revenue():
    """Invoice revenue deduplicated by invoice_id."""
    df = read_query(
        f"""
        SELECT
            application_name,
            DATE(invoice_transaction_date) as date,
            ROUND(SUM(distinct_inv_amount) / 100.0, 2) as invoice_revenue,
            currency,
            country
        FROM (
            SELECT DISTINCT
                invoice_id,
                application_name,
                invoice_transaction_date,
                invoice_amount_paid as distinct_inv_amount,
                currency,
                country
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.KLIQ_Customer_Revenue`
            WHERE invoice_id IS NOT NULL
        )
        GROUP BY application_name, date, currency, country
    """
    )
    write_table(df, "d1_invoice_revenue")


def refresh_d1_appfee_revenue():
    """KLIQ's cut (application fees) deduplicated by application_fee_id."""
    df = read_query(
        f"""
        SELECT
            application_name,
            DATE(application_fee_transaction_date) as date,
            ROUND(SUM(distinct_fee) / 100.0, 2) as app_fee_revenue,
            ROUND(SUM(distinct_refund) / 100.0, 2) as app_fee_refunded
        FROM (
            SELECT DISTINCT
                application_fee_id,
                application_name,
                application_fee_transaction_date,
                application_fee_amount as distinct_fee,
                application_fee_amount_refunded as distinct_refund
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.KLIQ_Customer_Revenue`
            WHERE application_fee_id IS NOT NULL
        )
        GROUP BY application_name, date
    """
    )
    write_table(df, "d1_appfee_revenue")


def refresh_d1_revenue_summary():
    """Revenue summary: new revenue (first sale per app) vs total revenue, by date."""
    df = read_query(
        f"""
        WITH deduped_invoices AS (
            SELECT DISTINCT
                invoice_id,
                application_name,
                DATE(invoice_transaction_date) as date,
                invoice_amount_paid / 100.0 as revenue
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.KLIQ_Customer_Revenue`
            WHERE invoice_id IS NOT NULL
              AND invoice_amount_paid IS NOT NULL
              AND invoice_amount_paid > 0
        ),
        ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (PARTITION BY application_name ORDER BY date ASC) as rn
            FROM deduped_invoices
        )
        SELECT
            date,
            application_name,
            ROUND(revenue, 2) as revenue,
            CASE WHEN rn = 1 THEN 'new_revenue' ELSE 'recurring_revenue' END as revenue_type
        FROM ranked
    """
    )
    write_table(df, "d1_revenue_summary")


def refresh_d1_coach_summary():
    """Coach summary: all apps with revenue OR active users. Includes hosting, GMV, app fees, MAU."""
    df = read_query(
        f"""
        WITH all_apps AS (
            SELECT id as application_id, application_name, created_at
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications`
        ),
        gmv_latest_month AS (
            SELECT MAX(DATE_TRUNC(DATE(paid_at), MONTH)) as latest_month
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.user_subscription_invoices`
            WHERE status = 'paid'
        ),
        gmv AS (
            SELECT
                u.application_id,
                COUNT(DISTINCT u.invoice_id) as total_invoices,
                ROUND(SUM(u.amount_paid) / 100.0, 2) as total_gmv,
                ROUND(SUM(u.application_fee) / 100.0, 2) as total_app_fee_to_kliq,
                ROUND(SUM(CASE
                    WHEN DATE_TRUNC(DATE(u.paid_at), MONTH) = gm.latest_month
                    THEN u.application_fee ELSE 0 END) / 100.0, 2) as app_fee_last_month,
                MAX(u.currency) as currency,
                MIN(u.paid_at) as first_payment
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.user_subscription_invoices` u
            CROSS JOIN gmv_latest_month gm
            WHERE u.status = 'paid'
            GROUP BY u.application_id
        ),
        active_apps AS (
            SELECT application_id, MAX(mau) as latest_mau
            FROM (
                SELECT application_id, mau,
                    ROW_NUMBER() OVER (PARTITION BY application_id ORDER BY month DESC) as rn
                FROM `{TARGET_PROJECT}.{TARGET_DATASET}.d2_mau`
                WHERE mau > 0
            )
            WHERE rn = 1
            GROUP BY application_id
        ),
        hosting AS (
            SELECT
                application_name,
                invoice_paid_transaction_date as txn_date,
                amount_paid as hosting_amount_paid
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.KLIQ_Hosting_Revenue_paid_details`
            WHERE amount_paid > 0
        ),
        latest_full_month AS (
            SELECT MAX(m) as latest_month FROM (
                SELECT DATE_TRUNC(DATE(txn_date), MONTH) as m, COUNT(*) as cnt
                FROM hosting
                GROUP BY m
                HAVING cnt >= 10
            )
        ),
        hosting_summary AS (
            SELECT
                h.application_name,
                ROUND(SUM(h.hosting_amount_paid) / 100.0, 2) as total_hosting_paid,
                ROUND(SUM(CASE
                    WHEN DATE_TRUNC(DATE(h.txn_date), MONTH) = lm.latest_month
                    THEN h.hosting_amount_paid ELSE 0 END) / 100.0, 2) as hosting_last_month
            FROM hosting h
            CROSS JOIN latest_full_month lm
            GROUP BY h.application_name
        )
        SELECT
            a.application_name,
            a.application_id,
            IFNULL(hs.hosting_last_month, 0) as hosting_fee_last_month,
            IFNULL(g.app_fee_last_month, 0) as app_fee_last_month,
            IFNULL(hs.total_hosting_paid, 0) as total_hosting_paid,
            IFNULL(g.total_gmv, 0) as total_gmv,
            IFNULL(g.total_app_fee_to_kliq, 0) as total_app_fee_to_kliq,
            IFNULL(g.total_invoices, 0) as total_invoices,
            IFNULL(g.currency, 'usd') as currency,
            DATE_DIFF(CURRENT_DATE(), DATE(COALESCE(a.created_at, g.first_payment)), MONTH) as months_on_platform,
            DATE(COALESCE(a.created_at, g.first_payment)) as joined_date,
            ROUND(SAFE_DIVIDE(
                IFNULL(g.total_app_fee_to_kliq, 0) + IFNULL(hs.total_hosting_paid, 0),
                IFNULL(g.total_gmv, 0) + IFNULL(hs.total_hosting_paid, 0)
            ) * 100, 1) as kliq_revenue_pct,
            IFNULL(aa.latest_mau, 0) as latest_mau
        FROM all_apps a
        LEFT JOIN gmv g ON a.application_id = g.application_id
        LEFT JOIN active_apps aa ON a.application_id = aa.application_id
        LEFT JOIN hosting_summary hs ON a.application_name = hs.application_name
        WHERE g.total_gmv > 0 OR aa.latest_mau > 0 OR hs.total_hosting_paid > 0
        ORDER BY total_gmv DESC
    """
    )
    write_table(df, "d1_coach_summary")


def refresh_d1_coach_engagement():
    """Monthly community engagement per app: posts, likes, replies, visits."""
    df = read_query(
        f"""
        SELECT
            DATE_TRUNC(DATE(event_date), MONTH) as month,
            application_id,
            COUNTIF(event_name = 'app_opened') as app_opens,
            COUNTIF(event_name IN ('post_on_community', 'post_on_community_feed_with_photo',
                'post_on_community_feed_with_video_and_photo', 'post_on_community_feed_with_voice_notes',
                'post_on_community_feed_with_voice_notes_and_photo', 'post_on_community_feed_with_a_photo',
                'posts_on_community', 'posts_on_community_feed_with_a_photo')) as community_posts,
            COUNTIF(event_name IN ('like_on_community_post', 'likes_community_post')) as community_likes,
            COUNTIF(event_name = 'replies_on_community') as community_replies,
            COUNTIF(event_name = 'visits_community_page') as community_visits,
            COUNTIF(event_name IN ('post_on_community', 'post_on_community_feed_with_photo',
                'post_on_community_feed_with_video_and_photo', 'post_on_community_feed_with_voice_notes',
                'post_on_community_feed_with_voice_notes_and_photo', 'post_on_community_feed_with_a_photo',
                'posts_on_community', 'posts_on_community_feed_with_a_photo',
                'like_on_community_post', 'likes_community_post',
                'replies_on_community', 'visits_community_page')) as total_community_activity
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name IN (
            'app_opened',
            'post_on_community', 'post_on_community_feed_with_photo',
            'post_on_community_feed_with_video_and_photo', 'post_on_community_feed_with_voice_notes',
            'post_on_community_feed_with_voice_notes_and_photo', 'post_on_community_feed_with_a_photo',
            'posts_on_community', 'posts_on_community_feed_with_a_photo',
            'like_on_community_post', 'likes_community_post',
            'replies_on_community', 'visits_community_page'
        )
        GROUP BY month, application_id
        ORDER BY month DESC, app_opens DESC
    """
    )
    write_table(df, "d1_coach_engagement")


def refresh_d1_churn_analysis():
    """Per-app churn analysis: churn rate, content, posts, engagement for correlation visuals."""
    df = read_query(
        f"""
        WITH subs AS (
            SELECT 
                application_id,
                COUNTIF(metric = 'user_subscribed') as total_subscribed,
                COUNTIF(metric = 'cancels_subscription') as total_cancelled,
                COUNTIF(metric = 'recurring_payment') as recurring_payments
            FROM `{TARGET_PROJECT}.{TARGET_DATASET}.d2_subscriptions_revenue`
            GROUP BY application_id
        ),
        active_subs AS (
            SELECT application_id, 
                COUNTIF(status = 'active') as active_subs,
                COUNTIF(status = 'canceled') as canceled_subs
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.subscription_details`
            GROUP BY application_id
        ),
        content AS (
            SELECT application_id, 
                COUNT(*) as courses,
                SUM(module_count) as modules,
                SUM(lesson_count) as lessons
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.ecourses`
            WHERE deleted_at IS NULL
            GROUP BY application_id
        ),
        recipes AS (
            SELECT application_id, COUNT(*) as total_recipes
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.nutritions`
            GROUP BY application_id
        ),
        blogs AS (
            SELECT application_id, COUNT(*) as total_blogs
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.wellness`
            WHERE deleted_at IS NULL
            GROUP BY application_id
        ),
        content_events AS (
            SELECT application_id,
                COUNTIF(event_name = 'live_session_created') as live_sessions_created,
                COUNTIF(event_name = 'live_session_joined') as live_sessions_joined,
                COUNTIF(event_name = 'starts_past_session') as replay_views,
                COUNTIF(event_name = 'publishes_program') as programs_published,
                COUNTIF(event_name = 'starts_program') as program_starts,
                COUNTIF(event_name = 'completes_program') as program_completions
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
            WHERE event_name IN ('live_session_created','live_session_joined','starts_past_session',
                'publishes_program','starts_program','completes_program')
            GROUP BY application_id
        ),
        posts AS (
            SELECT application_id,
                COUNT(*) as total_posts,
                COUNTIF(user_type = 3) as coach_posts,
                COUNTIF(user_type = 5) as user_posts
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.posts`
            GROUP BY application_id
        ),
        engagement AS (
            SELECT application_id,
                SUM(app_opens) as total_app_opens,
                SUM(community_likes) as total_likes,
                SUM(community_replies) as total_replies,
                SUM(community_visits) as total_community_visits,
                SUM(total_community_activity) as total_community_activity
            FROM `{TARGET_PROJECT}.{TARGET_DATASET}.d1_coach_engagement`
            GROUP BY application_id
        ),
        summary AS (
            SELECT application_id, latest_mau, total_gmv, months_on_platform, application_name
            FROM `{TARGET_PROJECT}.{TARGET_DATASET}.d1_coach_summary`
        )
        SELECT 
            s.application_name,
            s.application_id,
            IFNULL(sub.total_subscribed, 0) as total_subscribed,
            IFNULL(sub.total_cancelled, 0) as total_cancelled,
            IFNULL(asub.active_subs, 0) as active_subs,
            IFNULL(asub.canceled_subs, 0) as canceled_subs,
            ROUND(SAFE_DIVIDE(IFNULL(sub.total_cancelled, 0), IFNULL(sub.total_subscribed, 0)) * 100, 1) as churn_rate,
            IFNULL(sub.recurring_payments, 0) as recurring_payments,
            IFNULL(c.courses, 0) as courses,
            IFNULL(c.lessons, 0) as lessons,
            IFNULL(r.total_recipes, 0) as recipes,
            IFNULL(b.total_blogs, 0) as blogs,
            IFNULL(ce.live_sessions_created, 0) as live_sessions_created,
            IFNULL(ce.live_sessions_joined, 0) as live_sessions_joined,
            IFNULL(ce.replay_views, 0) as replay_views,
            IFNULL(ce.programs_published, 0) as programs_published,
            IFNULL(ce.program_starts, 0) as program_starts,
            IFNULL(ce.program_completions, 0) as program_completions,
            IFNULL(c.courses, 0) + IFNULL(r.total_recipes, 0) + IFNULL(b.total_blogs, 0)
                + IFNULL(ce.programs_published, 0) + IFNULL(ce.live_sessions_created, 0) as total_content_items,
            IFNULL(p.total_posts, 0) as total_posts,
            IFNULL(p.coach_posts, 0) as coach_posts,
            IFNULL(p.user_posts, 0) as user_posts,
            IFNULL(e.total_app_opens, 0) as total_app_opens,
            IFNULL(e.total_likes, 0) as total_likes,
            IFNULL(e.total_replies, 0) as total_replies,
            IFNULL(e.total_community_visits, 0) as total_community_visits,
            IFNULL(e.total_community_activity, 0) as total_community_activity,
            s.latest_mau,
            s.total_gmv,
            s.months_on_platform,
            CASE 
                WHEN IFNULL(c.courses, 0) + IFNULL(r.total_recipes, 0) + IFNULL(b.total_blogs, 0)
                    + IFNULL(ce.programs_published, 0) + IFNULL(ce.live_sessions_created, 0) = 0 THEN '0 - No content'
                WHEN IFNULL(c.courses, 0) + IFNULL(r.total_recipes, 0) + IFNULL(b.total_blogs, 0)
                    + IFNULL(ce.programs_published, 0) + IFNULL(ce.live_sessions_created, 0) <= 10 THEN '1 - Light (1-10)'
                WHEN IFNULL(c.courses, 0) + IFNULL(r.total_recipes, 0) + IFNULL(b.total_blogs, 0)
                    + IFNULL(ce.programs_published, 0) + IFNULL(ce.live_sessions_created, 0) <= 50 THEN '2 - Moderate (11-50)'
                ELSE '3 - Heavy (50+)'
            END as content_tier,
            CASE 
                WHEN IFNULL(p.total_posts, 0) = 0 THEN '0 posts'
                WHEN p.total_posts <= 50 THEN '1-50 posts'
                WHEN p.total_posts <= 200 THEN '51-200 posts'
                WHEN p.total_posts <= 1000 THEN '201-1000 posts'
                ELSE '1000+ posts'
            END as post_tier
        FROM summary s
        LEFT JOIN subs sub ON s.application_id = sub.application_id
        LEFT JOIN active_subs asub ON s.application_id = asub.application_id
        LEFT JOIN content c ON s.application_id = c.application_id
        LEFT JOIN recipes r ON s.application_id = r.application_id
        LEFT JOIN blogs b ON s.application_id = b.application_id
        LEFT JOIN content_events ce ON s.application_id = ce.application_id
        LEFT JOIN posts p ON s.application_id = p.application_id
        LEFT JOIN engagement e ON s.application_id = e.application_id
        ORDER BY churn_rate DESC
    """
    )
    write_table(df, "d1_churn_analysis")


def refresh_d1_retention_analysis():
    """Per-app user retention: D1/D7/D14/D30 retention rates + early engagement breakdown."""
    df = read_query(
        f"""
        WITH first_open AS (
            SELECT user_id, application_id, MIN(DATE(event_date)) as first_date
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
            WHERE event_name = 'app_opened' AND user_id IS NOT NULL
            AND DATE(event_date) <= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY user_id, application_id
        ),
        retention AS (
            SELECT f.user_id, f.application_id, f.first_date,
                MAX(CASE WHEN DATE_DIFF(DATE(e.event_date), f.first_date, DAY) BETWEEN 1 AND 1 THEN 1 ELSE 0 END) as ret_d1,
                MAX(CASE WHEN DATE_DIFF(DATE(e.event_date), f.first_date, DAY) BETWEEN 1 AND 7 THEN 1 ELSE 0 END) as ret_d7,
                MAX(CASE WHEN DATE_DIFF(DATE(e.event_date), f.first_date, DAY) BETWEEN 1 AND 14 THEN 1 ELSE 0 END) as ret_d14,
                MAX(CASE WHEN DATE_DIFF(DATE(e.event_date), f.first_date, DAY) BETWEEN 1 AND 30 THEN 1 ELSE 0 END) as ret_d30
            FROM first_open f
            LEFT JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.events` e
                ON f.user_id = e.user_id AND f.application_id = e.application_id AND e.event_name = 'app_opened'
            GROUP BY f.user_id, f.application_id, f.first_date
        ),
        early_engagement AS (
            SELECT f.user_id, f.application_id,
                COUNT(*) as opens_d30,
                COUNT(DISTINCT DATE(e.event_date)) as unique_days_d30
            FROM first_open f
            JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.events` e
                ON f.user_id = e.user_id AND f.application_id = e.application_id
                AND e.event_name = 'app_opened'
                AND DATE_DIFF(DATE(e.event_date), f.first_date, DAY) BETWEEN 0 AND 30
            GROUP BY f.user_id, f.application_id
        ),
        early_content AS (
            SELECT f.user_id, f.application_id,
                COUNTIF(e.event_name IN ('visits_blog', 'engage_with_blog_post')) as blog_engagement,
                COUNTIF(e.event_name = 'visits_community_page') as community_visits,
                COUNTIF(e.event_name IN ('visits_library_page', 'completes_library_video', 'starts_library_video')) as library_engagement,
                COUNTIF(e.event_name IN ('starts_past_session', 'live_session_joined')) as session_engagement,
                COUNTIF(e.event_name IN ('starts_program', 'completes_program')) as program_engagement,
                COUNTIF(e.event_name IN ('like_on_community_post', 'likes_community_post', 'replies_on_community')) as social_engagement,
                COUNTIF(e.event_name = 'checkout_completion') as checkout_completions,
                COUNTIF(e.event_name = 'user_subscribed') as subscribed,
                COUNTIF(e.event_name = 'cancels_subscription') as cancelled
            FROM first_open f
            JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.events` e
                ON f.user_id = e.user_id AND f.application_id = e.application_id
                AND DATE_DIFF(DATE(e.event_date), f.first_date, DAY) BETWEEN 0 AND 30
            GROUP BY f.user_id, f.application_id
        ),
        app_names AS (
            SELECT id as application_id, application_name
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications`
        )
        SELECT
            a.application_name,
            r.application_id,
            COUNT(*) as total_users,
            ROUND(AVG(r.ret_d1) * 100, 1) as d1_retention_pct,
            ROUND(AVG(r.ret_d7) * 100, 1) as d7_retention_pct,
            ROUND(AVG(r.ret_d14) * 100, 1) as d14_retention_pct,
            ROUND(AVG(r.ret_d30) * 100, 1) as d30_retention_pct,
            ROUND(AVG(ee.opens_d30), 1) as avg_opens_first_30d,
            ROUND(AVG(ee.unique_days_d30), 1) as avg_unique_days_first_30d,
            ROUND(AVG(ec.blog_engagement), 1) as avg_blog_engagement_30d,
            ROUND(AVG(ec.community_visits), 1) as avg_community_visits_30d,
            ROUND(AVG(ec.library_engagement), 1) as avg_library_engagement_30d,
            ROUND(AVG(ec.session_engagement), 1) as avg_session_engagement_30d,
            ROUND(AVG(ec.program_engagement), 1) as avg_program_engagement_30d,
            ROUND(AVG(ec.social_engagement), 1) as avg_social_engagement_30d,
            SUM(ec.subscribed) as total_subscribed_30d,
            SUM(ec.cancelled) as total_cancelled_30d,
            ROUND(SAFE_DIVIDE(SUM(ec.cancelled), SUM(ec.subscribed)) * 100, 1) as early_churn_rate
        FROM retention r
        JOIN early_engagement ee ON r.user_id = ee.user_id AND r.application_id = ee.application_id
        JOIN early_content ec ON r.user_id = ec.user_id AND r.application_id = ec.application_id
        LEFT JOIN app_names a ON r.application_id = a.application_id
        GROUP BY a.application_name, r.application_id
        HAVING total_users >= 5
        ORDER BY d30_retention_pct DESC
    """
    )
    write_table(df, "d1_retention_analysis")


def refresh_d1_coach_gmv_timeline():
    """Monthly GMV by coach for line graph over time. GMV = end-user payments to coaches."""
    df = read_query(
        f"""
        SELECT
            DATE_TRUNC(DATE(u.paid_at), MONTH) as month,
            FORMAT_DATE('%b %Y', DATE_TRUNC(DATE(u.paid_at), MONTH)) as month_label,
            EXTRACT(YEAR FROM DATE_TRUNC(DATE(u.paid_at), MONTH)) * 100 + EXTRACT(MONTH FROM DATE_TRUNC(DATE(u.paid_at), MONTH)) as month_sort,
            a.application_name,
            u.application_id,
            ROUND(SUM(u.amount_paid) / 100.0, 2) as gmv,
            ROUND(SUM(u.application_fee) / 100.0, 2) as app_fee_to_kliq,
            COUNT(DISTINCT u.invoice_id) as invoice_count
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.user_subscription_invoices` u
        LEFT JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications` a ON u.application_id = a.id
        WHERE u.status = 'paid'
        GROUP BY month, month_label, month_sort, a.application_name, u.application_id
        ORDER BY month DESC, gmv DESC
    """
    )
    write_table(df, "d1_coach_gmv_timeline")


def refresh_d1_ga4_acquisition():
    """GA4 sign-up acquisition: device, source, country by date."""
    df = read_ga4_query(
        f"""
        SELECT
            PARSE_DATE('%Y%m%d', event_date) as date,
            IFNULL(collected_traffic_source.manual_source,
                IFNULL(traffic_source.source, '(direct)')) as source,
            IFNULL(collected_traffic_source.manual_medium,
                IFNULL(traffic_source.medium, '(none)')) as medium,
            IFNULL(collected_traffic_source.manual_campaign_name,
                IFNULL(traffic_source.name, '(not set)')) as campaign,
            device.category as device_type,
            device.operating_system as os,
            geo.country as country,
            COUNT(DISTINCT user_pseudo_id) as unique_users
        FROM `{SOURCE_PROJECT}.{GA4_DATASET}.events_intraday_*`
        WHERE event_name = 'sign_up'
        GROUP BY date, source, medium, campaign, device_type, os, country
        ORDER BY date DESC
    """
    )
    write_table(df, "d1_ga4_acquisition")


def refresh_d1_ga4_traffic():
    """GA4 website traffic: all sessions grouped by channel, device, country by date."""
    df = read_ga4_query(
        f"""
        WITH raw AS (
            SELECT
                PARSE_DATE('%Y%m%d', event_date) as date,
                IFNULL(collected_traffic_source.manual_source,
                    IFNULL(traffic_source.source, '(direct)')) as raw_source,
                IFNULL(collected_traffic_source.manual_medium,
                    IFNULL(traffic_source.medium, '(none)')) as medium,
                device.category as device_type,
                geo.country as country,
                user_pseudo_id
            FROM `{SOURCE_PROJECT}.{GA4_DATASET}.events_intraday_*`
            WHERE event_name = 'session_start'
        )
        SELECT
            date,
            CASE
                WHEN raw_source IN ('facebook', 'fb', 'facebook.com', 'm.facebook.com',
                    'l.facebook.com', 'l.instagram.com', 'instagram', 'MetaAds') THEN 'Meta'
                WHEN raw_source IN ('tiktok', 'TikTok') THEN 'TikTok'
                WHEN raw_source = 'google' THEN 'Google'
                WHEN raw_source IN ('bing', 'yahoo', 'duckduckgo') THEN 'Other Search'
                WHEN raw_source IN ('youtube', 'youtube.com') THEN 'YouTube'
                WHEN raw_source IN ('reddit', 'reddit.com') THEN 'Reddit'
                WHEN raw_source IN ('rewardful') THEN 'Rewardful (Affiliate)'
                WHEN raw_source IN ('powered_by_kliq') THEN 'Powered by KLIQ'
                WHEN raw_source = '(direct)' THEN 'Direct'
                ELSE 'Other'
            END as channel,
            medium,
            device_type,
            country,
            COUNT(DISTINCT user_pseudo_id) as sessions
        FROM raw
        GROUP BY date, channel, medium, device_type, country
        ORDER BY date DESC
    """
    )
    write_table(df, "d1_ga4_traffic")


def refresh_d1_ga4_funnel():
    """GA4 website funnel: form_start → form_submit → sign_up by date and source."""
    df = read_ga4_query(
        f"""
        SELECT
            PARSE_DATE('%Y%m%d', event_date) as date,
            event_name as funnel_step,
            CASE event_name
                WHEN 'form_start' THEN 1
                WHEN 'form_submit' THEN 2
                WHEN 'sign_up' THEN 3
            END as step_order,
            device.category as device_type,
            IFNULL(collected_traffic_source.manual_source,
                IFNULL(traffic_source.source, '(direct)')) as source,
            COUNT(DISTINCT user_pseudo_id) as unique_users
        FROM `{SOURCE_PROJECT}.{GA4_DATASET}.events_intraday_*`
        WHERE event_name IN ('form_start', 'form_submit', 'sign_up')
        GROUP BY date, funnel_step, step_order, device_type, source
        ORDER BY date DESC, step_order
    """
    )
    write_table(df, "d1_ga4_funnel")


def refresh_d1_app_status():
    """App status: engagement + subscription status per app."""
    df = read_query(
        f"""
        WITH all_apps AS (
            SELECT id as application_id, application_name, created_at
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications`
        ),
        sub_apps AS (
            SELECT DISTINCT application_id, 
                MAX(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as has_active_sub
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.subscription_details`
            GROUP BY application_id
        ),
        engaged_apps AS (
            SELECT DISTINCT application_id
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
            WHERE event_name = 'app_opened'
            AND event_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
        )
        SELECT 
            a.application_id,
            a.application_name,
            CASE WHEN e.application_id IS NOT NULL THEN 'active_engagement' ELSE 'no_recent_engagement' END as engagement_status,
            CASE 
                WHEN s.application_id IS NULL THEN 'no_subscription'
                WHEN s.has_active_sub = 1 THEN 'active_subscription'
                ELSE 'churned_subscription'
            END as subscription_status
        FROM all_apps a
        LEFT JOIN sub_apps s ON a.application_id = s.application_id
        LEFT JOIN engaged_apps e ON a.application_id = e.application_id
    """
    )
    write_table(df, "d1_app_status")


# ═══════════════════════════════════════════════════════════════
# DASHBOARD 2 — App Health Score
# ═══════════════════════════════════════════════════════════════


def refresh_d2_app_lookup():
    """Application lookup table."""
    df = read_query(
        f"""
        SELECT 
            id as application_id,
            application_name,
            created_at
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications`
    """
    )
    write_table(df, "d2_app_lookup")


def refresh_d2_engagement():
    """Engagement events by app and date."""
    df = read_query(
        f"""
        SELECT 
            application_id,
            DATE(event_date) as date,
            event_name as metric,
            COUNT(*) as value
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name IN (
            'live_session_joined', 'live_session_created',
            'create_module', 'completes_module',
            'creates_post', 'creates_program',
            'creates_event', 'creates_ecourse',
            'publish_module', 'publishes_program'
        )
        GROUP BY application_id, date, metric
    """
    )
    write_table(df, "d2_engagement")


def refresh_d2_subscriptions_revenue():
    """Subscription and revenue events by app and date."""
    df = read_query(
        f"""
        SELECT 
            application_id,
            DATE(event_date) as date,
            event_name as metric,
            COUNT(*) as value
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name IN (
            'user_subscribed', 'cancels_subscription',
            'selects_subscription', 'checkout_started',
            'checkout_completion', 'recurring_payment',
            'purchase_success', 'purchase_cancelled'
        )
        GROUP BY application_id, date, metric
    """
    )
    write_table(df, "d2_subscriptions_revenue")


def refresh_d2_user_overview():
    """User overview by app (user counts + platform breakdown)."""
    df = read_query(
        f"""
        WITH user_counts AS (
            SELECT 
                application_id,
                COUNT(DISTINCT id) as total_users,
                COUNT(DISTINCT CASE WHEN user_type = 4 THEN id END) as talent_users,
                COUNT(DISTINCT CASE WHEN user_type = 5 THEN id END) as regular_users
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.users`
            GROUP BY application_id
        ),
        platform_counts AS (
            SELECT 
                application_id,
                COUNT(DISTINCT CASE WHEN platform_type = 'web' THEN user_id END) as web_users,
                COUNT(DISTINCT CASE WHEN platform_type != 'web' AND platform_type IS NOT NULL THEN user_id END) as app_users
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
            WHERE event_name = 'app_opened'
            GROUP BY application_id
        )
        SELECT 
            u.application_id,
            a.application_name,
            u.total_users,
            u.talent_users,
            u.regular_users,
            IFNULL(p.web_users, 0) as web_users,
            IFNULL(p.app_users, 0) as app_users
        FROM user_counts u
        LEFT JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications` a ON u.application_id = a.id
        LEFT JOIN platform_counts p ON u.application_id = p.application_id
        ORDER BY u.total_users DESC
    """
    )
    write_table(df, "d2_user_overview")


def refresh_d2_dau():
    """Daily Active Users by app."""
    df = read_query(
        f"""
        SELECT 
            application_id,
            DATE(event_date) as date,
            COUNT(DISTINCT user_id) as dau
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name = 'app_opened'
        GROUP BY application_id, date
    """
    )
    write_table(df, "d2_dau")


def refresh_d2_mau():
    """Monthly Active Users by app."""
    df = read_query(
        f"""
        SELECT 
            application_id,
            DATE_TRUNC(DATE(event_date), MONTH) as month,
            COUNT(DISTINCT user_id) as mau
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events`
        WHERE event_name = 'app_opened'
        GROUP BY application_id, month
    """
    )
    write_table(df, "d2_mau")


def refresh_d1_appstore_sales():
    """Pull latest Apple App Store sales data and append to BigQuery."""
    with open(APPLE_KEY_FILE, "r") as f:
        apple_key = f.read()

    def apple_token():
        now = int(time.time())
        payload = {
            "iss": APPLE_ISSUER_ID,
            "iat": now,
            "exp": now + 1200,
            "aud": "appstoreconnect-v1",
        }
        return jwt.encode(
            payload, apple_key, algorithm="ES256", headers={"kid": APPLE_KEY_ID}
        )

    def get_sales_report(date_str):
        headers = {"Authorization": f"Bearer {apple_token()}"}
        resp = requests.get(
            "https://api.appstoreconnect.apple.com/v1/salesReports",
            headers=headers,
            params={
                "filter[reportType]": "SALES",
                "filter[reportSubType]": "SUMMARY",
                "filter[frequency]": "DAILY",
                "filter[reportDate]": date_str,
                "filter[vendorNumber]": APPLE_VENDOR,
            },
        )
        if resp.status_code == 200:
            content = gzip.decompress(resp.content).decode("utf-8")
            return pd.read_csv(io.StringIO(content), sep="\t")
        return None

    # Pull last 7 days to catch any gaps
    all_dfs = []
    for i in range(1, 8):
        d = date.today() - timedelta(days=i)
        df = get_sales_report(d.strftime("%Y-%m-%d"))
        if df is not None and len(df) > 0:
            all_dfs.append(df)
        time.sleep(0.3)

    if not all_dfs:
        print("  ⚠️  No Apple sales data available")
        return

    combined = pd.concat(all_dfs, ignore_index=True)
    combined.columns = [c.strip().replace(" ", "_").lower() for c in combined.columns]
    combined["report_date"] = pd.to_datetime(combined["begin_date"], format="%m/%d/%Y")

    # Delete existing rows for these dates, then append
    min_date = combined["report_date"].min().strftime("%Y-%m-%d")
    max_date = combined["report_date"].max().strftime("%Y-%m-%d")
    delete_sql = f"""
        DELETE FROM `{TARGET_PROJECT}.{TARGET_DATASET}.d1_appstore_sales`
        WHERE report_date BETWEEN '{min_date}' AND '{max_date}'
    """
    try:
        write_client.query(delete_sql).result()
    except Exception:
        pass  # Table may not exist yet on first run

    table_id = f"{TARGET_PROJECT}.{TARGET_DATASET}.d1_appstore_sales"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    job = write_client.load_table_from_dataframe(
        combined, table_id, job_config=job_config
    )
    job.result()
    print(f"  ✅ d1_appstore_sales — {len(combined)} rows ({min_date} to {max_date})")


def refresh_d1_unified_revenue():
    """Combine Stripe GMV + iOS App Store + Google Play Store revenue per app per month.

    Apple developer_proceeds are in local currency (currency_of_proceeds),
    so we convert to USD using approximate exchange rates.
    Stripe amounts are converted to USD using approximate FX rates.
    Google Play revenue is estimated from purchase_success events using
    the average iOS revenue per purchase as a proxy (since Play doesn't
    report dollar amounts in events).
    """
    df = read_query(
        f"""
        WITH 
        -- Approximate exchange rates to USD (as of early 2025)
        fx_rates AS (
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
                STRUCT('AED', 0.272)
            ])
        ),
        stripe_fx AS (
            SELECT currency, rate FROM UNNEST([
                STRUCT('usd' AS currency, 1.0 AS rate),
                STRUCT('gbp', 1.27),
                STRUCT('eur', 1.08),
                STRUCT('aud', 0.64),
                STRUCT('cad', 0.72)
            ])
        ),
        stripe_revenue AS (
            SELECT 
                a.application_name,
                CAST(u.application_id AS INT64) as application_id,
                DATE_TRUNC(DATE(u.paid_at), MONTH) as month,
                FORMAT_DATE('%b %Y', DATE_TRUNC(DATE(u.paid_at), MONTH)) as month_label,
                EXTRACT(YEAR FROM DATE_TRUNC(DATE(u.paid_at), MONTH)) * 100 + EXTRACT(MONTH FROM DATE_TRUNC(DATE(u.paid_at), MONTH)) as month_sort,
                ROUND(SUM(u.amount_paid / 100.0 * COALESCE(sfx.rate, 1.0)), 2) as revenue,
                'Stripe' as revenue_source
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.user_subscription_invoices` u
            LEFT JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications` a ON u.application_id = a.id
            LEFT JOIN stripe_fx sfx ON LOWER(u.currency) = sfx.currency
            WHERE u.status = 'paid'
            GROUP BY a.application_name, u.application_id, month, month_label, month_sort
        ),
        ios_app_map AS (
            SELECT DISTINCT 
                LOWER(sku) as sku_lower,
                FIRST_VALUE(title) OVER (PARTITION BY LOWER(sku) ORDER BY units DESC) as app_name
            FROM `{TARGET_PROJECT}.{TARGET_DATASET}.d1_appstore_sales`
            WHERE product_type_identifier IN ('1F', '3F', '7F')
            AND title IS NOT NULL AND title != ''
        ),
        ios_revenue AS (
            SELECT 
                COALESCE(m.app_name, s.title) as application_name,
                CAST(NULL AS INT64) as application_id,
                DATE_TRUNC(s.report_date, MONTH) as month,
                FORMAT_DATE('%b %Y', DATE_TRUNC(s.report_date, MONTH)) as month_label,
                CAST(FORMAT_DATE('%Y%m', DATE_TRUNC(s.report_date, MONTH)) AS INT64) as month_sort,
                ROUND(SUM(s.developer_proceeds * COALESCE(fx.rate, 1.0)), 2) as revenue,
                'iOS App Store' as revenue_source
            FROM `{TARGET_PROJECT}.{TARGET_DATASET}.d1_appstore_sales` s
            LEFT JOIN ios_app_map m ON LOWER(s.parent_identifier) = m.sku_lower
            LEFT JOIN fx_rates fx ON s.currency_of_proceeds = fx.currency
            WHERE s.product_type_identifier = 'IAY'
            AND s.developer_proceeds > 0
            GROUP BY application_name, month, month_label, month_sort
        ),
        -- Google Play Store: purchase_success events (in-app purchases via Play Store)
        -- These events don't carry dollar amounts, so we estimate revenue using
        -- the average iOS App Store revenue per purchase as a proxy.
        ios_avg_rev AS (
            SELECT SAFE_DIVIDE(
                SUM(developer_proceeds * COALESCE(fx.rate, 1.0)),
                NULLIF(SUM(units), 0)
            ) as avg_rev_per_purchase
            FROM `{TARGET_PROJECT}.{TARGET_DATASET}.d1_appstore_sales` s
            LEFT JOIN fx_rates fx ON s.currency_of_proceeds = fx.currency
            WHERE s.product_type_identifier = 'IAY'
            AND s.developer_proceeds > 0
        ),
        google_play_revenue AS (
            SELECT 
                a.application_name,
                CAST(e.application_id AS INT64) as application_id,
                DATE_TRUNC(DATE(e.event_date), MONTH) as month,
                FORMAT_DATE('%b %Y', DATE_TRUNC(DATE(e.event_date), MONTH)) as month_label,
                EXTRACT(YEAR FROM DATE_TRUNC(DATE(e.event_date), MONTH)) * 100 + EXTRACT(MONTH FROM DATE_TRUNC(DATE(e.event_date), MONTH)) as month_sort,
                ROUND(COUNT(*) * COALESCE(iavg.avg_rev_per_purchase, 5.0), 2) as revenue,
                'Google Play Store' as revenue_source
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events` e
            LEFT JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications` a ON e.application_id = a.id
            CROSS JOIN ios_avg_rev iavg
            WHERE e.event_name = 'purchase_success'
            GROUP BY a.application_name, e.application_id, month, month_label, month_sort, iavg.avg_rev_per_purchase
        )
        SELECT * FROM stripe_revenue
        UNION ALL
        SELECT * FROM ios_revenue
        UNION ALL
        SELECT * FROM google_play_revenue
        ORDER BY month_sort DESC, application_name
    """
    )
    write_table(df, "d1_unified_revenue")


def refresh_d1_ios_downloads():
    """iOS App Store downloads per app per month (first downloads + redownloads)."""
    df = read_query(
        f"""
        SELECT 
            title as application_name,
            DATE_TRUNC(report_date, MONTH) as month,
            FORMAT_DATE('%b %Y', DATE_TRUNC(report_date, MONTH)) as month_label,
            CAST(FORMAT_DATE('%Y%m', DATE_TRUNC(report_date, MONTH)) AS INT64) as month_sort,
            SUM(units) as ios_downloads,
            SUM(CASE WHEN product_type_identifier = '1F' THEN units ELSE 0 END) as first_downloads,
            SUM(CASE WHEN product_type_identifier IN ('3F','7F') THEN units ELSE 0 END) as redownloads
        FROM `{TARGET_PROJECT}.{TARGET_DATASET}.d1_appstore_sales`
        WHERE product_type_identifier IN ('1F', '3F', '7F')
        GROUP BY title, month, month_label, month_sort
        ORDER BY month_sort DESC, ios_downloads DESC
    """
    )
    write_table(df, "d1_ios_downloads")


def refresh_d1_app_engagement():
    """Avg user engagement per app per feature across D1/D7/D14/D30/D60/D90 windows."""
    df = read_query(
        f"""
        WITH feature_events AS (
            SELECT 
                a.application_name,
                e.user_id,
                DATE(e.event_date) as event_day,
                CASE 
                    WHEN e.event_name = 'app_opened' THEN 'App Open'
                    WHEN e.event_name = 'visits_community_page' THEN 'Community'
                    WHEN e.event_name IN ('engage_with_blog_post', 'visits_blog', 'visits_course_blog') THEN 'Blog'
                    WHEN e.event_name = 'visits_library_page' THEN 'Library'
                    WHEN e.event_name IN ('visits_program_page', 'visits_program_detail_page', 'completes_program_workout', 'starts_program', 'completes_program') THEN 'Programs'
                    WHEN e.event_name IN ('engages_with_recipe', 'visits_nutrition_page') THEN 'Nutrition'
                    WHEN e.event_name IN ('live_session_joined', 'starts_past_session', 'commented_in_live_session') THEN 'Live Sessions'
                    WHEN e.event_name IN ('starts_library_video', 'completes_library_video', 'ends_library_video') THEN 'Video Library'
                    WHEN e.event_name IN ('like_on_community_post', 'replies_on_community', 'post_on_community', 'post_on_community_feed_with_photo') THEN 'Community Engagement'
                    ELSE 'Other'
                END as feature
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events` e
            JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications` a ON e.application_id = a.id
            WHERE e.event_name IN (
                'app_opened', 'visits_community_page', 'engage_with_blog_post', 'visits_blog',
                'visits_library_page', 'visits_program_page', 'visits_program_detail_page',
                'completes_program_workout', 'starts_program', 'completes_program',
                'engages_with_recipe', 'visits_nutrition_page',
                'live_session_joined', 'starts_past_session', 'commented_in_live_session',
                'starts_library_video', 'completes_library_video', 'ends_library_video',
                'like_on_community_post', 'replies_on_community', 'post_on_community',
                'post_on_community_feed_with_photo', 'visits_course_blog'
            )
            AND e.user_type = 5
            AND e.platform_type = 'app'
        ),
        daily_counts AS (
            SELECT application_name, user_id, feature, event_day, COUNT(*) as daily_events
            FROM feature_events
            GROUP BY application_name, user_id, feature, event_day
        ),
        windowed AS (
            SELECT 
                application_name, feature, user_id,
                SUM(CASE WHEN event_day = CURRENT_DATE() THEN daily_events ELSE 0 END) as d1_events,
                SUM(CASE WHEN event_day >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) THEN daily_events ELSE 0 END) as d7_events,
                SUM(CASE WHEN event_day >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY) THEN daily_events ELSE 0 END) as d14_events,
                SUM(CASE WHEN event_day >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN daily_events ELSE 0 END) as d30_events,
                SUM(CASE WHEN event_day >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY) THEN daily_events ELSE 0 END) as d60_events,
                SUM(CASE WHEN event_day >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) THEN daily_events ELSE 0 END) as d90_events
            FROM daily_counts
            GROUP BY application_name, feature, user_id
        )
        SELECT 
            application_name, feature,
            COUNT(DISTINCT user_id) as unique_users,
            ROUND(AVG(d1_events), 2) as avg_d1,
            ROUND(AVG(d7_events), 2) as avg_d7,
            ROUND(AVG(d14_events), 2) as avg_d14,
            ROUND(AVG(d30_events), 2) as avg_d30,
            ROUND(AVG(d60_events), 2) as avg_d60,
            ROUND(AVG(d90_events), 2) as avg_d90
        FROM windowed
        GROUP BY application_name, feature
        HAVING unique_users >= 1
        ORDER BY application_name, unique_users DESC
    """
    )
    write_table(df, "d1_app_engagement")


def refresh_d1_app_device_breakdown():
    """Device breakdown (app vs web) per application."""
    df = read_query(
        f"""
        SELECT 
            a.application_name,
            e.platform_type as device,
            COUNT(DISTINCT e.user_id) as unique_users,
            COUNT(*) as total_events
        FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events` e
        JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications` a ON e.application_id = a.id
        WHERE e.user_type = 5
        AND e.platform_type IN ('app', 'web')
        GROUP BY a.application_name, e.platform_type
        ORDER BY a.application_name
    """
    )
    write_table(df, "d1_app_device_breakdown")


def refresh_d1_app_downloads():
    """Downloads per app: iOS App Store + KLIQ registered users."""
    df = read_query(
        f"""
        WITH ios AS (
            SELECT 
                title as application_name,
                SUM(CASE WHEN product_type_identifier IN ('1F','3F') THEN units ELSE 0 END) as ios_first_downloads,
                SUM(CASE WHEN product_type_identifier = '7F' THEN units ELSE 0 END) as ios_redownloads
            FROM `{TARGET_PROJECT}.{TARGET_DATASET}.d1_appstore_sales`
            WHERE product_type_identifier IN ('1F', '3F', '7F')
            GROUP BY title
        ),
        kliq_signups AS (
            SELECT 
                a.application_name,
                COUNT(DISTINCT u.id) as kliq_users
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.users` u
            JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications` a ON u.application_id = a.id
            WHERE u.user_type = 5
            GROUP BY a.application_name
        )
        SELECT 
            COALESCE(k.application_name, i.application_name) as application_name,
            COALESCE(i.ios_first_downloads, 0) as ios_first_downloads,
            COALESCE(i.ios_redownloads, 0) as ios_redownloads,
            COALESCE(i.ios_first_downloads, 0) + COALESCE(i.ios_redownloads, 0) as ios_total_downloads,
            COALESCE(k.kliq_users, 0) as kliq_registered_users
        FROM kliq_signups k
        FULL OUTER JOIN ios i ON LOWER(TRIM(k.application_name)) = LOWER(TRIM(i.application_name))
        ORDER BY ios_total_downloads DESC
    """
    )
    write_table(df, "d1_app_downloads")


def refresh_d1_app_top_users():
    """Top 5 most active users per app in last 90 days with email."""
    df = read_query(
        f"""
        WITH user_activity AS (
            SELECT 
                a.application_name,
                e.user_id,
                COUNT(*) as total_events,
                COUNT(DISTINCT DATE(e.event_date)) as active_days,
                MAX(e.event_date) as last_active
            FROM `{SOURCE_PROJECT}.{SOURCE_DATASET}.events` e
            JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.applications` a ON e.application_id = a.id
            WHERE e.user_type = 5
            AND e.platform_type = 'app'
            AND e.event_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
            GROUP BY a.application_name, e.user_id
        ),
        ranked AS (
            SELECT ua.*, ROW_NUMBER() OVER (PARTITION BY ua.application_name ORDER BY ua.total_events DESC) as rank
            FROM user_activity ua
        )
        SELECT 
            r.application_name,
            r.user_id,
            u.email as user_email,
            r.total_events,
            r.active_days,
            r.last_active,
            r.rank as user_rank
        FROM ranked r
        LEFT JOIN `{SOURCE_PROJECT}.{SOURCE_DATASET}.users` u ON r.user_id = u.id
        WHERE r.rank <= 5
        ORDER BY r.application_name, r.rank
    """
    )
    write_table(df, "d1_app_top_users")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════


def main():
    print("🔄 KLIQ Dashboard Refresh Starting...\n")

    ensure_dataset()

    print("📊 Dashboard 1 — Main Growth:")
    refresh_d1_growth_metrics()
    refresh_d1_onboarding_funnel()
    refresh_d1_engagement_funnel()
    refresh_d1_activation_score()
    refresh_d1_leads_sales()
    refresh_d1_device_type()
    refresh_d1_invoice_revenue()
    refresh_d1_appfee_revenue()
    refresh_d1_revenue_summary()
    refresh_d1_coach_summary()
    refresh_d1_coach_engagement()
    refresh_d1_churn_analysis()
    refresh_d1_retention_analysis()
    refresh_d1_coach_gmv_timeline()
    refresh_d1_app_status()

    print("\n📊 Leads & Sales — External Sources:")
    refresh_d1_demo_calls()
    refresh_d1_meta_ads()
    refresh_d1_tiktok_ads()

    print("\n📊 GA4 — Website Acquisition:")
    refresh_d1_ga4_acquisition()
    refresh_d1_ga4_traffic()
    refresh_d1_ga4_funnel()

    print("\n📊 App Store Data:")
    refresh_d1_appstore_sales()
    refresh_d1_unified_revenue()
    refresh_d1_ios_downloads()

    print("\n📊 App Performance:")
    refresh_d1_app_engagement()
    refresh_d1_app_device_breakdown()
    refresh_d1_app_downloads()
    refresh_d1_app_top_users()

    print("\n📊 Dashboard 2 — App Health Score:")
    refresh_d2_app_lookup()
    refresh_d2_engagement()
    refresh_d2_subscriptions_revenue()
    refresh_d2_user_overview()
    refresh_d2_dau()
    refresh_d2_mau()

    print("\n✅ All dashboard tables refreshed!")
    print(f"📍 Power BI should connect to: {TARGET_PROJECT}.{TARGET_DATASET}")


if __name__ == "__main__":
    main()
