"""
Voice Order Agent handling dialogue and order extraction using LangChain / Groq.
"""
import json
import logging
from typing import Dict, Any, Tuple
from app.config import get_settings
from app.agent.menu_rag import get_menu

logger = logging.getLogger(__name__)
settings = get_settings()


class VoiceOrderAgent:
    """Conversational ordering agent."""

    def __init__(self):
        self.menu = get_menu()

    def get_llm(self):
        """Lazy load configured LLM (Groq free tier default, OpenAI fallback)."""
        provider = settings.llm_provider.lower()
        if provider == "groq" and settings.groq_api_key:
            from langchain_groq import ChatGroq
            return ChatGroq(
                groq_api_key=settings.groq_api_key,
                model_name=settings.groq_model,
                temperature=settings.llm_temperature,
            )
        elif settings.openai_api_key:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=settings.openai_api_key,
                model_name=settings.openai_model,
                temperature=settings.llm_temperature,
            )
        return None

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
        menu_summary = ", ".join(f"{it['name']} (₹{it['price']})" for it in menu_items)

        if not llm:
            # Rule-based fallback when no API key configured
            matched = self.menu.search(user_text, top_k=1)
            if matched:
                item = matched[0]
                updated_order = current_order + [{"name": item["name"], "quantity": 1, "price": item["price"]}]
                reply = f"I added one {item['name']} (₹{item['price']}) to your order. Would you like anything else or should I confirm?"
                return reply, updated_order, False
            return f"Welcome! We have: {menu_summary}. What would you like to order today?", current_order, False

        system_prompt = f"""You are a polite, helpful restaurant ordering voice assistant.
Menu: {menu_summary}
Current Cart: {json.dumps(current_order)}

Rules:
1. Greet customer and answer menu questions naturally.
2. When customer requests an item, match it to the menu.
3. Keep responses short and conversational for voice (1-2 sentences).
4. If customer says they are done or asks to place order, confirm total and mark completed=true.

Output JSON with keys:
"reply": string (voice response to user)
"cart": list of {{"name": str, "quantity": int, "price": float}}
"completed": boolean (true only if customer confirmed final order)
"""

        from langchain.schema import SystemMessage, HumanMessage
        messages = [SystemMessage(content=system_prompt)]
        for turn in conversation_history[-6:]:
            if turn.get("role") == "user":
                messages.append(HumanMessage(content=turn.get("content", "")))
            elif turn.get("role") == "assistant":
                from langchain.schema import AIMessage
                messages.append(AIMessage(content=turn.get("content", "")))
        messages.append(HumanMessage(content=user_text))

        try:
            res = await llm.ainvoke(messages)
            content = res.content.strip()
            # Parse JSON if possible
            if "{" in content and "}" in content:
                json_part = content[content.find("{"):content.rfind("}") + 1]
                parsed = json.loads(json_part)
                return (
                    parsed.get("reply", "Understood. Anything else?"),
                    parsed.get("cart", current_order),
                    parsed.get("completed", False)
                )
            return content, current_order, False
        except Exception as e:
            logger.error(f"LLM processing error: {e}")
            return "Got that. Would you like anything else with your order?", current_order, False


_agent_instance = None


def get_voice_agent() -> VoiceOrderAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = VoiceOrderAgent()
    return _agent_instance
