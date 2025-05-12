# Main Kokoro TTS provider implementation
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from ...models import Voice, Language, AudioResult
from ...infrastructure import get_logger, VoiceNotFoundError, ModelLoadError, GenerationFailedError
from .model_handler import KokoroModelHandler
from .voice_manager import KokoroVoiceManager
from .audio_generator import KokoroAudioGenerator
from config import settings

logger = get_logger(__name__)


class KokoroTTSProvider:
    """Kokoro TTS implementation of TTSProvider."""
    
    def __init__(
        self,
        model_path: str = settings.KOKORO_SETTINGS["model_path"],
        voices_dir: str = settings.KOKORO_SETTINGS["voices_dir"],
        cache_dir: str = settings.KOKORO_SETTINGS["cache_dir"],
        default_language: str = settings.KOKORO_SETTINGS["default_language"],
        use_gpu: bool = settings.KOKORO_SETTINGS["use_gpu"],
    ):
        """Initialize Kokoro TTS provider.
        
        Args:
            model_path: Path to models directory
            voices_dir: Path to voices directory
            cache_dir: Path to cache directory
            default_language: Default language code
            use_gpu: Whether to use GPU
        """
        # Ensure cache directory exists
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Create component instances
        self._model_handler = KokoroModelHandler(
            model_path=model_path,
            voices_dir=voices_dir,
            use_gpu=use_gpu
        )
        
        self._voice_manager = KokoroVoiceManager(
            provider_id=self.provider_id,
            default_language=default_language
        )
        
        self._audio_generator = KokoroAudioGenerator(
            model_handler=self._model_handler,
            voice_manager=self._voice_manager,
            sample_rate=settings.KOKORO_SETTINGS["sampling_rate"]
        )
        
        logger.info(
            f"Kokoro TTS provider initialized",
            extra={
                "model_path": model_path,
                "voices_dir": voices_dir,
                "cache_dir": str(self._cache_dir),
                "default_language": default_language,
                "use_gpu": use_gpu,
            },
        )
    
    @property
    def provider_id(self) -> str:
        """Get provider identifier."""
        return "kokoro"
    
    @property
    def provider_name(self) -> str:
        """Get provider display name."""
        return "Kokoro TTS"
    
    async def initialize(self) -> None:
        """Initialize the provider.
        
        Raises:
            ModelLoadError: If model cannot be loaded
        """
        try:
            # Initialize model
            await self._model_handler.initialize()
            
            # Load available languages
            await self._voice_manager.load_languages()
            
            # Load available voices
            await self._voice_manager.load_voices()
            
            logger.info(
                f"Kokoro TTS provider initialized successfully",
                extra={
                    "voices": len(await self.get_voices()),
                    "languages": len(await self.get_languages()),
                },
            )
            
        except Exception as e:
            logger.exception(f"Failed to initialize Kokoro TTS provider: {str(e)}")
            raise ModelLoadError(f"Failed to initialize Kokoro TTS provider: {str(e)}")
    
    async def get_voices(self) -> List[Voice]:
        """Get available voices.
        
        Returns:
            List of available voices
        """
        return self._voice_manager.voices
    
    async def get_languages(self) -> List[Language]:
        """Get supported languages.
        
        Returns:
            List of supported languages
        """
        return self._voice_manager.languages
    
    async def generate_speech(
        self, 
        text: str, 
        voice_id: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> AudioResult:
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
            # Use the audio generator to generate speech
            return await self._audio_generator.generate_speech(
                text=text,
                voice_id=voice_id,
                options=options
            )
        except VoiceNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Failed to generate speech: {str(e)}")
            raise GenerationFailedError(f"Failed to generate speech: {str(e)}")
    
    async def get_voice(self, voice_id: str) -> Voice:
        """Get voice by ID.
        
        Args:
            voice_id: Voice identifier
            
        Returns:
            Voice
            
        Raises:
            VoiceNotFoundError: If voice not found
        """
        return await self._voice_manager.get_voice(voice_id)
    
    async def is_available(self) -> bool:
        """Check if provider is available.
        
        Returns:
            True if available, False otherwise
        """
        return await self._model_handler.is_available()
    
    def get_features(self) -> List[str]:
        """Get supported features.
        
        Returns:
            List of supported features
        """
        return [
            "multi_language",
            "voice_selection",
            "speed_control",
        ]
