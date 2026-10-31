"""
Base interfaces for all adapters - allows easy provider switching.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any


class STTAdapter(ABC):
    """Speech-to-Text adapter interface."""

    @abstractmethod
    async def transcribe_stream(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[str]:
        """
        Transcribe audio stream to text in real-time.

        Args:
            audio_stream: Async iterator of audio chunks (PCM16, 16kHz recommended)

        Yields:
            Transcribed text chunks as they become available
        """
        pass

    @abstractmethod
    async def close(self):
        """Close the STT connection."""
        pass


class TTSAdapter(ABC):
    """Text-to-Speech adapter interface."""

    @abstractmethod
    async def synthesize_stream(self, text_stream: AsyncIterator[str]) -> AsyncIterator[bytes]:
        """
        Synthesize text stream to audio in real-time.

        Args:
            text_stream: Async iterator of text chunks

        Yields:
            Audio chunks (PCM16, 16kHz or WAV format)
        """
        pass

    @abstractmethod
    async def close(self):
        """Close the TTS connection."""
        pass


class WhatsAppAdapter(ABC):
    """WhatsApp messaging adapter interface."""

    @abstractmethod
    async def send_message(self, to_phone: str, message: str) -> str:
        """
        Send WhatsApp message.

        Args:
            to_phone: Phone number in E.164 format (+919876543210)
            message: Message text

        Returns:
            Message ID
        """
        pass

    @abstractmethod
    async def send_media(self, to_phone: str, media_url: str, caption: str = "") -> str:
        """Send media (image/audio/video) via WhatsApp."""
        pass


class PhoneAdapter(ABC):
    """Phone call adapter interface."""

    @abstractmethod
    async def initiate_call(self, to_phone: str, webhook_url: str) -> Dict[str, Any]:
        """
        Initiate outbound call.

        Args:
            to_phone: Phone number to call
            webhook_url: Webhook for call events

        Returns:
            Call metadata (call_id, status)
        """
        pass

    @abstractmethod
    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get call status and metadata."""
        pass
