"""
Exclusion rules: determines which prospects should NOT receive outreach.

Rules:
1. Never contact apps with active Stripe subscriptions (already paying customers)
2. Never contact Dollar Diva (application_id = 274764)
3. Never contact KLIQ internal/test accounts (@joinkliq.io emails)
"""

from data_pipeline import get_client
from config import DATA_PROJECT

# Hard-coded exclusion list (application IDs)
BLOCKED_APP_IDS = {
    274764,  # Dollar Diva
}

# Email domains to exclude (internal/test accounts)
BLOCKED_EMAIL_DOMAINS = {
    "joinkliq.io",
}

# Cache for active app IDs (refreshed each poll cycle)
_active_app_ids_cache = None


def refresh_active_apps():
    """
    Fetch the set of application_ids that have active Stripe subscriptions.
    These are paying customers — never send them cold outreach.
    """
    global _active_app_ids_cache
    client = get_client()

    sql = f"""
    SELECT DISTINCT application_id
    FROM `{DATA_PROJECT}.prod_dataset.subscription_details`
    WHERE status = 'active'
    """
    df = client.query(sql).to_dataframe()
    _active_app_ids_cache = set(df["application_id"].tolist()) if not df.empty else set()
    print(f"[EXCLUSIONS] Loaded {len(_active_app_ids_cache)} active app IDs to exclude")
    return _active_app_ids_cache


def get_active_app_ids():
    """Get cached set of active app IDs, refreshing if needed."""
    global _active_app_ids_cache
    if _active_app_ids_cache is None:
        refresh_active_apps()
    return _active_app_ids_cache


def is_excluded(application_id, email=None, app_name=None):
    """
    Check if a prospect should be excluded from outreach.

    Returns (excluded: bool, reason: str or None).
    """
    # Rule 1: Hard-coded blocked app IDs
    if application_id in BLOCKED_APP_IDS:
        return True, f"Blocked app ID ({application_id})"

    # Rule 2: Dollar Diva by name (in case ID changes)
    if app_name and "dollar diva" in app_name.lower():
        return True, "Dollar Diva (blocked by name)"

    # Rule 3: Active Stripe subscription
    active_ids = get_active_app_ids()
    if application_id in active_ids:
        return True, "Active Stripe subscription"

    # Rule 4: Internal/test email domains
    if email:
        domain = email.split("@")[-1].lower() if "@" in email else ""
        if domain in BLOCKED_EMAIL_DOMAINS:
            return True, f"Internal email domain ({domain})"

    return False, None


if __name__ == "__main__":
    # Test exclusions
    print("=== Testing exclusion rules ===")

    tests = [
        (274764, "info@dollardiva.com", "Dollar Diva"),
        (731507799, "ben_dev87@joinkliq.io", "TEST TEST"),
        (999999, "user@gmail.com", "Some Coach"),
    ]

    for app_id, email, name in tests:
        excluded, reason = is_excluded(app_id, email, name)
        status = f"EXCLUDED: {reason}" if excluded else "OK"
        print(f"  app_id={app_id:>10}  {name:20s}  {email:35s}  → {status}")

    # Show how many active apps are excluded
    active = get_active_app_ids()
    print(f"\nTotal active apps excluded: {len(active)}")
