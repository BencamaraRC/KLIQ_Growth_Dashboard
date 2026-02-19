"""
Configuration and constants for the prospect outreach system.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── BigQuery ──
GCP_PROJECT = "rcwl-development"  # project where jobs run (SA has bigquery.jobs.create)
DATA_PROJECT = "rcwl-data"  # project where data lives
BQ_LOCATION = "EU"

# Service account key — same key used by the growth dashboard
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_KEY = os.path.join(_PROJECT_ROOT, "rcwl-development-0c013e9b5c2b.json")
SERVICE_ACCOUNT_KEY = os.environ.get("GCP_SERVICE_ACCOUNT_KEY", "") or (
    _DEFAULT_KEY if os.path.exists(_DEFAULT_KEY) else ""
)

# ── Twilio ──
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# ── Brevo (email) ──
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_FROM_EMAIL = os.getenv("BREVO_FROM_EMAIL", "ben@joinkliq.io")
BREVO_FROM_NAME = os.getenv("BREVO_FROM_NAME", "Ben from KLIQ")

# ── Outreach settings ──
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "15"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# ── Sequence triggers ──
# Each trigger maps an event_name to a sequence step
SEQUENCE_TRIGGERS = {
    "self_serve_completed": "welcome",
    "profile_image_added_your_store": "profile_uploaded",
    "profile_image_added": "profile_uploaded",
    "coach_type_updated": "coach_type_set",
    "create_module": "first_module",
    "publish_module": "module_published",
}

# ── Cheat sheet config ──
CHEAT_SHEET_OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "output", "cheat_sheets"
)
os.makedirs(CHEAT_SHEET_OUTPUT_DIR, exist_ok=True)

# ── Database (SQLite for tracking sent messages) ──
DB_PATH = os.path.join(os.path.dirname(__file__), "outreach.db")
