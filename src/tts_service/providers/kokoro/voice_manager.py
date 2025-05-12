# Voice manager for Kokoro TTS
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from ...models import Voice, Language
from ...infrastructure import get_logger, VoiceNotFoundError, ModelLoadError
from config import settings

logger = get_logger(__name__)


class KokoroVoiceManager:
    """Manager for Kokoro TTS voices and languages."""
    
    def __init__(
        self,
        provider_id: str,
        default_language: str = settings.KOKORO_SETTINGS["default_language"],
    ):
        """Initialize the voice manager.
        
        Args:
            provider_id: Provider identifier
            default_language: Default language code
        """
        self._provider_id = provider_id
        self._default_language = default_language
        self._voices: List[Voice] = []
        self._languages: List[Language] = []
        
        # Voice metadata
        self._voice_metadata: Dict[str, Dict[str, Any]] = self._load_voice_metadata()
        
        logger.info(
            f"Kokoro voice manager initialized",
            extra={
                "provider_id": self._provider_id,
                "default_language": self._default_language,
            },
        )
    
    @property
    def voices(self) -> List[Voice]:
        """Get available voices.
        
        Returns:
            List of available voices
        """
        return self._voices
    
    @property
    def languages(self) -> List[Language]:
        """Get supported languages.
        
        Returns:
            List of supported languages
        """
        return self._languages
    
    async def get_voice(self, voice_id: str) -> Voice:
        """Get voice by ID.
        
        Args:
            voice_id: Voice identifier
            
        Returns:
            Voice
            
        Raises:
            VoiceNotFoundError: If voice not found
        """
        voice = next((v for v in self._voices if v.id == voice_id), None)
        if not voice:
            raise VoiceNotFoundError(f"Voice '{voice_id}' not found")
        return voice
    
    async def load_voices(self) -> None:
        """Load available voices.
        
        Raises:
            ModelLoadError: If voices cannot be loaded
        """
        try:
            voices = []
            
            # Load voices from metadata
            for voice_id, metadata in self._voice_metadata.items():
                language = metadata.get("language", self._default_language)
                
                voice = Voice(
                    id=voice_id,
                    name=metadata.get("name", voice_id),
                    language=language,
                    gender=metadata.get("gender", "neutral"),
                    provider=self._provider_id,
                    description=metadata.get("description", ""),
                    tags=metadata.get("tags", []),
                    meta={
                        "speaker_id": metadata.get("speaker_id", 0),
                        "language": language,
                        **metadata.get("meta", {}),
                    },
                )
                
                voices.append(voice)
            
            # Update voices
            self._voices = voices
            
            logger.info(f"Loaded {len(voices)} voices")
            
        except Exception as e:
            logger.exception(f"Failed to load voices: {str(e)}")
            raise ModelLoadError(f"Failed to load voices: {str(e)}")
    
    async def load_languages(self) -> None:
        """Load available languages.
        
        Raises:
            ModelLoadError: If languages cannot be loaded
        """
        try:
            # For simplicity, we'll use a predefined list of languages
            # In a real implementation, this would be determined from the model
            languages = [
                Language(code="en", name="English"),
                Language(code="en-us", name="English (US)"),
                Language(code="en-gb", name="English (GB)"),
                Language(code="fr", name="French"),
                Language(code="de", name="German"),
                Language(code="es", name="Spanish"),
                Language(code="it", name="Italian"),
                Language(code="ja", name="Japanese"),
                Language(code="ko", name="Korean"),
                Language(code="zh", name="Chinese"),
            ]
            
            # Update languages
            self._languages = languages
            
            logger.info(f"Loaded {len(languages)} languages")
            
        except Exception as e:
            logger.exception(f"Failed to load languages: {str(e)}")
            raise ModelLoadError(f"Failed to load languages: {str(e)}")
    
    def _load_voice_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load voice metadata from files.
        
        Returns:
            Voice metadata
        """
        # For development, use hardcoded metadata
        # In a real implementation, this would be loaded from files
        return {
            "af_alloy": {
                "name": "Alloy",
                "language": "en-us",
                "gender": "neutral",
                "description": "A versatile, neutral voice with clear articulation",
                "tags": ["neutral", "clear", "versatile"],
                "speaker_id": 0,
                "meta": {
                    "accent": "neutral",
                    "age": "adult",
                },
            },
            "af_heart": {
                "name": "Heart",
                "language": "en-us",
                "gender": "female",
                "description": "A warm, emotive female voice with natural intonation",
                "tags": ["warm", "emotive", "natural"],
                "speaker_id": 1,
                "meta": {
                    "accent": "neutral",
                    "age": "adult",
                },
            },
            "af_bella": {
                "name": "Bella",
                "language": "en-us",
                "gender": "female",
                "description": "A bright, youthful female voice with a light tone",
                "tags": ["bright", "youthful", "light"],
                "speaker_id": 2,
                "meta": {
                    "accent": "neutral",
                    "age": "young adult",
                },
            },
            "af_sarah": {
                "name": "Sarah",
                "language": "en-us",
                "gender": "female",
                "description": "A professional, authoritative female voice with clear diction",
                "tags": ["professional", "authoritative", "clear"],
                "speaker_id": 3,
                "meta": {
                    "accent": "neutral",
                    "age": "adult",
                },
            },
            "am_adam": {
                "name": "Adam",
                "language": "en-us",
                "gender": "male",
                "description": "A deep, resonant male voice with a commanding presence",
                "tags": ["deep", "resonant", "commanding"],
                "speaker_id": 4,
                "meta": {
                    "accent": "american",
                    "age": "adult",
                },
            },
        }
