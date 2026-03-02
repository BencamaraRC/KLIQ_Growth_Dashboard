"""
One-time backfill: sync all existing prospects and FB leads to Brevo contacts.
Run this once to populate COACH_TYPE for contacts already in the DB.

Usage:
    python backfill_brevo_contacts.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from tracker import get_all_prospects, get_fb_leads
from brevo_contacts import sync_contact, sync_contact_from_fb_lead
import time


def main():
    print("=" * 60)
    print("Backfilling Brevo contacts with coach_type...")
    print("=" * 60)

    # 1. Sync all prospects (KLIQ signups)
    prospects = get_all_prospects()
    print(f"\n[PROSPECTS] Found {len(prospects)} prospects to sync")
    synced = 0
    for p in prospects:
        email = p.get("email")
        coach_type = p.get("coach_type")
        if not email:
            continue
        name = p.get("name", "")
        first_name = name.split()[0] if name else None
        last_name = " ".join(name.split()[1:]) if name and len(name.split()) > 1 else None

        ok = sync_contact(
            email=email,
            first_name=first_name,
            last_name=last_name,
            coach_type=coach_type,
            country=p.get("country"),
            phone=p.get("phone"),
            source="kliq_signup",
        )
        if ok:
            synced += 1
            print(f"  ✅ {email} — coach_type={coach_type or 'N/A'}")
        else:
            print(f"  ❌ {email} — failed")
        time.sleep(0.2)  # Rate limit

    print(f"\n[PROSPECTS] Synced {synced}/{len(prospects)} to Brevo")

    # 2. Sync all FB leads (Meta ad leads)
    fb_leads = get_fb_leads(campaign="fb_new_lead")
    print(f"\n[FB LEADS] Found {len(fb_leads)} FB leads to sync")
    fb_synced = 0
    for lead in fb_leads:
        email = lead.get("email")
        if not email:
            continue
        ok = sync_contact_from_fb_lead(lead)
        if ok:
            fb_synced += 1
            print(f"  ✅ {email}")
        else:
            print(f"  ❌ {email} — failed")
        time.sleep(0.2)

    print(f"\n[FB LEADS] Synced {fb_synced}/{len(fb_leads)} to Brevo")

    print(f"\n{'=' * 60}")
    print(f"DONE — Total synced: {synced + fb_synced}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
