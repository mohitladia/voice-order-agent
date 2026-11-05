from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
call = client.calls.create(
    to="+917264064842",
    from_=os.environ["TWILIO_PHONE_NUMBER"],
    url="https://anime-capable-trail-caribbean.trycloudflare.com/webhooks/twilio/voice",
)
print(call.sid)