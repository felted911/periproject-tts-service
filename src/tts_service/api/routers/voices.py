# API router for voice endpoints
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from ...services import TTSService
from ...models import Voice
from ...infrastructure import VoiceNotFoundError, ProviderNotAvailableError, get_logger
from ..dependencies import get_tts_service

router = APIRouter(prefix="/voices", tags=["voices"])
logger = get_logger(__name__)


@router.get("/", response_model=Dict[str, List[Voice]], summary="Get all available voices")
async def get_voices(
    tts_service: TTSService = Depends(get_tts_service),
) -> Dict[str, List[Voice]]:
    """Get all available voices from all providers.

    Returns:
        Dictionary of provider ID to voice list
    """
    return await tts_service.get_all_voices()


@router.get("/{voice_id}", response_model=Voice, summary="Get voice by ID")
async def get_voice(
    voice_id: str,
    provider_id: str = None,
    tts_service: TTSService = Depends(get_tts_service),
) -> Voice:
    """Get voice by ID.

    Args:
        voice_id: Voice ID
        provider_id: Provider ID (optional)

    Returns:
        Voice

    Raises:
        HTTPException: If voice not found or provider not available
    """
    try:
        return await tts_service.get_voice(voice_id, provider_id)
    except VoiceNotFoundError as e:
        # Log the error for debugging
        logger.error(f"Voice not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ProviderNotAvailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
