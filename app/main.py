"""
Main FastAPI app for Voice Order Agent.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Form, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.database import init_db, get_db
from app.models.order import OrderModel, OrderResponse
from app.agent.voice_agent import get_voice_agent
from app.adapters.factory import get_whatsapp_adapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Voice Order Agent...")
    init_db()
    yield
    logger.info("Voice Order Agent shutdown.")


app = FastAPI(
    title="Voice Order Agent",
    description="Extendible AI Voice Agent for phone-based order taking with WhatsApp confirmations",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "stt_provider": settings.stt_provider,
        "tts_provider": settings.tts_provider,
        "llm_provider": settings.llm_provider,
        "whatsapp_provider": settings.whatsapp_provider,
    }


@app.post("/webhooks/twilio/voice")
async def twilio_voice_webhook():
    """TwiML response to greet customer and gather voice input."""
    from twilio.twiml.voice_response import VoiceResponse, Gather

    resp = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/webhooks/twilio/gather",
        method="POST",
        speech_timeout="auto",
        language=settings.stt_language,
    )
    gather.say(
        "Welcome to our restaurant! I am your AI assistant. What would you like to order today?",
        voice="Polly.Aditi" if "IN" in settings.stt_language else "Polly.Joanna"
    )
    resp.append(gather)
    resp.redirect("/webhooks/twilio/voice")
    return Response(content=str(resp), media_type="application/xml")


@app.post("/webhooks/twilio/gather")
async def twilio_gather_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Processes customer speech gathered by Twilio."""
    from twilio.twiml.voice_response import VoiceResponse, Gather

    form_data = await request.form()
    speech_result = form_data.get("SpeechResult", "")
    from_phone = form_data.get("From", "Customer")
    call_sid = form_data.get("CallSid", "")

    logger.info(f"Speech from {from_phone}: {speech_result}")

    agent = get_voice_agent()
    reply, cart, completed = await agent.process_turn(
        user_text=speech_result,
        current_order=[],
        conversation_history=[]
    )

    resp = VoiceResponse()

    if completed and cart:
        total = sum(it.get("price", 0) * it.get("quantity", 1) for it in cart)
        order = OrderModel(
            customer_phone=from_phone,
            items=cart,
            total_amount=total,
            status="confirmed",
            call_id=call_sid,
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        resp.say(f"{reply} Your order number is {order.id}. Thank you!")
        resp.hangup()

        # Send WhatsApp confirmation in background
        background_tasks.add_task(send_whatsapp_receipt, order.id, from_phone, cart, total)
    else:
        gather = Gather(
            input="speech",
            action="/webhooks/twilio/gather",
            method="POST",
            speech_timeout="auto",
            language=settings.stt_language,
        )
        gather.say(reply)
        resp.append(gather)
        resp.redirect("/webhooks/twilio/voice")

    return Response(content=str(resp), media_type="application/xml")


async def send_whatsapp_receipt(order_id: int, phone: str, items: list, total: float):
    try:
        adapter = get_whatsapp_adapter()
        items_str = "\n".join(f"• {it['name']} x{it.get('quantity', 1)} - ₹{it.get('price', 0)}" for it in items)
        msg = f"🎉 *Order Confirmed!* (Order #{order_id})\n\n{items_str}\n\n*Total:* ₹{total:.2f}\n\nPreparing your order now! 🍕"
        await adapter.send_message(to_phone=phone, message=msg)
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")


@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order_endpoint(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(
        id=order.id,
        customer_phone=order.customer_phone,
        customer_name=order.customer_name,
        items=order.items or [],
        total_amount=order.total_amount or 0.0,
        delivery_address=order.delivery_address,
        special_instructions=order.special_instructions,
        status=order.status,
        business_id=order.business_id,
        whatsapp_sent=bool(order.whatsapp_message_sid),
        created_at=order.created_at,
    )
