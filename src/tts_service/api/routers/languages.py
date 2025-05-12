# API router for language endpoints
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from ...services import TTSService
from ...models import Language
from ...infrastructure import ProviderNotAvailableError
from ..dependencies import get_tts_service

router = APIRouter(prefix="/languages", tags=["languages"])


@router.get("/", response_model=Dict[str, List[Language]], summary="Get all supported languages")
async def get_languages(
    tts_service: TTSService = Depends(get_tts_service),
) -> Dict[str, List[Language]]:
    """Get all supported languages from all providers.

    Returns:
        Dictionary of provider ID to language list
    """
    return await tts_service.get_languages()
