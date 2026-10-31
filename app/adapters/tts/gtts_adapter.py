"""
gTTS (Google Text-to-Speech) adapter - completely free.
"""
import asyncio
import io
from typing import AsyncIterator
from gtts import gTTS
from app.adapters.base import TTSAdapter
import logging

logger = logging.getLogger(__name__)


class GTTSAdapter(TTSAdapter):
    """gTTS adapter - free, no API key needed."""

    def __init__(self, lang: str = "en", tld: str = "co.in"):
        self.lang = lang  # "en" for English, "hi" for Hindi
        self.tld = tld  # "co.in" for Indian accent, "com" for US

    async def synthesize_stream(self, text_stream: AsyncIterator[str]) -> AsyncIterator[bytes]:
        """
        Synthesize text to audio using gTTS.

        Note: gTTS doesn't support real streaming, so we batch per sentence.
        """
        buffer = ""

        async for text_chunk in text_stream:
            buffer += text_chunk

            # Send complete sentences
            sentences = buffer.split(". ")
            if len(sentences) > 1:
                # Process all but last (incomplete) sentence
                for sentence in sentences[:-1]:
                    if sentence.strip():
                        audio_bytes = await self._synthesize_text(sentence + ".")
                        yield audio_bytes

                buffer = sentences[-1]

        # Process remaining buffer
        if buffer.strip():
            audio_bytes = await self._synthesize_text(buffer)
            yield audio_bytes

    async def _synthesize_text(self, text: str) -> bytes:
        """Synthesize a single text chunk."""
        try:
            # Run gTTS in thread pool (it's blocking)
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(
                None,
                self._generate_audio,
                text
            )
            return audio_bytes
        except Exception as e:
            logger.error(f"gTTS synthesis error: {e}")
            return b""

    def _generate_audio(self, text: str) -> bytes:
        """Generate audio (blocking call)."""
        tts = gTTS(text=text, lang=self.lang, tld=self.tld, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()

    async def close(self):
        """No persistent connection."""
        pass


class GoogleTTSAdapter(TTSAdapter):
    """Google Cloud Text-to-Speech adapter (paid, higher quality)."""

    def __init__(self, api_key: str, language_code: str = "en-IN", voice_name: str = "en-IN-Wavenet-A"):
        self.api_key = api_key
        self.language_code = language_code
        self.voice_name = voice_name

    async def synthesize_stream(self, text_stream: AsyncIterator[str]) -> AsyncIterator[bytes]:
        """Synthesize using Google Cloud TTS."""
        import aiohttp
        import base64

        buffer = ""

        async for text_chunk in text_stream:
            buffer += text_chunk

            # Process complete sentences
            sentences = buffer.split(". ")
            if len(sentences) > 1:
                for sentence in sentences[:-1]:
                    if sentence.strip():
                        audio = await self._synthesize_google(sentence + ".")
                        yield audio
                buffer = sentences[-1]

        if buffer.strip():
            audio = await self._synthesize_google(buffer)
            yield audio

    async def _synthesize_google(self, text: str) -> bytes:
        """Call Google Cloud TTS API."""
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}"

        request_body = {
            "input": {"text": text},
            "voice": {
                "languageCode": self.language_code,
                "name": self.voice_name
            },
            "audioConfig": {
                "audioEncoding": "LINEAR16",
                "sampleRateHertz": 16000
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request_body) as response:
                    data = await response.json()
                    if "audioContent" in data:
                        return base64.b64decode(data["audioContent"])
                    return b""
        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            return b""

    async def close(self):
        """No persistent connection."""
        pass
