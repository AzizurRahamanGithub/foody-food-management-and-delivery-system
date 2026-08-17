import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(phone_number, message):
    """Send an SMS via Twilio.

    Config driven via settings/env:
      - TWILIO_ENABLED      : master switch (default True)
      - TWILIO_ACCOUNT_SID  : Twilio account SID
      - TWILIO_AUTH_TOKEN   : Twilio auth token
      - TWILIO_FROM_NUMBER  : verified Twilio sender number (E.164)
    """
    if not getattr(settings, 'TWILIO_ENABLED', True):
        return None

    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_FROM_NUMBER', '')

    if not account_sid or not auth_token or not from_number:
        logger.info("[SMS] Twilio not configured. phone=%s message=%s", phone_number, message)
        return None

    try:
        from twilio.rest import Client
    except ImportError:
        logger.warning("[SMS] twilio package not installed. phone=%s message=%s", phone_number, message)
        return None

    client = Client(account_sid, auth_token)
    response = client.messages.create(
        to=phone_number,
        from_=from_number,
        body=message,
    )
    logger.info("[SMS] Twilio message sid=%s status=%s", response.sid, response.status)
    return response
