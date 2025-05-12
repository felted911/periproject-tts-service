# Module initialization for API
from .routers import api_router
from .middleware import RequestLoggerMiddleware
from .dependencies import (
    get_cache_manager,
    get_kokoro_provider,
    get_providers,
    get_tts_service,
)

__all__ = [
    "api_router",
    "RequestLoggerMiddleware",
    "get_cache_manager",
    "get_kokoro_provider",
    "get_providers",
    "get_tts_service",
]
