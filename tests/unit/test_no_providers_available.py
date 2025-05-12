# Tests for handling no available providers
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.tts_service.infrastructure import ProviderNotAvailableError, VoiceNotFoundError
from src.tts_service.services.tts_service import TTSService
from src.tts_service.models import Voice


@pytest.mark.asyncio
async def test_get_provider_info_no_providers():
    """Test get_provider_info when no providers are available."""
    # Create empty providers dictionary
    providers = {}
    
    # Create mock cache manager
    cache_manager = MagicMock()
    cache_manager.get = AsyncMock(return_value=None)
    cache_manager.set = AsyncMock(return_value=True)
    
    # Create service with no providers
    service = TTSService(providers, cache_manager)
    
    # Call get_provider_info
    provider_info = await service.get_provider_info()
    
    # Verify empty result list is returned instead of error
    assert isinstance(provider_info, list)
    assert len(provider_info) == 0


@pytest.mark.asyncio
async def test_get_provider_info_unavailable_providers():
    """Test get_provider_info when all providers are unavailable."""
    # Create mock provider
    mock_provider = MagicMock()
    mock_provider.is_available = AsyncMock(return_value=False)
    mock_provider.provider_name = "Mock Provider"
    mock_provider.get_features = MagicMock(return_value=[])
    
    # Create providers dictionary with mock provider
    providers = {"mock": mock_provider}
    
    # Create mock cache manager
    cache_manager = MagicMock()
    cache_manager.get = AsyncMock(return_value=None)
    cache_manager.set = AsyncMock(return_value=True)
    
    # Create service with mock provider
    service = TTSService(providers, cache_manager)
    
    # Call get_provider_info
    provider_info = await service.get_provider_info()
    
    # Verify provider info is returned
    assert isinstance(provider_info, list)
    assert len(provider_info) == 1
    assert provider_info[0].id == "mock"
    assert provider_info[0].name == "Mock Provider"
    assert provider_info[0].is_available is False


@pytest.mark.asyncio
async def test_get_languages_no_providers():
    """Test get_languages when no providers are available."""
    # Create empty providers dictionary
    providers = {}
    
    # Create mock cache manager
    cache_manager = MagicMock()
    
    # Create service with no providers
    service = TTSService(providers, cache_manager)
    
    # Call get_languages
    languages = await service.get_languages()
    
    # Verify empty result is returned
    assert isinstance(languages, dict)
    assert len(languages) == 0


@pytest.mark.asyncio
async def test_generate_speech_no_providers():
    """Test generate_speech when no providers are available."""
    # Create empty providers dictionary
    providers = {}
    
    # Create mock cache manager
    cache_manager = MagicMock()
    cache_manager.get = AsyncMock(return_value=None)
    
    # Create service with no providers
    service = TTSService(providers, cache_manager)
    
    # Call generate_speech
    with pytest.raises(ProviderNotAvailableError) as exc_info:
        await service.generate_speech("Hello world", "test_voice")
    
    # Verify appropriate error message
    assert "No TTS providers are available in the system" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_voice_no_providers():
    """Test get_voice when no providers are available."""
    # Create empty providers dictionary
    providers = {}
    
    # Create mock cache manager
    cache_manager = MagicMock()
    
    # Create service with no providers
    service = TTSService(providers, cache_manager)
    
    # Call get_voice
    with pytest.raises(ProviderNotAvailableError) as exc_info:
        await service.get_voice("test_voice")
    
    # Verify appropriate error message
    assert "No TTS providers are available in the system" in str(exc_info.value)
