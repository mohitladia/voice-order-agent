"""
Google Speech-to-Text adapter (free tier: 60 minutes/month).
"""
import asyncio
import json
import websockets
from typing import AsyncIterator, Dict, Any
from app.adapters.base import STTAdapter
import logging

logger = logging.getLogger(__name__)


class GoogleSTTAdapter(STTAdapter):
    """Google Cloud Speech-to-Text adapter (streaming)."""

    def __init__(self, api_key: str, language_code: str = "en-IN"):
        self.api_key = api_key
        self.language_code = language_code
        self.websocket = None

    async def transcribe_stream(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[str]:
        """
        Transcribe audio using Google Speech-to-Text streaming API.

        Google free tier: 60 minutes/month
        """
        try:
            # Connect to Google Speech-to-Text streaming API
            uri = f"wss://speech.googleapis.com/v1/speech:streamingRecognize?key={self.api_key}"

            async with websockets.connect(uri) as websocket:
                self.websocket = websocket

                # Send config
                config_msg = {
                    "streamingConfig": {
                        "config": {
                            "encoding": "LINEAR16",
                            "sampleRateHertz": 16000,
                            "languageCode": self.language_code,
                            "enableAutomaticPunctuation": True
                        },
                        "singleUtterance": True,
                        "interimResults": True
                    }
                }
                await websocket.send(json.dumps(config_msg))

                # Audio streaming
                async for audio_chunk in audio_stream:
                    audio_msg = {"audioContent": audio_chunk.hex()}
                    await websocket.send(json.dumps(audio_msg))

                # Signal end of audio
                await websocket.send(json.dumps({}))

                # Receive transcriptions
                async for response in websocket:
                    if response:
                        data = json.loads(response)
                        if "results" in data:
                            for result in data["results"]:
                                if "alternatives" in result:
                                    transcript = result["alternatives"][0]["transcript"]
                                    if transcript:
                                        yield transcript

        except Exception as e:
            logger.error(f"Google STT error: {e}")
            raise

    async def close(self):
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()


class GoogleSTTSyncAdapter(STTAdapter):
    """Fallback: Google STT using REST API (simpler, slower)."""

    def __init__(self, api_key: str, language_code: str = "en-IN"):
        self.api_key = api_key
        self.language_code = language_code

    async def transcribe_stream(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[str]:
        """
        Non-streaming transcription using REST API.
        Collects all audio then transcribes.
        """
        import aiohttp
        import base64

        # Collect all audio
        audio_data = b""
        async for chunk in audio_stream:
            audio_data += chunk

        if not audio_data:
            yield ""
            return

        # Convert to base64
        audio_content = base64.b64encode(audio_data).decode("utf-8")

        # Prepare request
        request_data = {
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": 16000,
                "languageCode": self.language_code,
                "enableAutomaticPunctuation": True
            },
            "audio": {
                "content": audio_content
            }
        }

        # Send request
        url = f"https://speech.googleapis.com/v1/speech:recognize?key={self.api_key}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request_data) as response:
                    data = await response.json()

                    if "results" in data:
                        for result in data["results"]:
                            if "alternatives" in result:
                                transcript = result["alternatives"][0]["transcript"]
                                yield transcript

        except Exception as e:
            logger.error(f"Google STT REST error: {e}")
            yield ""

    async def close(self):
        """No persistent connection to close."""
        pass
