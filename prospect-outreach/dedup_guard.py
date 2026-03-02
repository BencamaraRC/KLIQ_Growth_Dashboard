"""
Dedup Guard — checks Twilio and Brevo APIs to verify whether an SMS or email
has already been sent to a given recipient, preventing duplicate outreach even
if the local SQLite DB is lost (e.g. Cloud Run container restarts).

Usage:
    from dedup_guard import sms_already_delivered, email_already_delivered

    if sms_already_delivered("+14155551234"):
        skip …

    if email_already_delivered("user@example.com"):
        skip …
"""

import re
import time
import logging
from datetime import datetime, timezone, timedelta
from functools import lru_cache

import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    BREVO_API_KEY,
    BREVO_FROM_EMAIL,
)
from email_sender import OUTREACH_TAG

log = logging.getLogger("dedup_guard")

# ── In-memory caches (survive within a single container lifetime) ──
# These avoid hammering the APIs on every single prospect.
_sms_cache: dict[str, bool] = {}  # phone → True if already sent
_email_cache: dict[str, bool] = {}  # email → True if already sent
_CACHE_TTL_S = 900  # 15 min — matches autopilot poll

# Track API auth failures to avoid flooding logs
_twilio_auth_failed = False
_brevo_auth_failed = False

# Track when caches were last fully cleared
_cache_born = time.time()


def _maybe_clear_caches():
    """Clear caches if they're older than TTL."""
    global _sms_cache, _email_cache, _cache_born
    if time.time() - _cache_born > _CACHE_TTL_S:
        _sms_cache.clear()
        _email_cache.clear()
        _cache_born = time.time()


# ═══════════════════════════════════════════════════════════════
#  TWILIO — check if SMS was already sent to a phone number
# ═══════════════════════════════════════════════════════════════


def _normalise_phone(phone: str) -> str:
    """Normalise to E.164-ish for consistent cache keys."""
    return re.sub(r"[^\d+]", "", phone.strip())


def sms_already_delivered(phone: str, lookback_days: int = 30) -> bool:
    """
    Check Twilio message logs for any outbound SMS to this phone number
    in the last `lookback_days` days.
    Returns True if at least one delivered/sent message is found.
    """
    _maybe_clear_caches()
    key = _normalise_phone(phone)
    if not key:
        return False

    # Check cache first
    if key in _sms_cache:
        return _sms_cache[key]

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return False  # Can't check — fail open (rely on SQLite)

    global _twilio_auth_failed
    if _twilio_auth_failed:
        return False  # Auth is broken — skip API calls until cache clears

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        after = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        messages = client.messages.list(
            to=key,
            date_sent_after=after,
            limit=5,
        )

        # Consider delivered, sent, or queued as "already sent"
        already = any(
            m.status in ("delivered", "sent", "queued", "accepted", "sending")
            for m in messages
        )
        _sms_cache[key] = already
        return already

    except TwilioRestException as e:
        if "401" in str(e) or "Authenticate" in str(e):
            if not _twilio_auth_failed:
                log.error(
                    f"Twilio auth failed — disabling dedup checks until restart: {e}"
                )
                _twilio_auth_failed = True
        else:
            log.warning(f"Twilio dedup check failed for {key}: {e}")
        return False  # Fail open
    except Exception as e:
        if "401" in str(e) or "Authenticate" in str(e):
            if not _twilio_auth_failed:
                log.error(
                    f"Twilio auth failed — disabling dedup checks until restart: {e}"
                )
                _twilio_auth_failed = True
        else:
            log.warning(f"Twilio dedup error for {key}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
#  BREVO — check if email was already sent to an address
# ═══════════════════════════════════════════════════════════════

_BREVO_EVENTS_URL = "https://api.brevo.com/v3/smtp/statistics/events"


def email_already_delivered(email: str, lookback_days: int = 30) -> bool:
    """
    Check Brevo transactional email events for any email sent to this
    address in the last `lookback_days` days.
    Returns True if at least one delivered/sent event is found.
    """
    _maybe_clear_caches()
    key = email.lower().strip()
    if not key or "@" not in key:
        return False

    if key in _email_cache:
        return _email_cache[key]

    if not BREVO_API_KEY:
        return False  # Can't check — fail open

    try:
        start_date = (
            datetime.now(timezone.utc) - timedelta(days=lookback_days)
        ).strftime("%Y-%m-%d")
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        resp = requests.get(
            _BREVO_EVENTS_URL,
            headers={
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
            },
            params={
                "email": key,
                "startDate": start_date,
                "endDate": end_date,
                "limit": 10,
                "event": "delivered",
                "tags": OUTREACH_TAG,
            },
            timeout=15,
        )

        if resp.status_code == 200:
            data = resp.json()
            events = data.get("events", [])
            already = len(events) > 0
            _email_cache[key] = already
            return already
        else:
            # Try broader check — any event (requests, delivered, etc.)
            resp2 = requests.get(
                _BREVO_EVENTS_URL,
                headers={
                    "accept": "application/json",
                    "api-key": BREVO_API_KEY,
                },
                params={
                    "email": key,
                    "startDate": start_date,
                    "endDate": end_date,
                    "limit": 10,
                    "tags": OUTREACH_TAG,
                },
                timeout=15,
            )
            if resp2.status_code == 200:
                events = resp2.json().get("events", [])
                already = len(events) > 0
                _email_cache[key] = already
                return already

        log.warning(f"Brevo dedup check failed for {key}: HTTP {resp.status_code}")
        return False

    except Exception as e:
        log.warning(f"Brevo dedup error for {key}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
#  Combined convenience check
# ═══════════════════════════════════════════════════════════════


def email_was_opened(email: str, lookback_days: int = 30) -> bool:
    """Check Brevo for any 'opened' event for this email address."""
    key = email.lower().strip()
    if not key or "@" not in key or not BREVO_API_KEY:
        return False
    try:
        start_date = (
            datetime.now(timezone.utc) - timedelta(days=lookback_days)
        ).strftime("%Y-%m-%d")
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        resp = requests.get(
            _BREVO_EVENTS_URL,
            headers={"accept": "application/json", "api-key": BREVO_API_KEY},
            params={
                "email": key,
                "startDate": start_date,
                "endDate": end_date,
                "limit": 5,
                "event": "opened",
                "tags": OUTREACH_TAG,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return len(resp.json().get("events", [])) > 0
    except Exception as e:
        log.warning(f"Brevo open check error for {key}: {e}")
    return False


def get_email_engagement(email: str, lookback_days: int = 30) -> dict:
    """Get full engagement info for an email: delivered, opened, clicked."""
    key = email.lower().strip()
    result = {
        "delivered": False,
        "opened": False,
        "clicked": False,
        "open_count": 0,
        "click_count": 0,
    }
    if not key or "@" not in key or not BREVO_API_KEY:
        return result
    try:
        start_date = (
            datetime.now(timezone.utc) - timedelta(days=lookback_days)
        ).strftime("%Y-%m-%d")
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        headers = {"accept": "application/json", "api-key": BREVO_API_KEY}
        for event_type in ("delivered", "opened", "clicks"):
            resp = requests.get(
                _BREVO_EVENTS_URL,
                headers=headers,
                params={
                    "email": key,
                    "startDate": start_date,
                    "endDate": end_date,
                    "limit": 50,
                    "event": event_type,
                    "tags": OUTREACH_TAG,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                events = resp.json().get("events", [])
                if event_type == "delivered":
                    result["delivered"] = len(events) > 0
                elif event_type == "opened":
                    result["opened"] = len(events) > 0
                    result["open_count"] = len(events)
                elif event_type == "clicks":
                    result["clicked"] = len(events) > 0
                    result["click_count"] = len(events)
    except Exception as e:
        log.warning(f"Brevo engagement check error for {key}: {e}")
    return result


def already_contacted(recipient: str, channel: str, lookback_days: int = 30) -> bool:
    """
    Unified check: has this recipient already been contacted via channel?
    channel: 'sms' or 'email'
    """
    if channel == "sms":
        return sms_already_delivered(recipient, lookback_days)
    elif channel == "email":
        return email_already_delivered(recipient, lookback_days)
    return False
