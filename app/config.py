"""
Configuration with provider selection support.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Provider selection
    stt_provider: str = "google"  # google | assemblyai | whisper
    tts_provider: str = "gtts"     # gtts | google | cartesia | elevenlabs
    llm_provider: str = "groq"     # groq | openai | anthropic | gemini
    whatsapp_provider: str = "twilio"  # twilio | greenapi

    # Google (STT/TTS)
    google_api_key: str = ""

    # Groq (free LLM)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # AssemblyAI
    assemblyai_api_key: str = ""

    # Whisper (local)
    whisper_model: str = "base"  # tiny | base | small | medium | large

    # Cartesia TTS
    cartesia_api_key: str = ""

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"

    # Green API (free WhatsApp)
    greenapi_instance_id: str = ""
    greenapi_token: str = ""

    # Language settings
    stt_language: str = "en-IN"
    tts_language: str = "en"

    # Database
    database_url: str = "sqlite:///./orders.db"

    # Application
    webhook_base_url: str = "http://localhost:8000"
    environment: str = "development"
    debug: bool = True

    # LLM settings
    llm_temperature: float = 0.7
    llm_max_tokens: int = 500

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()
