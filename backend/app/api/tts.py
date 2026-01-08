"""
Text-to-Speech API endpoint using ElevenLabs.
Provides high-quality, natural-sounding German voices.
"""

import logging
import io
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from elevenlabs.client import ElevenLabs

from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["text-to-speech"])


# ElevenLabs voice IDs for German
ELEVENLABS_VOICES = {
    "george": "JBFqnCBsd6RMkjVDRZzb",     # George - warm, natural male
    "alice": "Xb7hH8MSUJpSbSDYk0k2",       # Alice - friendly female
    "aria": "9BWtsMINqrJLrRacOk9x",        # Aria - expressive female
    "roger": "CwhRBWXzGAHq8TQ4Fs17",       # Roger - confident male
    "sarah": "EXAVITQu4vr4xnSDxMaL",       # Sarah - soft female
}

DEFAULT_VOICE_ID = ELEVENLABS_VOICES["alice"]  # Friendly female voice


class TTSRequest(BaseModel):
    """Request model for text-to-speech."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice_id: Optional[str] = Field(default=None, description="ElevenLabs Voice ID")


def get_elevenlabs_client() -> ElevenLabs:
    """Get ElevenLabs client with API key from settings."""
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        raise HTTPException(status_code=500, detail="ElevenLabs API key not configured")
    return ElevenLabs(api_key=settings.elevenlabs_api_key)


@router.post("/speak")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using ElevenLabs.
    Returns audio as MP3 stream.
    """
    try:
        client = get_elevenlabs_client()
        voice_id = request.voice_id or DEFAULT_VOICE_ID
        
        logger.info(f"ElevenLabs TTS request: {len(request.text)} chars, voice={voice_id}")
        
        # Generate speech with ElevenLabs
        audio_generator = client.text_to_speech.convert(
            text=request.text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",  # Best for German
            output_format="mp3_44100_128",
        )
        
        # Collect audio data from generator
        audio_data = io.BytesIO()
        for chunk in audio_generator:
            audio_data.write(chunk)
        
        audio_data.seek(0)
        
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
        logger.error(f"ElevenLabs TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"Text-to-Speech failed: {str(e)}")


@router.get("/voices")
async def list_voices():
    """
    List available ElevenLabs voices.
    """
    return {
        "voices": [
            {"id": ELEVENLABS_VOICES["alice"], "name": "Alice", "description": "Freundliche weibliche Stimme", "gender": "female"},
            {"id": ELEVENLABS_VOICES["aria"], "name": "Aria", "description": "Ausdrucksstarke weibliche Stimme", "gender": "female"},
            {"id": ELEVENLABS_VOICES["sarah"], "name": "Sarah", "description": "Sanfte weibliche Stimme", "gender": "female"},
            {"id": ELEVENLABS_VOICES["george"], "name": "George", "description": "Warme männliche Stimme", "gender": "male"},
            {"id": ELEVENLABS_VOICES["roger"], "name": "Roger", "description": "Selbstbewusste männliche Stimme", "gender": "male"},
        ],
        "default": DEFAULT_VOICE_ID,
        "model": "eleven_multilingual_v2"
    }
