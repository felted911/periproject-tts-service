# Tests for Kokoro TTS provider
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np

from src.tts_service.providers import KokoroTTSProvider
from src.tts_service.models import AudioFormat
from src.tts_service.infrastructure import VoiceNotFoundError


@pytest.fixture
def mock_kokoro():
    """Create a mock Kokoro instance."""
    mock = MagicMock()
    mock.create.return_value = (np.zeros(1000, dtype=np.float32), 24000)
    return mock


@pytest.fixture
def mock_provider(mock_kokoro):
    """Create a mock Kokoro TTS provider."""
    # First, patch the Kokoro class in the model_handler module
    with patch("src.tts_service.providers.kokoro.model_handler.Kokoro", return_value=mock_kokoro):
        # Create the provider
        provider = KokoroTTSProvider(
            model_path="mock_model_path",
            voices_dir="mock_voices_dir",
            cache_dir="mock_cache_dir",
            default_language="en-us",
            use_gpu=False,
        )

        # Mock the inner components
        provider._model_handler.initialize = AsyncMock()
        provider._model_handler._kokoro = mock_kokoro
        provider._voice_manager.load_languages = AsyncMock()
        provider._voice_manager.load_voices = AsyncMock()

        # Use private attributes instead of properties
        provider._voice_manager._voices = []
        provider._voice_manager._languages = []

        yield provider


@pytest.mark.asyncio
async def test_initialization(mock_provider):
    """Test provider initialization."""
    await mock_provider.initialize()

    # Verify initialization methods were called
    mock_provider._model_handler.initialize.assert_called_once()
    mock_provider._voice_manager.load_languages.assert_called_once()
    mock_provider._voice_manager.load_voices.assert_called_once()


@pytest.mark.asyncio
async def test_get_voices(mock_provider):
    """Test getting voices."""
    # Set up mock voices
    mock_voices = [{"id": "test_voice", "name": "Test Voice", "language": "en-us"}]
    mock_provider._voice_manager._voices = mock_voices

    # Get voices
    voices = await mock_provider.get_voices()

    # Verify result
    assert voices == mock_voices


@pytest.mark.asyncio
async def test_generate_speech(mock_provider, mock_kokoro):
    """Test speech generation."""
    # Set up mock voice
    mock_voice = MagicMock()
    mock_voice.id = "test_voice"
    mock_voice.language = "en-us"

    # Mock the voice manager to return our mock voice
    mock_provider._voice_manager.get_voice = AsyncMock(return_value=mock_voice)

    # Generate speech
    result = await mock_provider.generate_speech(
        text="Hello, world!",
        voice_id="test_voice",
        options={"speed": 1.2, "format": "wav"},
    )

    # The generate_speech method will now call _audio_generator.generate_speech
    # which eventually calls kokoro.create, so we check that
    mock_kokoro.create.assert_called_once()
    call_args = mock_kokoro.create.call_args[1]
    assert call_args["text"] == "Hello, world!"
    assert call_args["voice"] == "test_voice"
    assert call_args["speed"] == 1.2
    assert call_args["lang"] == "en-us"

    # Verify result
    assert result.format == AudioFormat.WAV
    assert result.audio_data is not None
    assert result.sample_rate == 24000


@pytest.mark.asyncio
async def test_get_voice(mock_provider):
    """Test getting a voice by ID."""
    # Set up mock voice
    mock_voice = MagicMock()
    mock_voice.id = "test_voice"

    # Mock the voice manager get_voice method
    mock_provider._voice_manager.get_voice = AsyncMock(return_value=mock_voice)

    # Get voice
    voice = await mock_provider.get_voice("test_voice")

    # Verify result
    assert voice == mock_voice
    mock_provider._voice_manager.get_voice.assert_called_once_with("test_voice")


@pytest.mark.asyncio
async def test_get_voice_not_found(mock_provider):
    """Test getting a non-existent voice."""
    # Mock the voice manager to raise an error
    mock_provider._voice_manager.get_voice = AsyncMock(side_effect=VoiceNotFoundError("Voice not found"))

    # Try to get non-existent voice
    with pytest.raises(VoiceNotFoundError):
        await mock_provider.get_voice("non_existent_voice")


@pytest.mark.asyncio
async def test_is_available(mock_provider):
    """Test checking provider availability."""
    # Set up mock model handler is_available method
    mock_provider._model_handler.is_available = AsyncMock(return_value=True)
    assert await mock_provider.is_available() is True

    # Test unavailable
    mock_provider._model_handler.is_available = AsyncMock(return_value=False)
    assert await mock_provider.is_available() is False


def test_get_features(mock_provider):
    """Test getting supported features."""
    features = mock_provider.get_features()

    # Verify result
    assert "multi_language" in features
    assert "voice_selection" in features
    assert "speed_control" in features
