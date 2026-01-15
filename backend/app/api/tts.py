"""
Text-to-Speech API endpoint using edge-tts (free) or ElevenLabs (premium).
Provides high-quality, natural-sounding German voices.
"""

import logging
import io
import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import edge_tts

from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["text-to-speech"])


# Edge-TTS German voices (free, high quality)
EDGE_TTS_VOICES = {
    "katja": "de-DE-KatjaNeural",        # Female - friendly, clear
    "conrad": "de-DE-ConradNeural",      # Male - professional
    "amala": "de-DE-AmalaNeural",        # Female - warm
    "killian": "de-DE-KillianNeural",    # Male - calm
}

DEFAULT_VOICE = EDGE_TTS_VOICES["katja"]


class TTSRequest(BaseModel):
    """Request model for text-to-speech."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice: Optional[str] = Field(default=None, description="Voice name (e.g., 'de-DE-KatjaNeural')")
    rate: Optional[str] = Field(default="+0%", description="Speech rate (e.g., '-10%', '+20%')")


@router.post("/speak")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using edge-tts (free Microsoft Azure voices).
    Returns audio as MP3 stream.
    """
    try:
        # Use provided voice or default
        voice = request.voice or DEFAULT_VOICE
        rate = request.rate or "+0%"

        logger.info(f"Edge-TTS request: {len(request.text)} chars, voice={voice}, rate={rate}")

        # Create edge-tts communicate object
        communicate = edge_tts.Communicate(
            text=request.text,
            voice=voice,
            rate=rate
        )

        # Generate speech and collect audio data
        audio_data = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.write(chunk["data"])

        audio_data.seek(0)

        if audio_data.getbuffer().nbytes == 0:
            raise HTTPException(status_code=500, detail="No audio data generated")

        return StreamingResponse(
            audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Edge-TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"Text-to-Speech failed: {str(e)}")


@router.get("/voices")
async def list_voices():
    """
    List available edge-tts German voices.
    """
    return {
        "voices": [
            {"id": "de-DE-KatjaNeural", "name": "Katja", "description": "Freundliche weibliche Stimme", "gender": "female"},
            {"id": "de-DE-AmalaNeural", "name": "Amala", "description": "Warme weibliche Stimme", "gender": "female"},
            {"id": "de-DE-ConradNeural", "name": "Conrad", "description": "Professionelle männliche Stimme", "gender": "male"},
            {"id": "de-DE-KillianNeural", "name": "Killian", "description": "Ruhige männliche Stimme", "gender": "male"},
        ],
        "default": DEFAULT_VOICE,
        "provider": "edge-tts (Microsoft Azure)"
    }
