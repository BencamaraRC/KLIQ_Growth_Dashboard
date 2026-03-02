"""
Facebook / Meta Marketing API integration.
Fetches campaign insights, lead form data, and audience demographics.
"""

import logging
import requests
from datetime import datetime, timedelta
from config import META_ACCESS_TOKEN, META_AD_ACCOUNT_ID, META_PAGE_ID, META_API_VERSION

log = logging.getLogger("meta.insights")

BASE_URL = f"https://graph.facebook.com/{META_API_VERSION}"

# ── In-memory cache (10 min TTL) ──────────────────────────────────
_CACHE = {}
_CACHE_TTL = 600  # seconds


def _cached(key):
    if key in _CACHE:
        entry = _CACHE[key]
        if (datetime.utcnow() - entry["ts"]).total_seconds() < _CACHE_TTL:
            return entry["data"]
    return None


def _set_cache(key, data):
    _CACHE[key] = {"data": data, "ts": datetime.utcnow()}


def _api_get(endpoint, params=None):
    """Make a GET request to the Meta Graph API."""
    if not META_ACCESS_TOKEN:
        print("[fb_insights] META_ACCESS_TOKEN not set")
        return None
    p = params or {}
    p["access_token"] = META_ACCESS_TOKEN
    try:
        url = f"{BASE_URL}{endpoint}"
        print(
            f"[fb_insights] GET {url} (params keys: {[k for k in p if k != 'access_token']})"
        )
        resp = requests.get(url, params=p, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        print(f"[fb_insights] Meta API {resp.status_code}: {resp.text[:500]}")
        return None
    except Exception as e:
        print(f"[fb_insights] Meta API error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# PAGES — discover Page ID automatically
# ═══════════════════════════════════════════════════════════════
def get_pages():
    """List pages the token has access to."""
    cached = _cached("pages")
    if cached is not None:
        return cached
    data = _api_get("/me/accounts", {"fields": "id,name,access_token"})
    pages = data.get("data", []) if data else []
    _set_cache("pages", pages)
    return pages


def get_page_id():
    """Return configured page ID or first available page."""
    if META_PAGE_ID:
        return META_PAGE_ID
    pages = get_pages()
    return pages[0]["id"] if pages else None


# ═══════════════════════════════════════════════════════════════
# CAMPAIGN INSIGHTS — spend, impressions, CPL, demographics
# ═══════════════════════════════════════════════════════════════
def get_campaign_insights(days_back=90):
    """Fetch campaign-level performance metrics."""
    cache_key = f"campaign_insights_{days_back}"
    cached = _cached(cache_key)
    if cached is not None:
        return cached

    if not META_AD_ACCOUNT_ID:
        log.warning("META_AD_ACCOUNT_ID not set")
        return []

    end = datetime.utcnow().strftime("%Y-%m-%d")
    start = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    data = _api_get(
        f"/{META_AD_ACCOUNT_ID}/insights",
        {
            "fields": "campaign_name,campaign_id,impressions,reach,clicks,cpc,cpm,"
            "spend,actions,cost_per_action_type,frequency",
            "time_range": f'{{"since":"{start}","until":"{end}"}}',
            "level": "campaign",
            "limit": 100,
        },
    )
    results = data.get("data", []) if data else []
    _set_cache(cache_key, results)
    return results


def get_demographic_insights(days_back=90, breakdown="age,gender"):
    """Fetch audience demographic breakdown for the ad account."""
    cache_key = f"demo_insights_{days_back}_{breakdown}"
    cached = _cached(cache_key)
    if cached is not None:
        return cached

    if not META_AD_ACCOUNT_ID:
        log.warning("META_AD_ACCOUNT_ID not set")
        return []

    end = datetime.utcnow().strftime("%Y-%m-%d")
    start = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    data = _api_get(
        f"/{META_AD_ACCOUNT_ID}/insights",
        {
            "fields": "impressions,reach,clicks,spend,actions,cost_per_action_type",
            "time_range": f'{{"since":"{start}","until":"{end}"}}',
            "breakdowns": breakdown,
            "limit": 200,
        },
    )
    results = data.get("data", []) if data else []
    _set_cache(cache_key, results)
    return results


def get_placement_insights(days_back=90):
    """Fetch performance breakdown by placement (Feed, Stories, Reels, etc.)."""
    return get_demographic_insights(
        days_back, breakdown="publisher_platform,platform_position"
    )


def get_device_insights(days_back=90):
    """Fetch performance breakdown by device platform."""
    return get_demographic_insights(days_back, breakdown="device_platform")


def get_hourly_insights(days_back=30):
    """Fetch performance breakdown by hour of day."""
    cache_key = f"hourly_insights_{days_back}"
    cached = _cached(cache_key)
    if cached is not None:
        return cached

    if not META_AD_ACCOUNT_ID:
        return []

    end = datetime.utcnow().strftime("%Y-%m-%d")
    start = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    data = _api_get(
        f"/{META_AD_ACCOUNT_ID}/insights",
        {
            "fields": "impressions,reach,clicks,spend,actions",
            "time_range": f'{{"since":"{start}","until":"{end}"}}',
            "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone",
            "limit": 50,
        },
    )
    results = data.get("data", []) if data else []
    _set_cache(cache_key, results)
    return results


def get_country_insights(days_back=90):
    """Fetch performance breakdown by country."""
    return get_demographic_insights(days_back, breakdown="country")


# ═══════════════════════════════════════════════════════════════
# LEAD FORMS — retrieve actual lead submissions
# ═══════════════════════════════════════════════════════════════
def get_lead_forms():
    """List all lead gen forms for the page."""
    cache_key = "lead_forms"
    cached = _cached(cache_key)
    if cached is not None:
        return cached

    page_id = get_page_id()
    if not page_id:
        log.warning("No page ID available")
        return []

    data = _api_get(
        f"/{page_id}/leadgen_forms",
        {"fields": "id,name,status,leads_count,created_time"},
    )
    forms = data.get("data", []) if data else []
    _set_cache(cache_key, forms)
    return forms


def get_leads_from_form(form_id, limit=500):
    """Retrieve individual lead submissions from a specific form."""
    cache_key = f"leads_{form_id}"
    cached = _cached(cache_key)
    if cached is not None:
        return cached

    all_leads = []
    url_params = {
        "fields": "created_time,field_data,ad_id,ad_name,adset_id,adset_name,"
        "campaign_id,campaign_name,platform,is_organic",
        "limit": 100,
    }

    data = _api_get(f"/{form_id}/leads", url_params)
    while data:
        leads = data.get("data", [])
        all_leads.extend(leads)
        if len(all_leads) >= limit:
            break
        # Pagination
        paging = data.get("paging", {})
        next_url = paging.get("next")
        if not next_url:
            break
        try:
            resp = requests.get(next_url, timeout=30)
            data = resp.json() if resp.status_code == 200 else None
        except Exception:
            break

    _set_cache(cache_key, all_leads)
    return all_leads


def get_all_leads(limit=1000):
    """Retrieve all leads across all forms."""
    forms = get_lead_forms()
    all_leads = []
    for form in forms:
        leads = get_leads_from_form(form["id"], limit=limit)
        for lead in leads:
            lead["form_name"] = form.get("name", "")
        all_leads.extend(leads)
    return all_leads


def parse_lead_fields(lead):
    """Parse a lead's field_data into a flat dict."""
    result = {
        "created_time": lead.get("created_time", ""),
        "ad_name": lead.get("ad_name", ""),
        "adset_name": lead.get("adset_name", ""),
        "campaign_name": lead.get("campaign_name", ""),
        "platform": lead.get("platform", ""),
        "is_organic": lead.get("is_organic", False),
        "form_name": lead.get("form_name", ""),
    }
    for field in lead.get("field_data", []):
        name = field.get("name", "").lower().replace(" ", "_")
        values = field.get("values", [])
        result[name] = values[0] if values else ""
    return result


# ═══════════════════════════════════════════════════════════════
# ACCOUNT SUMMARY — quick overview
# ═══════════════════════════════════════════════════════════════
def get_account_summary(days_back=90):
    """High-level account KPIs: total spend, leads, impressions, etc."""
    cache_key = f"account_summary_{days_back}"
    cached = _cached(cache_key)
    if cached is not None:
        return cached

    if not META_AD_ACCOUNT_ID:
        print("[fb_insights] get_account_summary: META_AD_ACCOUNT_ID not set")
        return {}

    print(
        f"[fb_insights] get_account_summary: account={META_AD_ACCOUNT_ID}, days_back={days_back}"
    )
    end = datetime.utcnow().strftime("%Y-%m-%d")
    start = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    data = _api_get(
        f"/{META_AD_ACCOUNT_ID}/insights",
        {
            "fields": "impressions,reach,clicks,cpc,cpm,spend,actions,"
            "cost_per_action_type,frequency,ctr",
            "time_range": f'{{"since":"{start}","until":"{end}"}}',
        },
    )
    results = data.get("data", []) if data else []
    summary = results[0] if results else {}
    if not summary:
        print(f"[fb_insights] get_account_summary: empty result, data={data}")
    _set_cache(cache_key, summary)
    return summary


def extract_action_value(actions_list, action_type):
    """Extract a specific action value from Meta's actions array."""
    if not actions_list:
        return 0
    for action in actions_list:
        if action.get("action_type") == action_type:
            return int(action.get("value", 0))
    return 0
