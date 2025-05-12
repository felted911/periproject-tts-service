# Module initialization for routers
from fastapi import APIRouter

from .voices import router as voices_router
from .tts import router as tts_router
from .languages import router as languages_router
from .providers import router as providers_router

api_router = APIRouter()

# Include all routers
api_router.include_router(voices_router)
api_router.include_router(tts_router)
api_router.include_router(languages_router)
api_router.include_router(providers_router)

__all__ = [
    "api_router",
]
