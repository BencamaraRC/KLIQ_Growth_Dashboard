"""
Autopilot Scheduler — runs in a background thread inside the Dash app.

Automated outreach rules:
  1. SMS for new sign-ups    → 12 hours after signup
  2. SMS for FB leads        → 12 hours after lead comes in
  3. Email for new sign-ups  → 36 hours after signup

Runs every POLL_MINUTES (default 15), checks time thresholds, and sends
messages that haven't already been recorded in the tracker DB.
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timezone, timedelta

import pandas as pd

from config import DRY_RUN
from tracker import (
    get_all_prospects,
    get_prospect,
    upsert_prospect,
    already_sent,
    record_sent,
    get_fb_leads,
    fb_already_sent,
    record_fb_sent,
)
from data_pipeline import (
    fetch_new_signups,
    fetch_prospect_profile,
    fetch_all_phones,
)
from sequences import render_sms, render_email
from email_sender import send_email
from sms_sender import send_sms
from gsheet_leads import sync_sheet_leads
from dedup_guard import sms_already_delivered, email_already_delivered
from exclusions import is_excluded
from calendly_tracker import (
    sync_calendly_bookings,
    is_configured as _calendly_configured,
)

log = logging.getLogger("autopilot")
log.setLevel(logging.INFO)
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(
        logging.Formatter(
            "[%(asctime)s] AUTOPILOT %(levelname)s  %(message)s", "%H:%M:%S"
        )
    )
    log.addHandler(_h)

# ── Settings ──
POLL_MINUTES = int(os.getenv("AUTOPILOT_POLL_MINUTES", "15"))
SIGNUP_SMS_DELAY_H = 12  # SMS sent 12h after signup
SIGNUP_SMS_MAX_H = 168  # Never SMS coaches older than 168h (7 days)
SIGNUP_EMAIL_DELAY_H = 36  # Email sent 36h after signup
FB_SMS_DELAY_H = 12  # FB lead SMS sent 12h after lead_date
FB_SMS_MAX_H = 168  # Never SMS FB leads older than 168h (7 days)
LOOKBACK_HOURS = 720  # Sync window: 30 days

# ── Run log (in-memory, exposed to Outreach UI) ──
_run_log: list[dict] = []
_MAX_LOG = 200


def get_run_log() -> list[dict]:
    """Return most recent autopilot run entries (newest first)."""
    return list(reversed(_run_log[-_MAX_LOG:]))


def _log_entry(action: str, detail: str, success: bool = True):
    _run_log.append(
        {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "action": action,
            "detail": detail,
            "ok": success,
        }
    )
    if len(_run_log) > _MAX_LOG:
        _run_log.pop(0)


# ═════════════════════════════════════════════════════════════
#  RULE 1: SMS for new sign-ups — 12h after signup
# ═════════════════════════════════════════════════════════════
def _run_signup_sms():
    """Send welcome SMS to prospects who signed up 12–168h ago and have a phone."""
    now = datetime.now(timezone.utc)
    min_cutoff = now - timedelta(hours=SIGNUP_SMS_DELAY_H)  # must be 12h+ old
    max_cutoff = now - timedelta(hours=SIGNUP_SMS_MAX_H)  # must be within 168h
    sent = 0

    try:
        phones = fetch_all_phones()
    except Exception as e:
        _log_entry("signup_sms", f"BQ fetch_all_phones failed: {e}", False)
        return 0

    for p in phones:
        phone = p.get("phone_number", "")
        if not phone:
            continue
        created = p.get("created_at")
        if not created:
            continue
        try:
            dt = pd.to_datetime(created, utc=True)
        except Exception:
            continue
        if dt > min_cutoff:
            continue  # Too recent — not 12h yet
        if dt < max_cutoff:
            continue  # Too old — past 168h window

        app_id = p.get("application_id")
        if not app_id:
            continue

        # Exclusion check — skip internal, test, and paying accounts
        email = p.get("email", "")
        app_name = p.get("application_name", "")
        excluded, reason = is_excluded(app_id, email, app_name)
        if excluded:
            log.debug(f"Excluded from signup SMS: {app_name} ({email}) — {reason}")
            continue

        # Already sent? (local DB)
        if already_sent(app_id, "welcome", "sms"):
            continue

        # Already sent? (Twilio API — survives DB resets)
        if sms_already_delivered(phone):
            log.debug(f"Twilio dedup: skip SMS to {phone} (app={app_id})")
            record_sent(app_id, "welcome", "sms", phone, "dedup_twilio")
            continue

        # Build context
        name = p.get("application_name") or "Coach"
        first_name = name.split()[0] if name else "Coach"
        ctx = {"first_name": first_name, "name": name}

        if DRY_RUN:
            log.info(f"[DRY] Would SMS {phone} (signup_sms, app={app_id})")
            _log_entry("signup_sms", f"[DRY] {phone} app={app_id}")
            continue

        try:
            body = render_sms("welcome", ctx)
            msg_id = send_sms(phone, body)
            if msg_id:
                record_sent(app_id, "welcome", "sms", phone, msg_id)
                sent += 1
                log.info(f"✅ Signup SMS → {phone} (app={app_id})")
                _log_entry("signup_sms", f"Sent to {phone} app={app_id}")
            else:
                _log_entry("signup_sms", f"send_sms returned None for {phone}", False)
        except Exception as e:
            _log_entry("signup_sms", f"Error sending to {phone}: {e}", False)

    return sent


# ═════════════════════════════════════════════════════════════
#  RULE 2: SMS for FB leads — 12h after lead_date
# ═════════════════════════════════════════════════════════════
def _run_fb_sms():
    """Send SMS to FB leads 12–168h after their lead_date."""
    now = datetime.now(timezone.utc)
    min_cutoff = now - timedelta(hours=FB_SMS_DELAY_H)  # must be 12h+ old
    max_cutoff = now - timedelta(hours=FB_SMS_MAX_H)  # must be within 168h
    sent = 0

    for campaign in ("fb_reengagement", "fb_new_lead"):
        try:
            leads = get_fb_leads(campaign=campaign)
        except Exception as e:
            _log_entry("fb_sms", f"get_fb_leads({campaign}) failed: {e}", False)
            continue

        for lead in leads:
            phone = lead.get("phone", "")
            if not phone:
                continue
            email = lead.get("email", "")
            if not email:
                continue

            # Check time window: 12h–168h after lead_date
            ld = lead.get("lead_date")
            if ld and ld not in ("None", ""):
                try:
                    lead_dt = pd.to_datetime(ld, utc=True)
                    if lead_dt > min_cutoff:
                        continue  # Not 12h yet
                    if lead_dt < max_cutoff:
                        continue  # Too old — past 168h window
                except Exception:
                    pass
            else:
                continue  # No lead_date — skip, don't SMS without knowing age

            if fb_already_sent(email, campaign, "sms"):
                continue

            # Already sent? (Twilio API — survives DB resets)
            if sms_already_delivered(phone):
                log.debug(f"Twilio dedup: skip FB SMS to {phone}")
                record_fb_sent(email, campaign, "sms", phone, "dedup_twilio")
                continue

            first_name = lead.get("first_name") or "Coach"
            ctx = {"first_name": first_name, "name": first_name}

            if DRY_RUN:
                log.info(f"[DRY] Would SMS {phone} (fb_sms, {campaign})")
                _log_entry("fb_sms", f"[DRY] {phone} {campaign}")
                continue

            try:
                body = render_sms(campaign, ctx)
                msg_id = send_sms(phone, body)
                if msg_id:
                    record_fb_sent(email, campaign, "sms", phone, msg_id)
                    sent += 1
                    log.info(f"✅ FB SMS → {phone} ({campaign})")
                    _log_entry("fb_sms", f"Sent to {phone} ({campaign})")
                else:
                    _log_entry("fb_sms", f"send_sms returned None for {phone}", False)
            except Exception as e:
                _log_entry("fb_sms", f"Error {phone} ({campaign}): {e}", False)

    return sent


# ═════════════════════════════════════════════════════════════
#  RULE 2b: Email for FB leads — 12h after lead_date
# ═════════════════════════════════════════════════════════════
def _run_fb_email():
    """Send email to FB leads 12+ hours after their lead_date."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=FB_SMS_DELAY_H)  # Same 12h rule
    sent = 0

    for campaign in ("fb_reengagement", "fb_new_lead"):
        try:
            leads = get_fb_leads(campaign=campaign)
        except Exception as e:
            _log_entry("fb_email", f"get_fb_leads({campaign}) failed: {e}", False)
            continue

        for lead in leads:
            email = lead.get("email", "")
            if not email:
                continue

            ld = lead.get("lead_date")
            if ld and ld not in ("None", ""):
                try:
                    if pd.to_datetime(ld, utc=True) > cutoff:
                        continue
                except Exception:
                    pass

            if fb_already_sent(email, campaign, "email"):
                continue

            # Already sent? (Brevo API — survives DB resets)
            if email_already_delivered(email):
                log.debug(f"Brevo dedup: skip FB email to {email}")
                record_fb_sent(email, campaign, "email", email, "dedup_brevo")
                continue

            first_name = lead.get("first_name") or "Coach"
            ctx = {"first_name": first_name, "name": first_name}

            if DRY_RUN:
                log.info(f"[DRY] Would email {email} (fb_email, {campaign})")
                _log_entry("fb_email", f"[DRY] {email} {campaign}")
                continue

            try:
                subject, body = render_email(campaign, ctx)
                msg_id = send_email(email, subject, body)
                if msg_id:
                    record_fb_sent(email, campaign, "email", email, msg_id)
                    sent += 1
                    log.info(f"✅ FB Email → {email} ({campaign})")
                    _log_entry("fb_email", f"Sent to {email} ({campaign})")
                else:
                    _log_entry(
                        "fb_email", f"send_email returned None for {email}", False
                    )
            except Exception as e:
                _log_entry("fb_email", f"Error {email} ({campaign}): {e}", False)

    return sent


# ═════════════════════════════════════════════════════════════
#  RULE 3: Email for new sign-ups — 36h after signup
# ═════════════════════════════════════════════════════════════
def _run_signup_email():
    """Send welcome email to prospects who signed up 36+ hours ago."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=SIGNUP_EMAIL_DELAY_H)
    sent = 0

    prospects = get_all_prospects()
    for p in prospects:
        email = p.get("email", "")
        if not email:
            continue
        app_id = p.get("application_id")
        if not app_id:
            continue

        # Check signup time
        sd = p.get("signup_date")
        if not sd or sd in ("None", ""):
            continue
        try:
            dt = pd.to_datetime(sd, utc=True)
        except Exception:
            continue
        if dt > cutoff:
            continue  # Not 36h yet

        # Already sent welcome email? (local DB)
        if already_sent(app_id, "welcome", "email"):
            continue

        # Already sent? (Brevo API — survives DB resets)
        if email_already_delivered(email):
            log.debug(f"Brevo dedup: skip signup email to {email} (app={app_id})")
            record_sent(app_id, "welcome", "email", email, "dedup_brevo")
            continue

        # Build context from profile_json or basic fields
        enriched = dict(p)
        if enriched.get("profile_json"):
            try:
                enriched.update(json.loads(enriched["profile_json"]))
            except (json.JSONDecodeError, TypeError):
                pass

        name = enriched.get("name") or "Coach"
        enriched.setdefault("first_name", name.split()[0] if name else "Coach")

        if DRY_RUN:
            log.info(f"[DRY] Would email {email} (signup_email, app={app_id})")
            _log_entry("signup_email", f"[DRY] {email} app={app_id}")
            continue

        try:
            subject, body = render_email("welcome", enriched)
            msg_id = send_email(email, subject, body)
            if msg_id:
                record_sent(app_id, "welcome", "email", email, msg_id)
                sent += 1
                log.info(f"✅ Signup Email → {email} (app={app_id})")
                _log_entry("signup_email", f"Sent to {email} app={app_id}")
            else:
                _log_entry(
                    "signup_email", f"send_email returned None for {email}", False
                )
        except Exception as e:
            _log_entry("signup_email", f"Error {email}: {e}", False)

    return sent


# ═════════════════════════════════════════════════════════════
#  AUTO-SYNC: pull recent sign-ups so they're in the DB
# ═════════════════════════════════════════════════════════════
def _auto_sync():
    """Pull last N hours of sign-ups from BigQuery and upsert into prospect DB."""
    try:
        signups = fetch_new_signups(since_hours=LOOKBACK_HOURS)
    except Exception as e:
        _log_entry("auto_sync", f"fetch_new_signups failed: {e}", False)
        return 0

    synced = 0
    for s in signups:
        app_id = s.get("application_id")
        if not app_id:
            continue
        try:
            profile = fetch_prospect_profile(app_id)
            profile["name"] = s.get("name") or profile.get("app_name", "Coach")
            profile["email"] = s.get("email") or profile.get("email", "")
            upsert_prospect(
                application_id=app_id,
                name=profile.get("name"),
                email=profile.get("email"),
                phone=profile.get("phone"),
                coach_type=profile.get("coach_type"),
                country=profile.get("country"),
                signup_date=str(s.get("signup_date", "")),
                profile_json=json.dumps(profile, default=str),
            )
            synced += 1
        except Exception as e:
            _log_entry("auto_sync", f"Error syncing app={app_id}: {e}", False)

    return synced


# ═════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═════════════════════════════════════════════════════════════
_thread: threading.Thread | None = None
_running = False


def _loop():
    """Main autopilot loop — runs forever in a background thread."""
    global _running
    log.info(f"Autopilot started (poll every {POLL_MINUTES}m, DRY_RUN={DRY_RUN})")
    _log_entry(
        "system", f"Autopilot started — poll every {POLL_MINUTES}m, DRY_RUN={DRY_RUN}"
    )

    while _running:
        cycle_start = time.time()
        log.info("─── Autopilot cycle start ───")
        _log_entry("cycle", "Cycle started")

        gsheet_new = 0
        try:
            # 0. Sync FB leads from Google Sheet
            try:
                gsheet_new = sync_sheet_leads()
                if gsheet_new:
                    log.info(f"GSheet sync: {gsheet_new} new FB leads")
                _log_entry("gsheet_sync", f"Synced from GSheet ({gsheet_new} new)")
            except Exception as e:
                _log_entry("gsheet_sync", f"GSheet sync failed: {e}", False)

            # 1. Auto-sync prospects from BigQuery
            synced = _auto_sync()
            _log_entry("auto_sync", f"Synced {synced} prospects")

            # 2. Signup SMS (12h)
            sms1 = _run_signup_sms()
            _log_entry("signup_sms", f"Sent {sms1} signup SMS")

            # 3. FB SMS (12h)
            sms2 = _run_fb_sms()
            _log_entry("fb_sms", f"Sent {sms2} FB SMS")

            # 4. FB Email (12h)
            em1 = _run_fb_email()
            _log_entry("fb_email", f"Sent {em1} FB emails")

            # 5. Signup Email (36h)
            em2 = _run_signup_email()
            _log_entry("signup_email", f"Sent {em2} signup emails")

            # 6. Sync Calendly bookings (conversion tracking)
            cal_new = 0
            if _calendly_configured():
                try:
                    cal_new = sync_calendly_bookings(lookback_days=30)
                    _log_entry(
                        "calendly_sync", f"Synced Calendly ({cal_new} new bookings)"
                    )
                except Exception as e:
                    _log_entry("calendly_sync", f"Calendly sync failed: {e}", False)

            total = sms1 + sms2 + em1 + em2
            log.info(
                f"─── Cycle done: {total} msgs sent, {synced} synced, {gsheet_new} GSheet, {cal_new} Calendly ───"
            )
            _log_entry(
                "cycle",
                f"Cycle done: {total} msgs, {synced} BQ, {gsheet_new} GSheet, {cal_new} Calendly",
            )

        except Exception as e:
            log.exception(f"Autopilot cycle error: {e}")
            _log_entry("cycle", f"Cycle error: {e}", False)

        # Sleep in 10s chunks so we can stop quickly
        elapsed = time.time() - cycle_start
        remaining = max(0, POLL_MINUTES * 60 - elapsed)
        sleep_end = time.time() + remaining
        while _running and time.time() < sleep_end:
            time.sleep(10)


def start():
    """Start the autopilot background thread (idempotent)."""
    global _thread, _running
    if _running and _thread and _thread.is_alive():
        log.info("Autopilot already running")
        return
    _running = True
    _thread = threading.Thread(target=_loop, daemon=True, name="autopilot")
    _thread.start()


def stop():
    """Signal the autopilot to stop (it will finish the current sleep chunk)."""
    global _running
    _running = False
    log.info("Autopilot stop requested")
    _log_entry("system", "Autopilot stopped")


def is_running() -> bool:
    return _running and _thread is not None and _thread.is_alive()
