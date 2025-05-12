# Voice models for the TTS service
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Voice(BaseModel):
    """Model representing a TTS voice."""
    
    id: str = Field(..., description="Unique identifier for the voice")
    name: str = Field(..., description="Display name for the voice")
    language: str = Field(..., description="Language code (e.g., 'en-US')")
    gender: str = Field(..., description="Voice gender (e.g., 'male', 'female', 'neutral')")
    provider: str = Field(..., description="TTS provider name")
    description: Optional[str] = Field(None, description="Voice description")
    tags: List[str] = Field(default_factory=list, description="Voice tags (e.g., 'casual', 'formal')")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional voice metadata")
    
    class Config:
        """Pydantic model configuration."""
        frozen = True


class Language(BaseModel):
    """Model representing a supported language."""
    
    code: str = Field(..., description="Language code (e.g., 'en-US')")
    name: str = Field(..., description="Language name (e.g., 'English (US)')")
    is_available: bool = Field(True, description="Whether the language is currently available")


class VoiceList(BaseModel):
    """Model representing a list of voices."""
    
    voices: List[Voice] = Field(..., description="List of available voices")
    provider: str = Field(..., description="TTS provider name")
    count: int = Field(..., description="Number of voices")
    
    @classmethod
    def from_voices(cls, voices: List[Voice], provider: str) -> "VoiceList":
        """Create a VoiceList from a list of voices."""
        return cls(
            voices=voices,
            provider=provider,
            count=len(voices)
        )
