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
