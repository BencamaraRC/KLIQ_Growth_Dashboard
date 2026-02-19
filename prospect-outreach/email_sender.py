"""
Email sending via Brevo (formerly Sendinblue) REST API.
"""

import base64
import requests
from config import BREVO_API_KEY, BREVO_FROM_EMAIL, BREVO_FROM_NAME, DRY_RUN

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_email(to_email, subject, html_body, attachment_path=None):
    """
    Send an email via Brevo REST API, optionally with a PDF attachment.
    Returns the Brevo message ID on success, or 'dry_run' in dry-run mode.
    """
    if DRY_RUN:
        print(f"[DRY RUN] Email to {to_email}:")
        print(f"  Subject: {subject}")
        print(f"  Attachment: {attachment_path or 'None'}")
        return "dry_run"

    if not BREVO_API_KEY:
        print("[EMAIL ERROR] BREVO_API_KEY is not set.")
        return None

    payload = {
        "sender": {"email": BREVO_FROM_EMAIL, "name": BREVO_FROM_NAME},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
    }

    # Attach PDF if provided
    if attachment_path:
        with open(attachment_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        payload["attachment"] = [
            {
                "content": encoded,
                "name": "KLIQ_Growth_Cheatsheet.pdf",
            }
        ]

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY,
    }

    try:
        resp = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        msg_id = resp.json().get("messageId", "unknown")
        print(f"[EMAIL SENT] ID={msg_id} to={to_email}")
        return msg_id
    except requests.exceptions.HTTPError as e:
        print(f"[EMAIL ERROR] to={to_email}: {e} — {resp.text}")
        return None
    except Exception as e:
        print(f"[EMAIL ERROR] to={to_email}: {e}")
        return None
