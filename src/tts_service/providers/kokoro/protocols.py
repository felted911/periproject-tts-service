# Protocol interfaces for Kokoro TTS provider components
from typing import Dict, List, Any, Protocol, Optional, Tuple
from pathlib import Path

from ...models import Voice, Language, AudioResult, AudioFormat


class KokoroVoiceManagerProtocol(Protocol):
    """Interface for managing Kokoro TTS voices."""

    @property
    def voices(self) -> List[Voice]:
        """Get available voices."""
        ...

    @property
    def languages(self) -> List[Language]:
        """Get supported languages."""
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

    async def load_voices(self) -> None:
        """Load available voices.

        Raises:
            ModelLoadError: If voices cannot be loaded
        """
        ...

    async def load_languages(self) -> None:
        """Load available languages.

        Raises:
            ModelLoadError: If languages cannot be loaded
        """
        ...


class KokoroModelHandlerProtocol(Protocol):
    """Interface for handling Kokoro TTS models."""

    @property
    def model(self) -> Any:
        """Get Kokoro model instance."""
        ...

    @property
    def is_initialized(self) -> bool:
        """Check if model is initialized."""
        ...

    async def initialize(self) -> None:
        """Initialize Kokoro model.

        Raises:
            ModelLoadError: If model cannot be initialized
        """
        ...

    async def is_available(self) -> bool:
        """Check if Kokoro is available."""
        ...


class KokoroAudioGeneratorProtocol(Protocol):
    """Interface for generating audio with Kokoro TTS."""

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

    def convert_audio_format(
        self, audio_data: Any, sample_rate: int, target_format: AudioFormat = AudioFormat.WAV
    ) -> Tuple[bytes, AudioFormat]:
        """Convert audio to the specified format.

        Args:
            audio_data: Audio data
            sample_rate: Sample rate
            target_format: Target audio format

        Returns:
            Tuple of audio bytes and format
        """
        ...
