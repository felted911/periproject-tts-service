# Test configuration for integration tests
import os
import sys
import asyncio
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from typing import Dict, Any, Generator
from unittest.mock import AsyncMock, MagicMock

# Add src directory to path
src_path = Path(__file__).resolve().parent.parent.parent / "src"
sys.path.insert(0, str(src_path))
project_path = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_path))

# Import after path setup
from config import settings
from src.main import app

# Import the internal module variables to directly manipulate them
from src.tts_service.api.dependencies import (
    get_cache_manager,
    get_kokoro_provider,
    get_tts_service,
    get_providers,
    _providers,
    _tts_service,
    _cache_manager,
)
from src.tts_service.api.routers.tts import get_tts_validator
from src.tts_service.infrastructure import CacheManager
from src.tts_service.providers import KokoroTTSProvider, TTSProvider
from src.tts_service.services import TTSService
from src.tts_service.api.validators.tts_validator import TTSRequestValidator
from src.tts_service.providers.kokoro.model_handler import KokoroModelHandler
from src.tts_service.providers.kokoro.voice_manager import KokoroVoiceManager
from src.tts_service.providers.kokoro.audio_generator import KokoroAudioGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session.

    This ensures a consistent event loop across all tests and prevents warnings.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_cache_dir(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return str(cache_dir)


@pytest.fixture
def test_cache_manager(test_cache_dir):
    """Create a test cache manager."""
    return CacheManager(
        cache_dir=test_cache_dir,
        enabled=True,
        ttl=3600,
        max_size=1024 * 1024 * 10,  # 10MB
    )


@pytest.fixture
def test_kokoro_provider():
    """Create a test Kokoro TTS provider with proper mocked components."""
    # Create mocked components
    model_handler = MagicMock(spec=KokoroModelHandler)
    model_handler.is_available = AsyncMock(return_value=True)

    voice_manager = MagicMock(spec=KokoroVoiceManager)
    voice_manager.voices = []
    voice_manager.languages = []
    voice_manager.get_voice = AsyncMock()

    audio_generator = MagicMock(spec=KokoroAudioGenerator)
    audio_generator.generate_speech = AsyncMock()

    # Create the provider with mocked components
    provider = KokoroTTSProvider(
        model_path="mock_model_path",
        voices_dir="mock_voices_dir",
        cache_dir="mock_cache_dir",
        default_language="en-us",
        use_gpu=False,
    )

    # Replace the internal components with our mocks
    provider._model_handler = model_handler
    provider._voice_manager = voice_manager
    provider._audio_generator = audio_generator

    # Mock key methods
    provider.is_available = AsyncMock(return_value=True)

    return provider


@pytest.fixture
def mock_providers(test_kokoro_provider):
    """Create mock providers dictionary."""
    # Create a dictionary that can be passed directly to the TTSService
    # Use the fixture as a parameter, not calling it directly
    return {"kokoro": test_kokoro_provider}


@pytest.fixture
def test_tts_service(mock_providers, test_cache_manager):
    """Create a test TTS service."""
    # Use the mock_providers dictionary directly, not a Depends object
    return TTSService(providers=mock_providers, cache_manager=test_cache_manager)


@pytest.fixture
def test_tts_validator():
    """Create a test TTS validator with fixed MAX_TEXT_LENGTH value."""
    # Use the imported TTSRequestValidator class
    return TTSRequestValidator(max_text_length=1000)  # Use a fixed value for testing


@pytest.fixture
def test_app():
    """Create a test FastAPI app without the lifespan context."""
    # Create a test version of the app without the lifespan context to avoid initialization
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from src.tts_service.api import api_router, RequestLoggerMiddleware
    from src.main import http_exception_handler, general_exception_handler
    from config import settings
    from fastapi import HTTPException

    # Create test app without lifespan
    test_app = FastAPI(
        title="Peri TTS Service Test",
        description="Test version of the TTS service",
        version="0.1.0",
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        # Ensure URLs work with or without trailing slashes
        redirect_slashes=True,
    )

    # Add CORS middleware
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request logger middleware
    test_app.add_middleware(RequestLoggerMiddleware)

    # Include API router
    test_app.include_router(api_router, prefix=settings.API_PREFIX)

    # Add error handlers
    test_app.exception_handler(HTTPException)(http_exception_handler)
    test_app.exception_handler(Exception)(general_exception_handler)

    # Add health check endpoint
    @test_app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return test_app


@pytest.fixture
def client(
    test_tts_service,
    test_cache_manager,
    test_kokoro_provider,
    test_tts_validator,
    mock_providers,
    monkeypatch,
    test_app,
):
    """Create a test client."""
    # Set the global singleton instances directly
    global _providers, _tts_service, _cache_manager
    _providers = mock_providers
    _tts_service = test_tts_service
    _cache_manager = test_cache_manager

    # Ensure app has redirect_slashes enabled for trailing slash handling
    test_app.redirect_slashes = True

    # Override dependencies for testing
    async def override_get_cache_manager():
        return test_cache_manager

    async def override_get_kokoro_provider():
        return test_kokoro_provider

    # Important: Return the actual dictionary, not a Depends object
    def override_get_providers():
        return mock_providers

    async def override_get_tts_service():
        return test_tts_service

    # Important: Must be in sync function since the original is sync
    def override_get_tts_validator():
        return test_tts_validator

    # Clear any previous overrides that might be lingering
    test_app.dependency_overrides.clear()

    # Register all the overrides
    test_app.dependency_overrides[get_cache_manager] = override_get_cache_manager
    test_app.dependency_overrides[get_kokoro_provider] = override_get_kokoro_provider
    test_app.dependency_overrides[get_providers] = override_get_providers
    test_app.dependency_overrides[get_tts_service] = override_get_tts_service
    test_app.dependency_overrides[get_tts_validator] = override_get_tts_validator

    # Set up FastAPI test client without lifespan events
    client = TestClient(test_app, raise_server_exceptions=False)

    # Return the client
    yield client

    # Clean up
    test_app.dependency_overrides.clear()
