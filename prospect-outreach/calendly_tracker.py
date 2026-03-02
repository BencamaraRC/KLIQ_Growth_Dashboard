"""
Calendly Booking Tracker — polls the Calendly API v2 for scheduled events
and matches invitee emails against sent outreach messages to compute
conversion rates.

Requires CALENDLY_API_TOKEN env var (Personal Access Token).
"""

import sqlite3
import requests
from datetime import datetime, timezone, timedelta

from config import CALENDLY_API_TOKEN, CALENDLY_EVENT_SLUGS, DB_PATH

BASE_URL = "https://api.calendly.com"
_HEADERS = {}


def _ensure_headers():
    global _HEADERS
    if not _HEADERS and CALENDLY_API_TOKEN:
        _HEADERS = {
            "Authorization": f"Bearer {CALENDLY_API_TOKEN}",
            "Content-Type": "application/json",
        }
    return bool(_HEADERS)


def is_configured() -> bool:
    """Return True if the Calendly API token is set."""
    return bool(CALENDLY_API_TOKEN)


# ── Calendly API helpers ──


def _get_current_user():
    """Get the current user's URI and organization URI."""
    if not _ensure_headers():
        return None, None
    resp = requests.get(f"{BASE_URL}/users/me", headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()["resource"]
    return data["uri"], data["current_organization"]


def _get_org_uri():
    """Get the organization URI (cached after first call)."""
    if not hasattr(_get_org_uri, "_cache"):
        _, org = _get_current_user()
        _get_org_uri._cache = org
    return _get_org_uri._cache


def fetch_scheduled_events(min_start_time=None, max_start_time=None, status="active"):
    """
    Fetch scheduled events from Calendly for the organization.
    Returns list of event dicts.
    """
    if not _ensure_headers():
        return []

    org_uri = _get_org_uri()
    if not org_uri:
        return []

    params = {
        "organization": org_uri,
        "status": status,
        "count": 100,
    }
    if min_start_time:
        params["min_start_time"] = min_start_time
    if max_start_time:
        params["max_start_time"] = max_start_time

    all_events = []
    url = f"{BASE_URL}/scheduled_events"

    while url:
        resp = requests.get(url, headers=_HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        all_events.extend(data.get("collection", []))
        # Pagination
        next_page = data.get("pagination", {}).get("next_page_token")
        if next_page:
            params["page_token"] = next_page
        else:
            url = None
        # Only set params on first request
        if url:
            params = {"page_token": next_page} if next_page else {}
            url = f"{BASE_URL}/scheduled_events" if next_page else None

    return all_events


def fetch_event_invitees(event_uri):
    """Fetch invitees for a specific event. Returns list of invitee dicts."""
    if not _ensure_headers():
        return []

    # event_uri is like https://api.calendly.com/scheduled_events/UUID
    url = f"{event_uri}/invitees"
    all_invitees = []

    while url:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        all_invitees.extend(data.get("collection", []))
        next_page = data.get("pagination", {}).get("next_page_token")
        url = f"{event_uri}/invitees?page_token={next_page}" if next_page else None

    return all_invitees


def _get_event_type_slug(event):
    """Extract the event type slug from the event_type URI."""
    # event_type is like https://api.calendly.com/event_types/UUID
    # We need the actual slug from the event name or by querying the type
    # For matching, we use the event name which contains our identifiable text
    name = event.get("name", "").lower()
    if "shortlist" in name or "partner" in name:
        return "kliq-pp-shortlist"
    elif "concierge" in name or "demo" in name or "15min" in name:
        return "kliq-demo-call-15mins-clone"
    # Fallback: try to extract from event_type URI
    return "unknown"


# ── Database operations ──


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS calendly_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_uri TEXT UNIQUE NOT NULL,
            event_type_slug TEXT,
            invitee_email TEXT NOT NULL,
            invitee_name TEXT,
            event_start TEXT,
            event_status TEXT DEFAULT 'active',
            created_at TEXT,
            matched_campaign TEXT,
            matched_channel TEXT,
            converted_to_sale INTEGER DEFAULT 0,
            converted_at TEXT,
            call_status TEXT DEFAULT 'Booked'
        )
    """
    )
    # Migrate: add columns if table already exists without them
    try:
        conn.execute(
            "ALTER TABLE calendly_bookings ADD COLUMN converted_to_sale INTEGER DEFAULT 0"
        )
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE calendly_bookings ADD COLUMN converted_at TEXT")
    except Exception:
        pass
    try:
        conn.execute(
            "ALTER TABLE calendly_bookings ADD COLUMN call_status TEXT DEFAULT 'Booked'"
        )
    except Exception:
        pass
    conn.commit()
    return conn


def upsert_booking(
    event_uri,
    event_type_slug,
    invitee_email,
    invitee_name,
    event_start,
    event_status="active",
):
    """Insert or update a Calendly booking."""
    conn = _get_db()

    # Try to match this invitee to a sent message
    matched_campaign, matched_channel = _match_to_sent_message(conn, invitee_email)

    conn.execute(
        """INSERT INTO calendly_bookings
           (event_uri, event_type_slug, invitee_email, invitee_name, event_start,
            event_status, created_at, matched_campaign, matched_channel)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(event_uri) DO UPDATE SET
               event_status = excluded.event_status,
               matched_campaign = COALESCE(excluded.matched_campaign, calendly_bookings.matched_campaign),
               matched_channel = COALESCE(excluded.matched_channel, calendly_bookings.matched_channel)
        """,
        (
            event_uri,
            event_type_slug,
            invitee_email.lower(),
            invitee_name,
            event_start,
            event_status,
            datetime.now(timezone.utc).isoformat(),
            matched_campaign,
            matched_channel,
        ),
    )
    conn.commit()
    conn.close()


def _match_to_sent_message(conn, email):
    """Try to match a booking invitee email to a sent outreach message."""
    email_lower = email.lower()

    # Check sent_messages for this email
    row = conn.execute(
        "SELECT sequence_step, channel FROM sent_messages WHERE LOWER(recipient) = ? ORDER BY sent_at DESC LIMIT 1",
        (email_lower,),
    ).fetchone()

    if row:
        return row[0], row[1]

    # Check FB leads
    row = conn.execute(
        "SELECT campaign FROM fb_leads WHERE LOWER(email) = ? LIMIT 1",
        (email_lower,),
    ).fetchone()
    if row:
        return row[0], "fb_lead"

    # Check prospects
    row = conn.execute(
        "SELECT 'signup' FROM prospects WHERE LOWER(email) = ? LIMIT 1",
        (email_lower,),
    ).fetchone()
    if row:
        return "signup", "organic"

    return None, None


def get_all_bookings():
    """Get all tracked Calendly bookings."""
    conn = _get_db()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM calendly_bookings ORDER BY event_start DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_converted(booking_id, converted=True):
    """Mark a booking as converted to sale (or unmark)."""
    conn = _get_db()
    converted_at = datetime.now(timezone.utc).isoformat() if converted else None
    conn.execute(
        "UPDATE calendly_bookings SET converted_to_sale = ?, converted_at = ? WHERE id = ?",
        (1 if converted else 0, converted_at, booking_id),
    )
    conn.commit()
    conn.close()
    return True


def update_call_status(booking_id, status):
    """Update the call status for a booking."""
    conn = _get_db()
    conn.execute(
        "UPDATE calendly_bookings SET call_status = ? WHERE id = ?",
        (status, booking_id),
    )
    conn.commit()
    conn.close()
    return True


def get_booking_stats():
    """
    Compute conversion stats:
    - Total bookings
    - Bookings matched to outreach (by campaign)
    - Bookings NOT matched (organic / other sources)
    - Conversion rates (bookings / messages sent per campaign)
    - Breakdown by event type with matched vs unmatched
    """
    conn = _get_db()
    conn.row_factory = sqlite3.Row

    # Total bookings
    total = conn.execute(
        "SELECT COUNT(*) as cnt FROM calendly_bookings WHERE event_status = 'active'"
    ).fetchone()["cnt"]

    # Matched vs unmatched totals
    matched_total = conn.execute(
        "SELECT COUNT(*) as cnt FROM calendly_bookings WHERE event_status = 'active' AND matched_campaign IS NOT NULL"
    ).fetchone()["cnt"]
    unmatched_total = total - matched_total

    # Bookings by event type (with matched / unmatched split)
    by_type = conn.execute(
        """SELECT event_type_slug,
                  COUNT(*) as cnt,
                  SUM(CASE WHEN matched_campaign IS NOT NULL THEN 1 ELSE 0 END) as matched,
                  SUM(CASE WHEN matched_campaign IS NULL THEN 1 ELSE 0 END) as unmatched
           FROM calendly_bookings WHERE event_status = 'active'
           GROUP BY event_type_slug"""
    ).fetchall()

    # Bookings matched to campaigns
    by_campaign = conn.execute(
        """SELECT matched_campaign, COUNT(*) as cnt
           FROM calendly_bookings
           WHERE event_status = 'active' AND matched_campaign IS NOT NULL
           GROUP BY matched_campaign"""
    ).fetchall()

    # Total messages sent per campaign
    msgs_by_campaign = conn.execute(
        """SELECT sequence_step, COUNT(*) as cnt
           FROM sent_messages
           GROUP BY sequence_step"""
    ).fetchall()

    # Unique recipients per campaign
    unique_recipients = conn.execute(
        """SELECT sequence_step, COUNT(DISTINCT LOWER(recipient)) as cnt
           FROM sent_messages
           GROUP BY sequence_step"""
    ).fetchall()

    # Total unique outreach recipients (across all campaigns)
    total_unique_outreach = conn.execute(
        "SELECT COUNT(DISTINCT LOWER(recipient)) as cnt FROM sent_messages"
    ).fetchone()["cnt"]

    msgs_map = {r["sequence_step"]: r["cnt"] for r in msgs_by_campaign}
    unique_map = {r["sequence_step"]: r["cnt"] for r in unique_recipients}
    bookings_map = {r["matched_campaign"]: r["cnt"] for r in by_campaign}

    # Build conversion rates
    conversions = []
    for campaign, booked in bookings_map.items():
        sent = unique_map.get(campaign, 0)
        rate = (booked / sent * 100) if sent > 0 else 0
        conversions.append(
            {
                "campaign": campaign,
                "booked": booked,
                "unique_sent": sent,
                "total_sent": msgs_map.get(campaign, 0),
                "conversion_rate": round(rate, 1),
            }
        )

    # Overall outreach conversion: matched bookings / total unique outreach recipients
    outreach_conversion_rate = round(
        (
            (matched_total / total_unique_outreach * 100)
            if total_unique_outreach > 0
            else 0
        ),
        1,
    )

    # Sale conversions
    total_sales = conn.execute(
        "SELECT COUNT(*) as cnt FROM calendly_bookings WHERE event_status = 'active' AND converted_to_sale = 1"
    ).fetchone()["cnt"]
    booking_to_sale_rate = round((total_sales / total * 100) if total > 0 else 0, 1)
    outreach_to_sale_rate = round(
        (total_sales / total_unique_outreach * 100) if total_unique_outreach > 0 else 0,
        1,
    )

    conn.close()

    return {
        "total_bookings": total,
        "matched_total": matched_total,
        "unmatched_total": unmatched_total,
        "total_unique_outreach": total_unique_outreach,
        "outreach_conversion_rate": outreach_conversion_rate,
        "by_event_type": [dict(r) for r in by_type],
        "conversions": conversions,
        "total_sales": total_sales,
        "booking_to_sale_rate": booking_to_sale_rate,
        "outreach_to_sale_rate": outreach_to_sale_rate,
    }


# ── Main sync function ──


def sync_calendly_bookings(lookback_days=30):
    """
    Pull recent Calendly events and their invitees, upsert into local DB.
    Returns number of new bookings found.
    """
    if not is_configured():
        return 0

    now = datetime.now(timezone.utc)
    min_start = (now - timedelta(days=lookback_days)).strftime(
        "%Y-%m-%dT%H:%M:%S.000000Z"
    )

    events = fetch_scheduled_events(min_start_time=min_start)
    new_count = 0

    for event in events:
        event_uri = event.get("uri", "")
        event_start = event.get("start_time", "")
        event_status = event.get("status", "active")
        slug = _get_event_type_slug(event)

        # Get invitees for this event
        try:
            invitees = fetch_event_invitees(event_uri)
        except Exception:
            continue

        for inv in invitees:
            email = inv.get("email", "")
            name = inv.get("name", "")
            if not email:
                continue

            # Check if we already have this booking
            conn = _get_db()
            existing = conn.execute(
                "SELECT 1 FROM calendly_bookings WHERE event_uri = ?",
                (event_uri,),
            ).fetchone()
            conn.close()

            upsert_booking(
                event_uri=event_uri,
                event_type_slug=slug,
                invitee_email=email,
                invitee_name=name,
                event_start=event_start,
                event_status=event_status,
            )

            if not existing:
                new_count += 1

    return new_count
