"""
Adapter factory - selects providers based on config.
"""
from app.adapters.base import STTAdapter, TTSAdapter, WhatsAppAdapter
from app.config import get_settings
from typing import Type
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


def get_stt_adapter() -> STTAdapter:
    """Get STT adapter based on config."""
    provider = settings.stt_provider.lower()

    if provider == "google":
        from app.adapters.stt.google_stt import GoogleSTTSyncAdapter
        return GoogleSTTSyncAdapter(
            api_key=settings.google_api_key,
            language_code=settings.stt_language
        )
    elif provider == "assemblyai":
        from app.adapters.stt.assemblyai_stt import AssemblyAISTTAdapter
        return AssemblyAISTTAdapter(api_key=settings.assemblyai_api_key)
    elif provider == "whisper":
        from app.adapters.stt.whisper_stt import WhisperSTTAdapter
        return WhisperSTTAdapter(model_size=settings.whisper_model)
    else:
        raise ValueError(f"Unknown STT provider: {provider}")


def get_tts_adapter() -> TTSAdapter:
    """Get TTS adapter based on config."""
    provider = settings.tts_provider.lower()

    if provider == "gtts":
        from app.adapters.tts.gtts_adapter import GTTSAdapter
        return GTTSAdapter(lang=settings.tts_language)
    elif provider == "google":
        from app.adapters.tts.gtts_adapter import GoogleTTSAdapter
        return GoogleTTSAdapter(
            api_key=settings.google_api_key,
            language_code=settings.tts_language
        )
    elif provider == "cartesia":
        from app.adapters.tts.cartesia_tts import CartesiaTTSAdapter
        return CartesiaTTSAdapter(api_key=settings.cartesia_api_key)
    else:
        raise ValueError(f"Unknown TTS provider: {provider}")


def get_whatsapp_adapter() -> WhatsAppAdapter:
    """Get WhatsApp adapter based on config."""
    provider = settings.whatsapp_provider.lower()

    if provider == "twilio":
        from app.adapters.whatsapp.twilio_adapter import TwilioWhatsAppAdapter
        return TwilioWhatsAppAdapter(
            account_sid=settings.twilio_account_sid,
            auth_token=settings.twilio_auth_token,
            from_number=settings.twilio_whatsapp_from
        )
    elif provider == "greenapi":
        from app.adapters.whatsapp.greenapi_adapter import GreenAPIAdapter
        return GreenAPIAdapter(
            instance_id=settings.greenapi_instance_id,
            api_token=settings.greenapi_token
        )
    else:
        raise ValueError(f"Unknown WhatsApp provider: {provider}")
