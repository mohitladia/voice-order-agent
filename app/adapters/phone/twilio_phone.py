"""
Twilio Phone Call Adapter for outbound phone calls.
"""
import logging
from typing import Dict, Any
from app.adapters.base import PhoneAdapter

logger = logging.getLogger(__name__)


class TwilioPhoneAdapter(PhoneAdapter):
    """Twilio phone call adapter."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.client = None
        if account_sid and auth_token and not account_sid.startswith("ACxxxx"):
            from twilio.rest import Client
            self.client = Client(account_sid, auth_token)

    async def initiate_call(self, to_phone: str, webhook_url: str) -> Dict[str, Any]:
        """
        Initiate an outbound phone call and connect it to TwiML webhook.
        """
        if not self.client:
            logger.warning("Twilio client not configured. Simulating outbound call.")
            return {
                "call_sid": "SIMULATED_CALL_SID",
                "status": "queued",
                "to": to_phone,
                "from": self.from_number,
                "simulated": True
            }

        call = self.client.calls.create(
            to=to_phone,
            from_=self.from_number,
            url=webhook_url,
            method="POST"
        )

        return {
            "call_sid": call.sid,
            "status": call.status,
            "to": to_phone,
            "from": self.from_number,
            "simulated": False
        }

    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        if not self.client or call_id.startswith("SIMULATED"):
            return {"call_sid": call_id, "status": "completed"}

        call = self.client.calls(call_id).fetch()
        return {
            "call_sid": call.sid,
            "status": call.status,
            "duration": call.duration
        }
