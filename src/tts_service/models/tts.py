# TTS models for the service
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum

from .voice import Voice


class AudioFormat(str, Enum):
    """Supported audio formats."""

    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"


class TTSRequest(BaseModel):
    """Model for TTS request."""

    text: str = Field(..., description="Text to convert to speech", min_length=1)
    voice: str = Field(..., description="Voice ID to use")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional TTS options")
    format: AudioFormat = Field(default=AudioFormat.WAV, description="Output audio format")

    @validator("text")
    def validate_text_length(cls, v: str) -> str:
        """Validate text length."""
        from config.settings import MAX_TEXT_LENGTH

        if len(v) > MAX_TEXT_LENGTH:
            raise ValueError(f"Text length exceeds maximum of {MAX_TEXT_LENGTH} characters")
        return v


class TTSResponse(BaseModel):
    """Model for TTS response."""

    audio_url: str = Field(..., description="URL to the generated audio file")
    duration_ms: int = Field(..., description="Audio duration in milliseconds")
    text: str = Field(..., description="Text that was converted to speech")
    voice: Voice = Field(..., description="Voice used for synthesis")
    format: AudioFormat = Field(..., description="Audio format")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AudioResult(BaseModel):
    """Model for audio generation result."""

    audio_data: bytes = Field(..., description="Raw audio data")
    duration_ms: int = Field(..., description="Audio duration in milliseconds")
    sample_rate: int = Field(..., description="Audio sample rate in Hz")
    format: AudioFormat = Field(..., description="Audio format")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ProviderInfo(BaseModel):
    """Model for TTS provider information."""

    id: str = Field(..., description="Provider identifier")
    name: str = Field(..., description="Provider display name")
    description: Optional[str] = Field(None, description="Provider description")
    voice_count: int = Field(..., description="Number of available voices")
    features: List[str] = Field(default_factory=list, description="Supported features")
    is_available: bool = Field(True, description="Whether the provider is currently available")
