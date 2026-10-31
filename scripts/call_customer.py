"""
CLI script to trigger an outbound AI call to a customer.
Usage:
  python scripts/call_customer.py +919876543210
"""
import sys
import asyncio
from app.config import get_settings
from app.adapters.factory import get_phone_adapter


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/call_customer.py <phone_number> [webhook_url]")
        print("Example: python scripts/call_customer.py +919876543210 https://your-tunnel.ngrok-free.app/webhooks/twilio/voice")
        sys.exit(1)

    to_phone = sys.argv[1]
    settings = get_settings()
    webhook_url = sys.argv[2] if len(sys.argv) > 2 else f"{settings.webhook_base_url.rstrip('/')}/webhooks/twilio/voice"

    print(f"Initiating call to: {to_phone}")
    print(f"Connecting to webhook: {webhook_url}")
    print(f"Twilio Number: {settings.twilio_phone_number}")

    adapter = get_phone_adapter()
    result = await adapter.initiate_call(to_phone=to_phone, webhook_url=webhook_url)
    print("Call response:", result)


if __name__ == "__main__":
    asyncio.run(main())
