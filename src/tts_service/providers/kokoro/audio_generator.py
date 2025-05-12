# Audio generator for Kokoro TTS
import io
import os
import soundfile as sf
from typing import Dict, Any, Optional, Tuple, cast

# Add parent directory to path for imports
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from ...models import AudioResult, AudioFormat, Voice
from ...infrastructure import get_logger, GenerationFailedError, VoiceNotFoundError
from .model_handler import KokoroModelHandler
from .voice_manager import KokoroVoiceManager
from config import settings

logger = get_logger(__name__)


class KokoroAudioGenerator:
    """Generator for Kokoro TTS audio."""

    def __init__(
        self,
        model_handler: KokoroModelHandler,
        voice_manager: KokoroVoiceManager,
        sample_rate: int = settings.KOKORO_SETTINGS["sampling_rate"],
    ):
        """Initialize the audio generator.

        Args:
            model_handler: Kokoro model handler
            voice_manager: Voice manager
            sample_rate: Audio sample rate
        """
        self._model_handler = model_handler
        self._voice_manager = voice_manager
        self._sample_rate = sample_rate

        logger.info(
            f"Kokoro audio generator initialized",
            extra={
                "sample_rate": self._sample_rate,
            },
        )

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
        try:
            # Get voice
            voice = await self._voice_manager.get_voice(voice_id)

            # Get options
            options = options or {}
            speed = float(options.get("speed", 1.0))
            format_str = options.get("format", "wav")
            audio_format = AudioFormat(format_str)
            language = options.get("language", voice.language)

            # Ensure model is initialized
            if not self._model_handler.is_initialized:
                await self._model_handler.initialize()

            # Generate speech
            logger.debug(
                f"Generating speech",
                extra={
                    "text_length": len(text),
                    "voice_id": voice_id,
                    "speed": speed,
                    "format": format_str,
                },
            )

            # Generate the audio data
            audio_data, sample_rate = await self._generate_audio_data(
                text=text, voice_id=voice_id, speed=speed, language=language
            )

            # Calculate duration in milliseconds
            duration_ms = int(len(audio_data) / sample_rate * 1000)

            # Convert to the requested format
            audio_bytes, actual_format = self.convert_audio_format(audio_data, sample_rate, audio_format)

            logger.debug(
                f"Speech generated successfully",
                extra={
                    "duration_ms": duration_ms,
                    "audio_size": len(audio_bytes),
                    "sample_rate": sample_rate,
                    "format": actual_format.value,
                },
            )

            # Return result
            return AudioResult(
                audio_data=audio_bytes,
                duration_ms=duration_ms,
                sample_rate=sample_rate,
                format=actual_format,
                meta={
                    "voice_id": voice_id,
                    "speed": speed,
                    "text_length": len(text),
                },
            )

        except VoiceNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Failed to generate speech: {str(e)}")
            raise GenerationFailedError(f"Failed to generate speech: {str(e)}")

    async def _generate_audio_data(
        self, text: str, voice_id: str, speed: float = 1.0, language: str = "en-us"
    ) -> Tuple[Any, int]:
        """Generate audio data.

        Args:
            text: Text to convert to speech
            voice_id: Voice identifier
            speed: Speech speed
            language: Language code

        Returns:
            Tuple of audio data and sample rate

        Raises:
            GenerationFailedError: If speech generation fails
        """
        try:
            # Convert language code to standard format
            lang_code = self._normalize_language_code(language)

            # Generate speech
            kokoro = self._model_handler.model
            if kokoro is None:
                raise GenerationFailedError("Kokoro model not initialized")

            audio_data, sample_rate = kokoro.create(text=text, voice=voice_id, speed=speed, lang=lang_code)

            return audio_data, sample_rate

        except Exception as e:
            logger.exception(f"Failed to generate audio data: {str(e)}")
            raise GenerationFailedError(f"Failed to generate audio data: {str(e)}")

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
        # Convert to WAV format directly using soundfile
        with io.BytesIO() as wav_buffer:
            sf.write(wav_buffer, audio_data, sample_rate, format="WAV")
            wav_buffer.seek(0)
            audio_bytes = wav_buffer.read()

        # For now, we only support WAV format directly
        # Other formats would require external libraries (ffmpeg)
        if target_format != AudioFormat.WAV:
            logger.warning(
                f"Requested format {target_format.value} not supported without ffmpeg. Returning WAV format instead."
            )
            target_format = AudioFormat.WAV

        return audio_bytes, target_format

    def _normalize_language_code(self, language: str) -> str:
        """Normalize language code.

        Args:
            language: Language code

        Returns:
            Normalized language code
        """
        lang_code = language.lower()
        if "-" not in lang_code:
            # Default to US English if no region specified
            if lang_code == "en":
                lang_code = "en-us"
            # Other languages might need similar treatment

        return lang_code
