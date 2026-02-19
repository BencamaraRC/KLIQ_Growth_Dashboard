"""
Email sending via Brevo (formerly Sendinblue).
"""

import base64
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from config import BREVO_API_KEY, BREVO_FROM_EMAIL, BREVO_FROM_NAME, DRY_RUN


def _get_api():
    """Get a configured Brevo transactional email API instance."""
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = BREVO_API_KEY
    return sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )


def send_email(to_email, subject, html_body, attachment_path=None):
    """
    Send an email via Brevo, optionally with a PDF attachment.
    Returns the Brevo message ID on success, or 'dry_run' in dry-run mode.
    """
    if DRY_RUN:
        print(f"[DRY RUN] Email to {to_email}:")
        print(f"  Subject: {subject}")
        print(f"  Attachment: {attachment_path or 'None'}")
        return "dry_run"

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to_email}],
        sender={"email": BREVO_FROM_EMAIL, "name": BREVO_FROM_NAME},
        subject=subject,
        html_content=html_body,
    )

    # Attach PDF if provided
    if attachment_path:
        with open(attachment_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        send_smtp_email.attachment = [
            {
                "content": encoded,
                "name": "KLIQ_Growth_Cheatsheet.pdf",
                "type": "application/pdf",
            }
        ]

    try:
        api = _get_api()
        response = api.send_transac_email(send_smtp_email)
        msg_id = response.message_id
        print(f"[EMAIL SENT] ID={msg_id} to={to_email}")
        return msg_id
    except ApiException as e:
        print(f"[EMAIL ERROR] to={to_email}: {e}")
        return None
