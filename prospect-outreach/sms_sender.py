"""
SMS sending via Twilio Messaging Service with Alpha Sender ID "KLIQ".
"""

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, DRY_RUN

# Messaging Service SID (Alpha Sender ID: "KLIQ")
TWILIO_MESSAGING_SERVICE_SID = "MG6dda05b6ca48dd4359e7257b292379c0"


def send_sms(to_number, body):
    """
    Send an SMS via Twilio Messaging Service (sender shows as "KLIQ").
    Returns the message SID on success, 'dry_run' in dry-run mode, or None on error.
    """
    if DRY_RUN:
        print(f"[DRY RUN] SMS to {to_number}:")
        print(f"  {body[:120]}{'...' if len(body) > 120 else ''}")
        return "dry_run"

    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN]):
        print(f"[SMS ERROR] Twilio credentials not configured")
        return None

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            messaging_service_sid=TWILIO_MESSAGING_SERVICE_SID,
            to=to_number,
        )
        print(f"[SMS SENT] SID={message.sid} to={to_number} status={message.status}")
        return message.sid
    except TwilioRestException as e:
        print(f"[SMS ERROR] to={to_number}: {e.msg}")
        return None
