"""
Email sending via AWS SES (primary) with Brevo fallback.

Provider controlled by EMAIL_PROVIDER env var:
  - "ses"        → SES only
  - "brevo"      → Brevo only
  - "ses+brevo"  → SES primary, Brevo fallback (default)
"""

import base64
import logging
import requests
from config import (
    BREVO_API_KEY,
    BREVO_FROM_EMAIL,
    BREVO_FROM_NAME,
    DRY_RUN,
    EMAIL_PROVIDER,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_SES_REGION,
    SES_FROM_EMAIL,
    SES_FROM_NAME,
)

log = logging.getLogger("email_sender")

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
OUTREACH_TAG = "kliq-outreach"
REPLY_TO_EMAIL = "ben@joinkliq.io"
REPLY_TO_NAME = "Ben from KLIQ"

# ── Lazy SES client ──
_ses_client = None


def _get_ses_client():
    global _ses_client
    if _ses_client is None:
        import boto3

        _ses_client = boto3.client(
            "ses",
            region_name=AWS_SES_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    return _ses_client


# ── SES sender ──
def _send_via_ses(to_email, subject, html_body, attachment_path=None):
    """Send email via AWS SES. Returns message ID or None."""
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        log.warning("AWS SES credentials not set — skipping SES.")
        return None

    try:
        client = _get_ses_client()

        if attachment_path:
            # SES raw email for attachments
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.application import MIMEApplication

            msg = MIMEMultipart("mixed")
            msg["Subject"] = subject
            msg["From"] = f"{SES_FROM_NAME} <{SES_FROM_EMAIL}>"
            msg["Reply-To"] = f"{REPLY_TO_NAME} <{REPLY_TO_EMAIL}>"
            msg["To"] = to_email

            body_part = MIMEText(html_body, "html")
            msg.attach(body_part)

            with open(attachment_path, "rb") as f:
                att = MIMEApplication(f.read(), _subtype="pdf")
                att.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename="KLIQ_Growth_Cheatsheet.pdf",
                )
                msg.attach(att)

            resp = client.send_raw_email(
                Source=f"{SES_FROM_NAME} <{SES_FROM_EMAIL}>",
                Destinations=[to_email],
                RawMessage={"Data": msg.as_string()},
            )
        else:
            resp = client.send_email(
                Source=f"{SES_FROM_NAME} <{SES_FROM_EMAIL}>",
                Destination={"ToAddresses": [to_email]},
                ReplyToAddresses=[REPLY_TO_EMAIL],
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Html": {"Data": html_body, "Charset": "UTF-8"}},
                },
                Tags=[{"Name": "campaign", "Value": OUTREACH_TAG}],
            )

        msg_id = resp.get("MessageId", "unknown")
        log.info(f"EMAIL SENT [SES] ID={msg_id} to={to_email}")
        return msg_id
    except Exception as e:
        log.error(f"EMAIL ERROR [SES] to={to_email}: {e}")
        return None


# ── Brevo sender ──
def _send_via_brevo(to_email, subject, html_body, attachment_path=None):
    """Send email via Brevo REST API. Returns message ID or None."""
    if not BREVO_API_KEY:
        log.warning("BREVO_API_KEY not set — skipping Brevo.")
        return None

    payload = {
        "sender": {"email": BREVO_FROM_EMAIL, "name": BREVO_FROM_NAME},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
        "tags": [OUTREACH_TAG],
        "replyTo": {"email": REPLY_TO_EMAIL, "name": REPLY_TO_NAME},
    }

    if attachment_path:
        with open(attachment_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        payload["attachment"] = [
            {"content": encoded, "name": "KLIQ_Growth_Cheatsheet.pdf"}
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
        log.info(f"EMAIL SENT [Brevo] ID={msg_id} to={to_email}")
        return msg_id
    except requests.exceptions.HTTPError as e:
        log.error(f"EMAIL ERROR [Brevo] to={to_email}: {e} — {resp.text}")
        return None
    except Exception as e:
        log.error(f"EMAIL ERROR [Brevo] to={to_email}: {e}")
        return None


# ── Main send function ──
def send_email(to_email, subject, html_body, attachment_path=None):
    """
    Send an email using the configured provider(s).
    EMAIL_PROVIDER controls routing:
      - "ses"        → SES only
      - "brevo"      → Brevo only
      - "ses+brevo"  → Try SES first, fall back to Brevo
    Returns the message ID on success, or 'dry_run' / None.
    """
    if DRY_RUN:
        log.info(f"[DRY RUN] Email to {to_email}: Subject={subject}")
        return "dry_run"

    provider = EMAIL_PROVIDER.lower().strip()

    if provider == "brevo":
        return _send_via_brevo(to_email, subject, html_body, attachment_path)

    if provider == "ses":
        return _send_via_ses(to_email, subject, html_body, attachment_path)

    # Default: ses+brevo — try SES first, Brevo fallback
    msg_id = _send_via_ses(to_email, subject, html_body, attachment_path)
    if msg_id:
        return msg_id

    log.info(f"SES failed for {to_email} — falling back to Brevo")
    return _send_via_brevo(to_email, subject, html_body, attachment_path)
