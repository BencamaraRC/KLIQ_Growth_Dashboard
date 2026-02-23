"""
Google Sheets integration for Facebook Lead Ads.
Reads leads from the shared Google Sheet and syncs them into the local SQLite tracker.
"""

import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import SERVICE_ACCOUNT_KEY
from tracker import upsert_fb_lead, get_fb_leads

# ── Sheet config ──
FB_LEADS_SHEET_ID = "1D6ScYyqAbuRZCdx6jrOoTDH-5WlwvcH5UzokGsVrx6s"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Column mappings per sheet (0-indexed positions from header row)
# Meta:  created_time(1), campaign_name(7), which_coaching_niche(12), email(13), first_name(14), phone(15), lead_status(17)
# Meta 2: created_time(1), campaign_name(7), which_coaching_niche(12), email(13), first_name(14), whatsapp_number(15), lead_status(16)


def _get_sheets_service():
    """Build Google Sheets API service using the project service account."""
    if not SERVICE_ACCOUNT_KEY:
        print("[GSHEET] No service account key configured")
        return None
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_KEY, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _clean_phone(raw_phone):
    """Normalise phone number: strip spaces, ensure + prefix."""
    if not raw_phone:
        return ""
    phone = re.sub(r"[^\d+]", "", str(raw_phone).strip())
    if not phone:
        return ""
    # If it starts with a country code but no +, add +
    if not phone.startswith("+"):
        # UK numbers starting with 44 or 07
        if phone.startswith("44") and len(phone) >= 11:
            phone = "+" + phone
        elif phone.startswith("07") and len(phone) >= 11:
            phone = "+44" + phone[1:]
        # US/CA numbers starting with 1
        elif phone.startswith("1") and len(phone) >= 11:
            phone = "+" + phone
        # Default: just add +
        elif len(phone) >= 10:
            phone = "+" + phone
    return phone


def _safe_get(row, idx, default=""):
    """Safely get a value from a row list by index."""
    try:
        return row[idx].strip() if idx < len(row) and row[idx] else default
    except (IndexError, AttributeError):
        return default


def fetch_sheet_leads():
    """
    Read leads from the 'Meta 2' sheet.
    Returns a list of dicts with: first_name, last_name, email, phone, campaign, lead_date, niche.
    """
    service = _get_sheets_service()
    if not service:
        return []

    all_leads = []

    try:
        # ── Meta 2 sheet (active leads) ──
        result = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=FB_LEADS_SHEET_ID,
                range="'Meta 2'!A1:Z500",
            )
            .execute()
        )
        rows = result.get("values", [])
        if len(rows) > 1:
            for row in rows[1:]:
                email = _safe_get(row, 13)
                if not email or "@" not in email:
                    # Meta 2 has a slightly different layout — email might be at index 12
                    email = _safe_get(row, 12)
                    if not email or "@" not in email:
                        continue
                    # Shifted layout: email=12, first_name=13, phone=14
                    all_leads.append(
                        {
                            "first_name": _safe_get(row, 13),
                            "last_name": "",
                            "email": email.lower(),
                            "phone": _clean_phone(_safe_get(row, 14)),
                            "campaign": "fb_new_lead",
                            "lead_date": _safe_get(row, 1),
                            "niche": "",
                            "platform": _safe_get(row, 11),
                            "ad_name": _safe_get(row, 3),
                            "campaign_name": _safe_get(row, 7),
                            "source_sheet": "Meta 2",
                        }
                    )
                else:
                    all_leads.append(
                        {
                            "first_name": _safe_get(row, 14),
                            "last_name": "",
                            "email": email.lower(),
                            "phone": _clean_phone(_safe_get(row, 15)),
                            "campaign": "fb_new_lead",
                            "lead_date": _safe_get(row, 1),
                            "niche": _safe_get(row, 12),
                            "platform": _safe_get(row, 11),
                            "ad_name": _safe_get(row, 3),
                            "campaign_name": _safe_get(row, 7),
                            "source_sheet": "Meta 2",
                        }
                    )
            print(
                f"[GSHEET] Meta 2 sheet: {len(rows)-1} rows, {len(all_leads)} valid leads"
            )

    except Exception as e:
        print(f"[GSHEET ERROR] Failed to read sheet: {e}")
        return []

    print(f"[GSHEET] Total leads fetched: {len(all_leads)}")
    return all_leads


def sync_sheet_leads():
    """
    Fetch leads from Google Sheet and upsert into the local SQLite tracker.
    Returns the number of new leads added.
    """
    leads = fetch_sheet_leads()
    if not leads:
        return 0

    # Get existing leads to count new ones
    existing = {l["email"].lower() for l in get_fb_leads(campaign="fb_new_lead")}

    new_count = 0
    for lead in leads:
        was_new = lead["email"].lower() not in existing
        upsert_fb_lead(
            first_name=lead["first_name"],
            last_name=lead["last_name"],
            email=lead["email"],
            phone=lead["phone"],
            campaign=lead["campaign"],
            lead_date=lead["lead_date"],
            source="google_sheet",
        )
        if was_new:
            new_count += 1
            existing.add(lead["email"].lower())

    print(f"[GSHEET] Synced {len(leads)} leads ({new_count} new)")
    return new_count
