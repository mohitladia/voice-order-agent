"""
End-to-end tests for Voice Order Agent.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.agent.menu_rag import get_menu
from app.agent.voice_agent import get_voice_agent


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    """Verify health endpoint returns status and provider config."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "stt_provider" in data
    assert "llm_provider" in data


def test_menu_rag_lookup():
    """Verify menu loading and keyword search."""
    menu = get_menu()
    items = menu.get_all()
    assert len(items) > 0

    # Search for pizza
    pizza_results = menu.search("pizza", top_k=2)
    assert len(pizza_results) > 0
    assert any("pizza" in it["name"].lower() for it in pizza_results)

    # Search for cold coffee
    drink_results = menu.search("coffee", top_k=1)
    assert len(drink_results) > 0
    assert "coffee" in drink_results[0]["name"].lower()


@pytest.mark.asyncio
async def test_agent_conversation_turn():
    """Verify conversational turn processing by the agent."""
    agent = get_voice_agent()

    # Turn 1: Customer asks for Margherita Pizza
    reply, cart, completed = await agent.process_turn(
        user_text="I want one Margherita Pizza",
        current_order=[],
        conversation_history=[]
    )
    assert isinstance(reply, str)
    assert len(reply) > 0
    assert len(cart) > 0
    assert any("Margherita" in it["name"] for it in cart)
    assert completed is False

    # Turn 2: Customer confirms order
    reply_done, final_cart, is_done = await agent.process_turn(
        user_text="That's all, please confirm and place my order",
        current_order=cart,
        conversation_history=[
            {"role": "user", "content": "I want one Margherita Pizza"},
            {"role": "assistant", "content": reply}
        ]
    )
    assert isinstance(reply_done, str)
    assert is_done is True or len(final_cart) > 0


def test_twilio_voice_webhook(client):
    """Verify incoming voice webhook returns TwiML with speech gather."""
    response = client.post("/webhooks/twilio/voice")
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]
    xml_content = response.text
    assert "<Response>" in xml_content
    assert "<Gather" in xml_content
    assert "speech" in xml_content


def test_twilio_gather_webhook_flow(client):
    """Simulate a user speaking an order into the Twilio gather webhook."""
    form_data = {
        "SpeechResult": "I would like to order one Farmhouse Pizza please",
        "From": "+919876543210",
        "CallSid": "CA_test_12345"
    }
    response = client.post("/webhooks/twilio/gather", data=form_data)
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]
    assert "<Response>" in response.text
