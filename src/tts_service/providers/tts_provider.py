# Protocol for TTS providers
from typing import List, Dict, Any, Protocol, Optional

from ..models import Voice, Language, AudioResult


class TTSProvider(Protocol):
    """Interface for TTS providers."""

    @property
    def provider_id(self) -> str:
        """Get provider identifier."""
        ...

    @property
    def provider_name(self) -> str:
        """Get provider display name."""
        ...

    async def initialize(self) -> None:
        """Initialize the provider."""
        ...

    async def get_voices(self) -> List[Voice]:
        """Get available voices."""
        ...

    async def get_languages(self) -> List[Language]:
        """Get supported languages."""
        ...

    async def generate_speech(self, text: str, voice_id: str, options: Optional[Dict[str, Any]] = None) -> AudioResult:
        """Generate speech from text.

        Args:
            text: Text to convert to speech
            voice_id: Voice identifier
            options: Additional options

        Returns:
            Audio result

        Raises:
            VoiceNotFoundError: If voice not found
            GenerationFailedError: If speech generation fails
        """
        ...

    async def get_voice(self, voice_id: str) -> Voice:
        """Get voice by ID.

        Args:
            voice_id: Voice identifier

        Returns:
            Voice

        Raises:
            VoiceNotFoundError: If voice not found
        """
        ...

    async def is_available(self) -> bool:
        """Check if provider is available.

        Returns:
            True if available, False otherwise
        """
        ...

    def get_features(self) -> List[str]:
        """Get supported features.

        Returns:
            List of supported features
        """
        ...
