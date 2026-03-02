"""
Brevo Contact Sync — creates or updates contacts in Brevo with attributes
like COACH_TYPE, FIRSTNAME, LASTNAME, COUNTRY, SOURCE.

Called when:
  1. A new coach signs up on KLIQ (process_signup in run.py)
  2. A Meta ad lead is processed (process_fb_leads in gsheet_leads.py)

Requires BREVO_API_KEY env var.
"""

import logging
import requests
from config import BREVO_API_KEY

log = logging.getLogger("brevo_contacts")

BREVO_CONTACTS_URL = "https://api.brevo.com/v3/contacts"


def sync_contact(
    email,
    first_name=None,
    last_name=None,
    coach_type=None,
    country=None,
    phone=None,
    source=None,
    list_ids=None,
):
    """
    Create or update a contact in Brevo with the given attributes.

    Attributes are passed in UPPERCASE as required by Brevo API.
    Uses updateEnabled=true so existing contacts get updated (not duplicated).

    Args:
        email: Contact email (required)
        first_name: First name
        last_name: Last name
        coach_type: Coaching niche (e.g. "fitness", "life coaching")
        country: Country
        phone: Phone number in E.164 format (e.g. "+447...")
        source: Where the contact came from (e.g. "kliq_signup", "meta_lead")
        list_ids: Optional list of Brevo list IDs to add contact to

    Returns:
        True if successful, False otherwise.
    """
    if not BREVO_API_KEY:
        log.warning("BREVO_API_KEY not set — skipping contact sync.")
        return False

    if not email or "@" not in email:
        return False

    # Build attributes dict — only include non-empty values
    attributes = {}
    if first_name:
        attributes["FIRSTNAME"] = first_name
    if last_name:
        attributes["LASTNAME"] = last_name
    if coach_type:
        attributes["COACH_TYPE"] = coach_type
    if country:
        attributes["COUNTRY"] = country
    if phone:
        attributes["SMS"] = phone
    if source:
        attributes["SOURCE"] = source

    payload = {
        "email": email.lower().strip(),
        "updateEnabled": True,
        "attributes": attributes,
    }

    if list_ids:
        payload["listIds"] = list_ids

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY,
    }

    try:
        resp = requests.post(
            BREVO_CONTACTS_URL, json=payload, headers=headers, timeout=15
        )
        if resp.status_code in (200, 201, 204):
            log.info(
                f"[BREVO CONTACT] Synced {email} — coach_type={coach_type}, source={source}"
            )
            return True
        else:
            log.warning(
                f"[BREVO CONTACT] Failed for {email}: HTTP {resp.status_code} — {resp.text[:200]}"
            )
            return False
    except Exception as e:
        log.warning(f"[BREVO CONTACT] Error syncing {email}: {e}")
        return False


def sync_contact_from_prospect(prospect):
    """
    Convenience: sync a prospect dict (from tracker.py) to Brevo.
    Extracts first_name, coach_type, country, phone from the prospect.
    """
    if not prospect:
        return False

    email = prospect.get("email")
    if not email:
        return False

    name = prospect.get("name", "")
    first_name = prospect.get("first_name") or prospect.get("greeting_name")
    if not first_name:
        first_name = name.split()[0] if name else None
    last_name = " ".join(name.split()[1:]) if name and len(name.split()) > 1 else None

    return sync_contact(
        email=email,
        first_name=first_name,
        last_name=last_name,
        coach_type=prospect.get("coach_type"),
        country=prospect.get("country"),
        phone=prospect.get("phone"),
        source="kliq_signup",
    )


def sync_contact_from_fb_lead(lead):
    """
    Convenience: sync a FB lead dict (from gsheet_leads.py) to Brevo.
    Extracts first_name, niche (as coach_type), phone from the lead.
    """
    if not lead:
        return False

    email = lead.get("email")
    if not email:
        return False

    return sync_contact(
        email=email,
        first_name=lead.get("first_name"),
        last_name=lead.get("last_name"),
        coach_type=lead.get("niche"),
        phone=lead.get("phone"),
        source="meta_lead",
    )
