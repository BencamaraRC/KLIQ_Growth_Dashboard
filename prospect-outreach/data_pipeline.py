"""
Data pipeline: pulls new sign-ups and their activation events from BigQuery.
Builds a unified prospect profile for each new coach.
"""

import os
import json
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
from config import GCP_PROJECT, DATA_PROJECT, BQ_LOCATION, SERVICE_ACCOUNT_KEY

_client = None


def get_client():
    """Reuse a single BigQuery client."""
    global _client
    if _client is None:
        if SERVICE_ACCOUNT_KEY and os.path.exists(SERVICE_ACCOUNT_KEY):
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_KEY
            )
        else:
            import google.auth

            creds, _ = google.auth.default()
        _client = bigquery.Client(
            credentials=creds, project=GCP_PROJECT, location=BQ_LOCATION
        )
    return _client


def fetch_new_signups(since_hours=24):
    """
    Fetch prospects who completed sign-up in the last N hours.
    Returns list of dicts with: name, email, uuid, device_type, signup_date, application_id.
    """
    client = get_client()
    sql = f"""
    SELECT
        e.application_id,
        JSON_EXTRACT_SCALAR(e.data, '$.name') AS name,
        JSON_EXTRACT_SCALAR(e.data, '$.email') AS email,
        JSON_EXTRACT_SCALAR(e.data, '$.uuid') AS uuid,
        JSON_EXTRACT_SCALAR(e.data, '$.device_type') AS device_type,
        JSON_EXTRACT_SCALAR(e.data, '$.loginType') AS login_type,
        e.event_date AS signup_date
    FROM `{DATA_PROJECT}.prod_dataset.events` e
    WHERE e.event_name = 'self_serve_completed'
      AND e.data IS NOT NULL
      AND e.event_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {since_hours} HOUR)
    ORDER BY e.event_date DESC
    """
    df = client.query(sql).to_dataframe()
    return df.to_dict("records") if not df.empty else []


def has_returned_after_signup(application_id):
    """
    Check if a user has any events AFTER their self_serve_completed event.
    Returns True if they have logged back in / done anything after signup.
    """
    client = get_client()
    sql = f"""
    WITH signup AS (
        SELECT event_date
        FROM `{DATA_PROJECT}.prod_dataset.events`
        WHERE application_id = {application_id}
          AND event_name = 'self_serve_completed'
        ORDER BY event_date DESC
        LIMIT 1
    )
    SELECT COUNT(*) as post_signup_events
    FROM `{DATA_PROJECT}.prod_dataset.events` e
    CROSS JOIN signup s
    WHERE e.application_id = {application_id}
      AND e.event_date > s.event_date
      AND e.event_name NOT IN ('self_serve_completed', 'user_signed_up', 'coach_type_updated')
    """
    try:
        df = client.query(sql).to_dataframe()
        if not df.empty:
            return df.iloc[0]["post_signup_events"] > 0
    except Exception:
        pass
    return False


def _lookup_phone(client, email):
    """Look up a phone number from prod_dataset.applications by email."""
    sql = f"""
    SELECT phone_number
    FROM `{DATA_PROJECT}.prod_dataset.applications`
    WHERE LOWER(email) = LOWER('{email}')
      AND phone_number IS NOT NULL
      AND phone_number != 'NULL'
      AND phone_number != ''
    LIMIT 1
    """
    try:
        df = client.query(sql).to_dataframe()
        if not df.empty:
            return df.iloc[0]["phone_number"]
    except Exception:
        pass
    return None


def fetch_all_phones():
    """
    Fetch all prospects with valid phone numbers from prod_dataset.applications.
    Returns list of dicts with: application_id, application_name, phone_number, email, created_at.
    """
    client = get_client()
    sql = f"""
    SELECT
        a.id AS application_id,
        a.application_name,
        a.phone_number,
        a.email,
        a.created_at
    FROM `{DATA_PROJECT}.prod_dataset.applications` a
    WHERE a.phone_number IS NOT NULL
      AND a.phone_number != 'NULL'
      AND a.phone_number != ''
    ORDER BY a.created_at DESC
    """
    df = client.query(sql).to_dataframe()
    return df.to_dict("records") if not df.empty else []


def fetch_prospect_profile(application_id):
    """
    Build a full prospect profile for a given application_id.
    Combines: app info, coach type, country, activation actions, profile image status.
    """
    client = get_client()

    profile = {"application_id": application_id}

    # App info (name, email, created_at)
    sql_app = f"""
    SELECT application_name, email, created_at
    FROM `{DATA_PROJECT}.prod_dataset.applications`
    WHERE id = {application_id}
    LIMIT 1
    """
    app_df = client.query(sql_app).to_dataframe()

    if not app_df.empty:
        row = app_df.iloc[0]
        profile["app_name"] = row.get("application_name")
        profile["email"] = row.get("email")
        profile["created_at"] = row.get("created_at")

        # Pull phone from self-serve signup tables (joined by email)
        email = row.get("email")
        if email:
            phone = _lookup_phone(client, email)
            profile["phone"] = phone

    # Coach type + country
    sql_type = f"""
    SELECT
        JSON_EXTRACT_SCALAR(data, '$.coach_type') AS coach_type,
        JSON_EXTRACT_SCALAR(data, '$.country') AS country
    FROM `{DATA_PROJECT}.prod_dataset.events`
    WHERE application_id = {application_id}
      AND event_name = 'coach_type_updated'
      AND data IS NOT NULL
    ORDER BY event_date DESC
    LIMIT 1
    """
    type_df = client.query(sql_type).to_dataframe()
    if not type_df.empty:
        profile["coach_type"] = type_df.iloc[0].get("coach_type")
        profile["country"] = type_df.iloc[0].get("country")

    # Profile image uploaded?
    sql_img = f"""
    SELECT COUNT(*) AS cnt
    FROM `{DATA_PROJECT}.prod_dataset.events`
    WHERE application_id = {application_id}
      AND event_name IN ('profile_image_added', 'profile_image_added_your_store')
    """
    img_df = client.query(sql_img).to_dataframe()
    profile["has_profile_image"] = (
        int(img_df.iloc[0]["cnt"]) > 0 if not img_df.empty else False
    )

    # Activation actions completed
    sql_actions = f"""
    SELECT DISTINCT event_name
    FROM `{DATA_PROJECT}.prod_dataset.events`
    WHERE application_id = {application_id}
      AND event_name IN (
          'create_module', 'publish_module', 'live_session_created',
          'creates_program', 'publishes_program', 'post_on_community',
          'post_on_community_feed_with_photo',
          'subscription_selected_talent', 'self_serve_completed_add_payment_info'
      )
    """
    actions_df = client.query(sql_actions).to_dataframe()
    profile["actions_completed"] = (
        actions_df["event_name"].tolist() if not actions_df.empty else []
    )

    # Selected worlds (from onboarding)
    sql_worlds = f"""
    SELECT JSON_EXTRACT_SCALAR(data, '$.selectedWorlds') AS worlds
    FROM `{DATA_PROJECT}.prod_dataset.events`
    WHERE application_id = {application_id}
      AND event_name = 'self_serve_completed_creator_type'
      AND data IS NOT NULL
    ORDER BY event_date DESC
    LIMIT 1
    """
    worlds_df = client.query(sql_worlds).to_dataframe()
    if not worlds_df.empty and worlds_df.iloc[0]["worlds"]:
        try:
            profile["selected_worlds"] = json.loads(worlds_df.iloc[0]["worlds"])
        except (json.JSONDecodeError, TypeError):
            profile["selected_worlds"] = []
    else:
        profile["selected_worlds"] = []

    return profile


def fetch_recent_events(since_hours=1):
    """
    Fetch recent activation events that could trigger outreach sequences.
    Returns events with application_id, event_name, event_date, and data.
    """
    client = get_client()
    sql = f"""
    SELECT
        application_id,
        event_name,
        event_date,
        data
    FROM `{DATA_PROJECT}.prod_dataset.events`
    WHERE event_name IN (
        'self_serve_completed',
        'profile_image_added',
        'profile_image_added_your_store',
        'coach_type_updated',
        'create_module',
        'publish_module'
    )
    AND event_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {since_hours} HOUR)
    ORDER BY event_date DESC
    """
    df = client.query(sql).to_dataframe()
    return df.to_dict("records") if not df.empty else []


if __name__ == "__main__":
    # Quick test
    print("=== Recent sign-ups (last 48h) ===")
    signups = fetch_new_signups(since_hours=48)
    for s in signups:
        print(f"  {s['signup_date']}  {s['name']:30s}  {s['email']}")

    if signups:
        app_id = signups[0]["application_id"]
        print(f"\n=== Profile for app_id={app_id} ===")
        profile = fetch_prospect_profile(app_id)
        for k, v in profile.items():
            print(f"  {k}: {v}")
