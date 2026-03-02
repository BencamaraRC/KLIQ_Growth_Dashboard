"""
SMS sending via Twilio Messaging Service with Alpha Sender ID "KLIQ".
"""

import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, DRY_RUN

log = logging.getLogger("sms_sender")

# Messaging Service SID (Alpha Sender ID: "KLIQ")
TWILIO_MESSAGING_SERVICE_SID = "MG6dda05b6ca48dd4359e7257b292379c0"


def send_sms(to_number, body):
    """
    Send an SMS via Twilio Messaging Service (sender shows as "KLIQ").
    Returns the message SID on success, 'dry_run' in dry-run mode, or None on error.
    """
    if DRY_RUN:
        log.info(f"[DRY RUN] SMS to {to_number}: {body[:80]}...")
        return "dry_run"

    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN]):
        log.error("Twilio credentials not configured")
        return None

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            messaging_service_sid=TWILIO_MESSAGING_SERVICE_SID,
            to=to_number,
        )
        log.info(f"SMS SENT SID={message.sid} to={to_number} status={message.status}")
        return message.sid
    except TwilioRestException as e:
        log.error(f"SMS ERROR to={to_number}: {e.msg}")
        return None
