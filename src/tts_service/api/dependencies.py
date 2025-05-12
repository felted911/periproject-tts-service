# API dependencies
from typing import Dict

from fastapi import Depends

from ..services import TTSService, TTSServiceProtocol
from ..providers import TTSProvider, KokoroTTSProvider
from ..infrastructure import CacheManager, get_logger
from config import settings

# Singleton instances
_cache_manager: CacheManager = None
_tts_service: TTSServiceProtocol = None
_providers: Dict[str, TTSProvider] = {}

logger = get_logger(__name__)


def get_cache_manager() -> CacheManager:
    """Get or create cache manager instance.

    Returns:
        Cache manager instance
    """
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = CacheManager(
            cache_dir=settings.CACHE_DIR,
            enabled=settings.CACHE_ENABLED,
            ttl=settings.CACHE_TTL,
            max_size=settings.MAX_CACHE_SIZE,
        )

        logger.info("Cache manager created")

    return _cache_manager


def get_kokoro_provider() -> KokoroTTSProvider:
    """Get or create Kokoro TTS provider instance.

    Returns:
        Kokoro TTS provider instance
    """
    global _providers

    if "kokoro" not in _providers:
        _providers["kokoro"] = KokoroTTSProvider(
            model_path=settings.KOKORO_SETTINGS["model_path"],
            voices_dir=settings.KOKORO_SETTINGS["voices_dir"],
            cache_dir=settings.KOKORO_SETTINGS["cache_dir"],
            default_language=settings.KOKORO_SETTINGS["default_language"],
            use_gpu=settings.KOKORO_SETTINGS["use_gpu"],
        )

        logger.info("Kokoro TTS provider created")

    return _providers["kokoro"]


def get_providers() -> Dict[str, TTSProvider]:
    """Get all TTS providers.

    Returns:
        Dictionary of provider ID to provider instance
    """
    # Ensure providers are initialized
    get_kokoro_provider()

    return _providers


def get_tts_service(
    providers: Dict[str, TTSProvider] = Depends(get_providers),
    cache_manager: CacheManager = Depends(get_cache_manager),
) -> TTSServiceProtocol:
    """Get or create TTS service instance.

    Args:
        providers: Dictionary of TTS providers
        cache_manager: Cache manager instance

    Returns:
        TTS service instance
    """
    global _tts_service

    if _tts_service is None:
        _tts_service = TTSService(
            providers=providers,
            cache_manager=cache_manager,
        )

        logger.info("TTS service created")

    return _tts_service
