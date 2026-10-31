"""
Twilio WhatsApp adapter.
"""
from app.adapters.base import WhatsAppAdapter
import logging

logger = logging.getLogger(__name__)


class TwilioWhatsAppAdapter(WhatsAppAdapter):
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.client = None
        if account_sid and auth_token:
            from twilio.rest import Client
            self.client = Client(account_sid, auth_token)

    async def send_message(self, to_phone: str, message: str) -> str:
        if not self.client:
            logger.warning("Twilio client not configured. Skipping WhatsApp message.")
            return "simulated_sid"

        if not to_phone.startswith("whatsapp:"):
            to_phone = f"whatsapp:{to_phone}"

        msg = self.client.messages.create(
            from_=self.from_number,
            to=to_phone,
            body=message
        )
        return msg.sid

    async def send_media(self, to_phone: str, media_url: str, caption: str = "") -> str:
        if not self.client:
            return "simulated_sid"

        if not to_phone.startswith("whatsapp:"):
            to_phone = f"whatsapp:{to_phone}"

        msg = self.client.messages.create(
            from_=self.from_number,
            to=to_phone,
            body=caption,
            media_url=[media_url]
        )
        return msg.sid
