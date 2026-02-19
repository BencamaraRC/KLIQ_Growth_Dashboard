"""
Main sequence engine runner.
Polls BigQuery for new events and triggers the appropriate outreach sequences.
Can be run as a cron job or long-running process.
"""

import json
import time
from datetime import datetime, timezone
import pandas as pd

from config import POLL_INTERVAL_MINUTES, DRY_RUN, SEQUENCE_TRIGGERS
from data_pipeline import fetch_new_signups, fetch_prospect_profile, fetch_recent_events
from tracker import already_sent, record_sent, upsert_prospect, get_prospect
from sequences import render_sms, render_email
from sms_sender import send_sms
from email_sender import send_email
from cheat_sheet import generate_cheat_sheet
from exclusions import is_excluded, refresh_active_apps
from name_resolver import resolve_greeting


def _enrich_greeting(profile):
    """Add resolved greeting fields to a profile dict."""
    name = profile.get("name", "")
    app_name = profile.get("app_name", "")
    greeting, is_personal = resolve_greeting(name, app_name)
    profile["greeting_name"] = greeting
    profile["is_personal_name"] = is_personal
    # For templates: first_name is the greeting, name stays as full name
    profile["first_name"] = greeting
    return profile


def process_signup(signup):
    """Process a new sign-up: save prospect and send welcome sequence."""
    app_id = signup["application_id"]
    name = signup.get("name", "")
    email = signup.get("email", "")

    # Build full profile
    profile = fetch_prospect_profile(app_id)
    profile["name"] = name or profile.get("app_name", "Coach")
    profile["email"] = email or profile.get("email", "")

    # Check exclusions
    excluded, reason = is_excluded(app_id, email, profile.get("app_name"))
    if excluded:
        print(f"[EXCLUDED] {name} ({email}) app_id={app_id} — {reason}")
        return

    # Resolve greeting name
    profile = _enrich_greeting(profile)
    phone = profile.get("phone")

    # Save to local tracker
    upsert_prospect(
        application_id=app_id,
        name=profile.get("name"),
        email=profile.get("email"),
        phone=phone,
        coach_type=profile.get("coach_type"),
        country=profile.get("country"),
        signup_date=str(signup.get("signup_date", "")),
        profile_json=json.dumps(profile, default=str),
    )

    # Welcome email
    if email and not already_sent(app_id, "welcome", "email"):
        subject, body = render_email("welcome", profile)
        msg_id = send_email(email, subject, body)
        record_sent(app_id, "welcome", "email", email, msg_id)

    # Welcome SMS (if phone available)
    if phone and not already_sent(app_id, "welcome", "sms"):
        sms_body = render_sms("welcome", profile)
        msg_id = send_sms(phone, sms_body)
        record_sent(app_id, "welcome", "sms", phone, msg_id)

    print(
        f"[SIGNUP] Processed: {name} → greeting='{profile['greeting_name']}' ({email}) phone={phone or 'N/A'} app_id={app_id}"
    )


def process_event(event):
    """Process an activation event and trigger the appropriate sequence step."""
    app_id = event["application_id"]
    event_name = event["event_name"]

    step = SEQUENCE_TRIGGERS.get(event_name)
    if not step:
        return

    # Get or build prospect profile
    prospect = get_prospect(app_id)
    if not prospect:
        profile = fetch_prospect_profile(app_id)
        upsert_prospect(
            application_id=app_id,
            name=profile.get("app_name"),
            email=profile.get("email"),
            coach_type=profile.get("coach_type"),
            country=profile.get("country"),
            profile_json=json.dumps(profile, default=str),
        )
        prospect = get_prospect(app_id)

    if not prospect:
        print(f"[SKIP] No prospect data for app_id={app_id}")
        return

    # Merge profile_json back in for template rendering
    if prospect.get("profile_json"):
        try:
            full = json.loads(prospect["profile_json"])
            prospect.update(full)
        except (json.JSONDecodeError, TypeError):
            pass

    # Check exclusions
    excluded, reason = is_excluded(
        app_id, prospect.get("email"), prospect.get("app_name")
    )
    if excluded:
        print(f"[EXCLUDED] app_id={app_id} — {reason}")
        return

    # Resolve greeting name
    prospect = _enrich_greeting(prospect)

    email = prospect.get("email")
    phone = prospect.get("phone")

    # ── Profile uploaded → SMS + cheat sheet email ──
    if step == "profile_uploaded":
        # SMS 1: noticed your profile
        if phone and not already_sent(app_id, "profile_uploaded", "sms"):
            body = render_sms("profile_uploaded", prospect)
            msg_id = send_sms(phone, body)
            record_sent(app_id, "profile_uploaded", "sms", phone, msg_id)

        # Email: cheat sheet
        if email and not already_sent(app_id, "cheat_sheet", "email"):
            pdf_path = generate_cheat_sheet(prospect)
            subject, html_body = render_email("cheat_sheet", prospect)
            msg_id = send_email(email, subject, html_body, attachment_path=pdf_path)
            record_sent(app_id, "cheat_sheet", "email", email, msg_id)

        # SMS 2: white-glove CTA (slight delay in production)
        if phone and not already_sent(app_id, "profile_uploaded_cta", "sms"):
            body = render_sms("profile_uploaded_cta", prospect)
            msg_id = send_sms(phone, body)
            record_sent(app_id, "profile_uploaded_cta", "sms", phone, msg_id)

    # ── First module created → encouragement ──
    elif step == "first_module":
        if phone and not already_sent(app_id, "first_module", "sms"):
            body = render_sms("first_module", prospect)
            msg_id = send_sms(phone, body)
            record_sent(app_id, "first_module", "sms", phone, msg_id)

    # ── Coach type set → update profile ──
    elif step == "coach_type_set":
        try:
            data = json.loads(event.get("data", "{}"))
            coach_type = data.get("coach_type")
            country = data.get("country")
            if coach_type:
                upsert_prospect(app_id, coach_type=coach_type, country=country)
        except (json.JSONDecodeError, TypeError):
            pass

    print(f"[EVENT] {event_name} → step={step} for app_id={app_id}")


def run_once():
    """Single poll cycle: check for new sign-ups and events."""
    print(f"\n{'='*60}")
    print(
        f"[POLL] {datetime.now(timezone.utc).isoformat()} — checking for new activity..."
    )
    print(f"{'='*60}")

    # Refresh exclusion list each cycle
    refresh_active_apps()

    # 1. New sign-ups (last 24h to catch any we missed)
    signups = fetch_new_signups(since_hours=24)
    for s in signups:
        if not already_sent(s["application_id"], "welcome", "email"):
            process_signup(s)

    # 2. Recent activation events (last hour)
    events = fetch_recent_events(since_hours=1)
    for e in events:
        process_event(e)

    print(f"[DONE] Processed {len(signups)} sign-ups, {len(events)} events")


def run_loop():
    """Continuous polling loop."""
    print(f"KLIQ Prospect Outreach Engine")
    print(f"DRY_RUN={DRY_RUN} | Poll interval={POLL_INTERVAL_MINUTES}min")
    print(f"{'='*60}")

    while True:
        try:
            run_once()
        except Exception as e:
            print(f"[ERROR] {e}")

        print(f"[SLEEP] Next poll in {POLL_INTERVAL_MINUTES} minutes...")
        time.sleep(POLL_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    import sys

    if "--once" in sys.argv:
        run_once()
    else:
        run_loop()
