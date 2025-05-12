# Tests for TTS service provider handling
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.tts_service.infrastructure import ProviderNotAvailableError, VoiceNotFoundError
from src.tts_service.services.tts_service import TTSService
from src.tts_service.models import Voice, AudioResult, AudioFormat, ProviderInfo, Language


class TestTTSServiceProviderHandling:
    """Test provider handling in TTS service."""

    @pytest.fixture
    def mock_cache_manager(self):
        """Mock cache manager."""
        cache_manager = MagicMock()
        cache_manager.get = AsyncMock(return_value=None)
        cache_manager.set = AsyncMock(return_value=True)
        return cache_manager

    @pytest.fixture
    def available_provider(self):
        """Mock available provider."""
        provider = MagicMock()
        provider.is_available = AsyncMock(return_value=True)
        provider.provider_id = "available"
        provider.provider_name = "Available Provider"
        provider.get_features = MagicMock(return_value=["feature1", "feature2"])
        provider.get_voices = AsyncMock(
            return_value=[
                Voice(id="voice1", name="Voice 1", language="en", gender="female", provider="available"),
                Voice(id="voice2", name="Voice 2", language="en", gender="male", provider="available"),
            ]
        )
        provider.get_languages = AsyncMock(
            return_value=[
                Language(code="en", name="English"),
                Language(code="es", name="Spanish"),
            ]
        )
        provider.get_voice = AsyncMock(
            return_value=Voice(id="voice1", name="Voice 1", language="en", gender="female", provider="available")
        )
        provider.generate_speech = AsyncMock(
            return_value=AudioResult(
                audio_data=b"test audio",
                duration_ms=1000,
                sample_rate=24000,
                format=AudioFormat.WAV,
                meta={},
            )
        )
        return provider

    @pytest.fixture
    def unavailable_provider(self):
        """Mock unavailable provider."""
        provider = MagicMock()
        provider.is_available = AsyncMock(return_value=False)
        provider.provider_id = "unavailable"
        provider.provider_name = "Unavailable Provider"
        provider.get_features = MagicMock(return_value=[])
        return provider

    @pytest.fixture
    def failing_provider(self):
        """Mock provider that fails operations."""
        provider = MagicMock()
        provider.is_available = AsyncMock(return_value=True)
        provider.provider_id = "failing"
        provider.provider_name = "Failing Provider"
        provider.get_features = MagicMock(return_value=["feature1"])
        provider.get_voices = AsyncMock(side_effect=Exception("Provider operation failed"))
        provider.get_languages = AsyncMock(side_effect=Exception("Provider operation failed"))
        provider.get_voice = AsyncMock(side_effect=Exception("Provider operation failed"))
        provider.generate_speech = AsyncMock(side_effect=Exception("Provider operation failed"))
        return provider

    @pytest.mark.asyncio
    async def test_empty_providers(self, mock_cache_manager):
        """Test service with no providers."""
        # Create service with no providers
        service = TTSService({}, mock_cache_manager)

        # Test get_provider_info
        provider_info = await service.get_provider_info()
        assert isinstance(provider_info, list)
        assert len(provider_info) == 0

        # Test get_all_voices
        voices = await service.get_all_voices()
        assert isinstance(voices, dict)
        assert len(voices) == 0

        # Test get_languages
        languages = await service.get_languages()
        assert isinstance(languages, dict)
        assert len(languages) == 0

        # Test generate_speech
        with pytest.raises(ProviderNotAvailableError) as exc_info:
            await service.generate_speech("Test", "voice1")
        assert "No TTS providers are available" in str(exc_info.value)

        # Test get_voice
        with pytest.raises(ProviderNotAvailableError) as exc_info:
            await service.get_voice("voice1")
        assert "No TTS providers are available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_mixed_providers(
        self, mock_cache_manager, available_provider, unavailable_provider, failing_provider
    ):
        """Test service with mixed provider availability."""
        # Create service with mixed providers
        providers = {
            "available": available_provider,
            "unavailable": unavailable_provider,
            "failing": failing_provider,
        }
        service = TTSService(providers, mock_cache_manager)

        # Test get_provider_info
        provider_info = await service.get_provider_info()
        assert isinstance(provider_info, list)
        assert len(provider_info) == 3

        # Verify provider info content
        available_info = next(p for p in provider_info if p.id == "available")
        assert available_info.is_available is True
        assert available_info.voice_count == 2
        assert len(available_info.features) == 2

        unavailable_info = next(p for p in provider_info if p.id == "unavailable")
        assert unavailable_info.is_available is False
        assert unavailable_info.voice_count == 0
        assert len(unavailable_info.features) == 0

        # Test get_all_voices
        voices = await service.get_all_voices()
        assert "available" in voices
        assert len(voices["available"]) == 2
        assert "unavailable" not in voices
        assert "failing" not in voices

        # Test get_languages
        languages = await service.get_languages()
        assert "available" in languages
        assert len(languages["available"]) == 2
        assert "unavailable" not in languages
        assert "failing" not in languages

        # Test generate_speech with available provider
        result = await service.generate_speech("Test", "voice1")
        assert result.audio_data == b"test audio"
        assert result.duration_ms == 1000

        # Test get_voice with available provider
        voice = await service.get_voice("voice1")
        assert voice.id == "voice1"
        assert voice.provider == "available"

    @pytest.mark.asyncio
    async def test_all_providers_failing(self, mock_cache_manager, failing_provider):
        """Test service when all providers fail."""
        # Create service with only failing providers
        providers = {
            "failing1": failing_provider,
            "failing2": failing_provider,
        }
        service = TTSService(providers, mock_cache_manager)

        # Test get_provider_info
        provider_info = await service.get_provider_info()
        assert isinstance(provider_info, list)
        assert len(provider_info) == 2

        # Test get_all_voices
        voices = await service.get_all_voices()
        assert isinstance(voices, dict)
        assert len(voices) == 0

        # Test get_languages
        languages = await service.get_languages()
        assert isinstance(languages, dict)
        assert len(languages) == 0

        # Test generate_speech
        with pytest.raises(VoiceNotFoundError) as exc_info:
            await service.generate_speech("Test", "voice1")
        assert "not found in any available provider" in str(exc_info.value)

        # Test get_voice
        with pytest.raises(VoiceNotFoundError) as exc_info:
            await service.get_voice("voice1")
        assert "not found in any available provider" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_all_providers_unavailable(self, mock_cache_manager, unavailable_provider):
        """Test service when all providers are unavailable."""
        # Create service with only unavailable providers
        providers = {
            "unavailable1": unavailable_provider,
            "unavailable2": unavailable_provider,
        }
        service = TTSService(providers, mock_cache_manager)

        # Test get_provider_info - should return info but with is_available=False
        provider_info = await service.get_provider_info()
        assert isinstance(provider_info, list)
        assert len(provider_info) == 2
        assert all(not p.is_available for p in provider_info)

        # Test get_all_voices - should return empty dict
        voices = await service.get_all_voices()
        assert isinstance(voices, dict)
        assert len(voices) == 0

        # Test get_languages - should return empty dict
        languages = await service.get_languages()
        assert isinstance(languages, dict)
        assert len(languages) == 0

        # Test generate_speech - should fail with VoiceNotFoundError
        with pytest.raises(VoiceNotFoundError) as exc_info:
            await service.generate_speech("Test", "voice1")
        assert "not found in any available provider" in str(exc_info.value)

        # Test get_voice - should fail with VoiceNotFoundError
        with pytest.raises(VoiceNotFoundError) as exc_info:
            await service.get_voice("voice1")
        assert "not found in any available provider" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_specified_provider_not_found(self, mock_cache_manager, available_provider):
        """Test service when specified provider is not found."""
        # Create service with one provider
        providers = {
            "available": available_provider,
        }
        service = TTSService(providers, mock_cache_manager)

        # Test generate_speech with non-existent provider
        with pytest.raises(ProviderNotAvailableError) as exc_info:
            await service.generate_speech("Test", "voice1", provider_id="non_existent")
        assert "not found" in str(exc_info.value)

        # Test get_voice with non-existent provider
        with pytest.raises(ProviderNotAvailableError) as exc_info:
            await service.get_voice("voice1", provider_id="non_existent")
        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_specified_provider_unavailable(self, mock_cache_manager, unavailable_provider):
        """Test service when specified provider is unavailable."""
        # Create service with an unavailable provider
        providers = {
            "unavailable": unavailable_provider,
        }
        service = TTSService(providers, mock_cache_manager)

        # Test generate_speech with unavailable provider
        with pytest.raises(ProviderNotAvailableError) as exc_info:
            await service.generate_speech("Test", "voice1", provider_id="unavailable")
        assert "not available" in str(exc_info.value)

        # Test get_voice with unavailable provider
        with pytest.raises(ProviderNotAvailableError) as exc_info:
            await service.get_voice("voice1", provider_id="unavailable")
        assert "not available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_voice_not_found_in_any_provider(self, mock_cache_manager, available_provider):
        """Test service when voice is not found in any provider."""
        # Mock get_voice to raise VoiceNotFoundError
        available_provider.get_voice = AsyncMock(side_effect=VoiceNotFoundError("Voice not found"))

        # Create service with one provider
        providers = {
            "available": available_provider,
        }
        service = TTSService(providers, mock_cache_manager)

        # Test get_voice
        with pytest.raises(VoiceNotFoundError) as exc_info:
            await service.get_voice("non_existent_voice")
        assert "not found in any available provider" in str(exc_info.value)

        # Test generate_speech
        with pytest.raises(VoiceNotFoundError) as exc_info:
            await service.generate_speech("Test", "non_existent_voice")
        assert "not found in any available provider" in str(exc_info.value)
