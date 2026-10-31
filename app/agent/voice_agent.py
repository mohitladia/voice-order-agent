"""
Voice Order Agent handling dialogue and order extraction using LangChain / Groq.
"""
import json
import logging
from typing import Dict, Any, Tuple, List
from pydantic import BaseModel, Field

from app.config import get_settings
from app.agent.menu_rag import get_menu

logger = logging.getLogger(__name__)
settings = get_settings()


class CartItem(BaseModel):
    name: str = Field(description="Item name matching the restaurant menu")
    quantity: int = Field(default=1, description="Quantity ordered")
    price: float = Field(description="Price per item in INR")


class TurnOutput(BaseModel):
    reply: str = Field(description="Conversational, short voice response to customer (1-2 sentences)")
    cart: List[CartItem] = Field(default_factory=list, description="Complete updated cart list")
    completed: bool = Field(default=False, description="True only if user confirmed order and is ready to place it")


class VoiceOrderAgent:
    """Conversational ordering agent using LangChain sandwich architecture."""

    def __init__(self):
        self.menu = get_menu()

    def get_llm(self):
        """Lazy load configured LLM (Groq free tier default, OpenAI fallback)."""
        provider = settings.llm_provider.lower()
        if provider == "groq" and settings.groq_api_key and settings.groq_api_key != "your-groq-api-key":
            from langchain_groq import ChatGroq
            return ChatGroq(
                groq_api_key=settings.groq_api_key,
                model_name=settings.groq_model,
                temperature=settings.llm_temperature,
            )
        elif settings.openai_api_key and settings.openai_api_key != "your-openai-key":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=settings.openai_api_key,
                model_name=settings.openai_model,
                temperature=settings.llm_temperature,
            )
        return None

    def _fallback_turn(
        self,
        user_text: str,
        current_order: list,
        menu_summary: str
    ) -> Tuple[str, list, bool]:
        """Deterministic rule-based fallback when LLM fails or is not configured."""
        user_lower = user_text.lower()

        # Check for confirmation keywords
        confirm_words = ["confirm", "place order", "that's all", "that is all", "done", "finish", "checkout"]
        if any(w in user_lower for w in confirm_words) and current_order:
            total = sum(it.get("price", 0) * it.get("quantity", 1) for it in current_order)
            return f"Your total is Rs.{total:.2f}. Your order is confirmed and being prepared!", current_order, True

        # Check for item mention
        matched = self.menu.search(user_text, top_k=1)
        if matched:
            item = matched[0]
            updated_order = list(current_order) + [{"name": item["name"], "quantity": 1, "price": item["price"]}]
            reply = f"I added one {item['name']} (Rs.{item['price']}) to your order. Would you like anything else or should I confirm?"
            return reply, updated_order, False

        return f"Welcome! We have: {menu_summary}. What would you like to order today?", current_order, False

    async def process_turn(
        self,
        user_text: str,
        current_order: list,
        conversation_history: list
    ) -> Tuple[str, list, bool]:
        """
        Process a single conversation turn.

        Returns:
            (reply_text, updated_order_items, is_completed)
        """
        llm = self.get_llm()
        menu_items = self.menu.get_all()
        menu_summary = ", ".join(f"{it['name']} (Rs.{it['price']})" for it in menu_items)

        if not llm:
            return self._fallback_turn(user_text, current_order, menu_summary)

        system_prompt = f"""You are a polite, helpful restaurant ordering voice assistant.
Menu: {menu_summary}
Current Cart: {json.dumps(current_order)}

Rules:
1. Greet customer and answer menu questions naturally.
2. When customer requests an item, match it to the menu and add to cart. Keep existing items in cart unless customer asks to remove them.
3. Keep responses short and conversational for voice (1-2 sentences).
4. If customer says they are done, finished, or asks to confirm/place order, set completed=true.
"""

        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        messages = [SystemMessage(content=system_prompt)]
        for turn in conversation_history[-6:]:
            if turn.get("role") == "user":
                messages.append(HumanMessage(content=turn.get("content", "")))
            elif turn.get("role") == "assistant":
                messages.append(AIMessage(content=turn.get("content", "")))
        messages.append(HumanMessage(content=user_text))

        try:
            structured_llm = llm.with_structured_output(TurnOutput)
            result: TurnOutput = await structured_llm.ainvoke(messages)

            # Convert pydantic cart items to list of dicts
            cart_dicts = [
                {"name": it.name, "quantity": it.quantity, "price": it.price}
                for it in result.cart
            ]

            # If user already had items and LLM returned empty, retain current order unless user cleared
            if not cart_dicts and current_order and not any(w in user_text.lower() for w in ["remove", "clear", "cancel"]):
                cart_dicts = current_order

            return result.reply, cart_dicts, result.completed

        except Exception as e:
            logger.warning(f"Structured LLM failed: {e}. Falling back to rule-based parser.")
            return self._fallback_turn(user_text, current_order, menu_summary)


_agent_instance = None


def get_voice_agent() -> VoiceOrderAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = VoiceOrderAgent()
    return _agent_instance
