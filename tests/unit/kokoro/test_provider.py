# Tests for refactored Kokoro TTS provider
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np

from src.tts_service.providers import KokoroTTSProvider
from src.tts_service.providers.kokoro import KokoroVoiceManager, KokoroModelHandler, KokoroAudioGenerator
from src.tts_service.models import Voice, Language, AudioFormat, AudioResult
from src.tts_service.infrastructure import VoiceNotFoundError, ModelLoadError, GenerationFailedError


@pytest.fixture
def mock_model_handler():
    """Create a mock Kokoro model handler."""
    mock = MagicMock(spec=KokoroModelHandler)
    mock.is_initialized = False
    mock.initialize = AsyncMock()
    mock.is_available = AsyncMock(return_value=True)

    # Create mock Kokoro model
    mock_kokoro = MagicMock()
    mock_kokoro.create.return_value = (np.zeros(1000, dtype=np.float32), 24000)
    mock.model = mock_kokoro

    return mock


@pytest.fixture
def mock_voice_manager():
    """Create a mock Kokoro voice manager."""
    mock = MagicMock(spec=KokoroVoiceManager)
    mock.load_languages = AsyncMock()
    mock.load_voices = AsyncMock()

    # Create mock voices
    test_voice = Voice(
        id="test_voice",
        name="Test Voice",
        language="en-us",
        gender="neutral",
        provider="kokoro",
        description="Test voice for Kokoro TTS",
        tags=["test"],
        meta={},
    )
    mock.voices = [test_voice]

    # Create mock languages
    test_language = Language(code="en-us", name="English (US)")
    mock.languages = [test_language]

    # Setup get_voice mock
    mock.get_voice = AsyncMock()
    mock.get_voice.return_value = test_voice

    return mock


@pytest.fixture
def mock_audio_generator(mock_model_handler, mock_voice_manager):
    """Create a mock Kokoro audio generator."""
    mock = MagicMock(spec=KokoroAudioGenerator)

    # Setup generate_speech mock
    mock.generate_speech = AsyncMock()
    mock.generate_speech.return_value = AudioResult(
        audio_data=b"dummy audio data",
        duration_ms=1000,
        sample_rate=24000,
        format=AudioFormat.WAV,
        meta={"voice_id": "test_voice", "speed": 1.0, "text_length": 12},
    )

    return mock


@pytest.fixture
def mock_provider(mock_model_handler, mock_voice_manager, mock_audio_generator):
    """Create a mock refactored Kokoro TTS provider."""
    with patch("src.tts_service.providers.kokoro.provider.KokoroModelHandler", return_value=mock_model_handler):
        with patch("src.tts_service.providers.kokoro.provider.KokoroVoiceManager", return_value=mock_voice_manager):
            with patch(
                "src.tts_service.providers.kokoro.provider.KokoroAudioGenerator", return_value=mock_audio_generator
            ):
                provider = KokoroTTSProvider(
                    model_path="mock_model_path",
                    voices_dir="mock_voices_dir",
                    cache_dir="mock_cache_dir",
                    default_language="en-us",
                    use_gpu=False,
                )
                provider._model_handler = mock_model_handler
                provider._voice_manager = mock_voice_manager
                provider._audio_generator = mock_audio_generator
                yield provider


@pytest.mark.asyncio
async def test_initialization(mock_provider, mock_model_handler, mock_voice_manager):
    """Test provider initialization."""
    await mock_provider.initialize()

    # Verify initialization methods were called
    mock_model_handler.initialize.assert_called_once()
    mock_voice_manager.load_languages.assert_called_once()
    mock_voice_manager.load_voices.assert_called_once()


@pytest.mark.asyncio
async def test_get_voices(mock_provider, mock_voice_manager):
    """Test getting voices."""
    # Get voices
    voices = await mock_provider.get_voices()

    # Verify result
    assert voices == mock_voice_manager.voices
    assert len(voices) == 1
    assert voices[0].id == "test_voice"


@pytest.mark.asyncio
async def test_get_languages(mock_provider, mock_voice_manager):
    """Test getting languages."""
    # Get languages
    languages = await mock_provider.get_languages()

    # Verify result
    assert languages == mock_voice_manager.languages
    assert len(languages) == 1
    assert languages[0].code == "en-us"


@pytest.mark.asyncio
async def test_generate_speech(mock_provider, mock_audio_generator):
    """Test speech generation."""
    # Generate speech
    result = await mock_provider.generate_speech(
        text="Hello, world!",
        voice_id="test_voice",
        options={"speed": 1.2, "format": "wav"},
    )

    # Verify audio generator was called with correct parameters
    mock_audio_generator.generate_speech.assert_called_once_with(
        text="Hello, world!",
        voice_id="test_voice",
        options={"speed": 1.2, "format": "wav"},
    )

    # Verify result
    assert result.format == AudioFormat.WAV
    assert result.audio_data is not None
    assert result.duration_ms == 1000
    assert result.sample_rate == 24000
    assert result.meta["voice_id"] == "test_voice"


@pytest.mark.asyncio
async def test_get_voice(mock_provider, mock_voice_manager):
    """Test getting a voice by ID."""
    # Get voice
    voice = await mock_provider.get_voice("test_voice")

    # Verify voice manager's get_voice was called
    mock_voice_manager.get_voice.assert_called_once_with("test_voice")

    # Verify result
    assert voice.id == "test_voice"
    assert voice.name == "Test Voice"


@pytest.mark.asyncio
async def test_get_voice_not_found(mock_provider, mock_voice_manager):
    """Test getting a non-existent voice."""
    # Setup mock to raise VoiceNotFoundError
    mock_voice_manager.get_voice.side_effect = VoiceNotFoundError("Voice 'non_existent_voice' not found")

    # Try to get non-existent voice
    with pytest.raises(VoiceNotFoundError):
        await mock_provider.get_voice("non_existent_voice")


@pytest.mark.asyncio
async def test_is_available(mock_provider, mock_model_handler):
    """Test checking provider availability."""
    # Test is_available
    availability = await mock_provider.is_available()

    # Verify model handler's is_available was called
    mock_model_handler.is_available.assert_called_once()

    # Verify result
    assert availability is True


def test_get_features(mock_provider):
    """Test getting supported features."""
    features = mock_provider.get_features()

    # Verify result
    assert "multi_language" in features
    assert "voice_selection" in features
    assert "speed_control" in features
