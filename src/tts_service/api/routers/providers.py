# API router for provider endpoints
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ...services import TTSService
from ...models import ProviderInfo
from ...infrastructure import ProviderNotAvailableError
from ..dependencies import get_tts_service

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/", response_model=List[ProviderInfo], summary="Get all available providers")
async def get_providers(
    tts_service: TTSService = Depends(get_tts_service),
) -> List[ProviderInfo]:
    """Get information about all providers.
    
    Returns:
        List of provider information
    """
    return await tts_service.get_provider_info()
