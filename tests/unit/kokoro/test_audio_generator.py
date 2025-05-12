# Tests for Kokoro audio generator
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np
import io
import soundfile as sf

from src.tts_service.providers.kokoro import (
    KokoroAudioGenerator,
    KokoroModelHandler,
    KokoroVoiceManager
)
from src.tts_service.models import Voice, AudioFormat
from src.tts_service.infrastructure import VoiceNotFoundError, GenerationFailedError


@pytest.fixture
def mock_model_handler():
    """Create a mock Kokoro model handler."""
    mock = MagicMock(spec=KokoroModelHandler)
    mock.is_initialized = True
    mock.initialize = AsyncMock()
    
    # Create mock Kokoro model
    mock_kokoro = MagicMock()
    # Generate a sine wave as audio data
    sample_rate = 24000
    duration = 0.5  # 500ms
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * 440 * t) * 0.3
    mock_kokoro.create.return_value = (audio_data.astype(np.float32), sample_rate)
    mock.model = mock_kokoro
    
    return mock


@pytest.fixture
def mock_voice_manager():
    """Create a mock Kokoro voice manager."""
    mock = MagicMock(spec=KokoroVoiceManager)
    
    # Create mock voice
    test_voice = Voice(
        id="test_voice",
        name="Test Voice",
        language="en-us",
        gender="neutral",
        provider="kokoro",
        description="Test voice for Kokoro TTS",
        tags=["test"],
        meta={}
    )
    
    # Setup get_voice mock
    mock.get_voice = AsyncMock()
    mock.get_voice.return_value = test_voice
    
    return mock


@pytest.fixture
def audio_generator(mock_model_handler, mock_voice_manager):
    """Create an audio generator with mock components."""
    generator = KokoroAudioGenerator(
        model_handler=mock_model_handler,
        voice_manager=mock_voice_manager,
        sample_rate=24000
    )
    return generator


@pytest.mark.asyncio
async def test_initialization(mock_model_handler, mock_voice_manager):
    """Test audio generator initialization."""
    generator = KokoroAudioGenerator(
        model_handler=mock_model_handler,
        voice_manager=mock_voice_manager,
        sample_rate=24000
    )
    
    # Check initial state
    assert generator._model_handler == mock_model_handler
    assert generator._voice_manager == mock_voice_manager
    assert generator._sample_rate == 24000


@pytest.mark.asyncio
async def test_generate_speech_success(audio_generator, mock_model_handler, mock_voice_manager):
    """Test successful speech generation."""
    # Generate speech
    result = await audio_generator.generate_speech(
        text="Hello, world!",
        voice_id="test_voice",
        options={"speed": 1.2, "format": "wav"}
    )
    
    # Verify model handler and voice manager were called
    mock_voice_manager.get_voice.assert_called_once_with("test_voice")
    
    # Verify Kokoro.create was called with correct parameters
    mock_model_handler.model.create.assert_called_once_with(
        text="Hello, world!",
        voice="test_voice",
        speed=1.2,
        lang="en-us"
    )
    
    # Verify result
    assert result.format == AudioFormat.WAV
    assert result.audio_data is not None
    assert result.sample_rate == 24000
    assert result.meta["voice_id"] == "test_voice"
    assert result.meta["speed"] == 1.2
    assert result.meta["text_length"] == 13


@pytest.mark.asyncio
async def test_generate_speech_voice_not_found(audio_generator, mock_voice_manager):
    """Test speech generation with non-existent voice."""
    # Setup mock to raise VoiceNotFoundError
    mock_voice_manager.get_voice.side_effect = VoiceNotFoundError("Voice 'non_existent_voice' not found")
    
    # Try to generate speech with non-existent voice
    with pytest.raises(VoiceNotFoundError):
        await audio_generator.generate_speech(
            text="Hello, world!",
            voice_id="non_existent_voice"
        )


@pytest.mark.asyncio
async def test_generate_speech_model_not_initialized(audio_generator, mock_model_handler):
    """Test speech generation with uninitialized model."""
    # Setup mock with uninitialized model
    mock_model_handler.is_initialized = False
    mock_model_handler.model = None
    
    # Generate speech - should initialize model first
    with pytest.raises(GenerationFailedError):
        await audio_generator.generate_speech(
            text="Hello, world!",
            voice_id="test_voice"
        )
    
    # Verify model initialization was attempted
    mock_model_handler.initialize.assert_called_once()


def test_convert_audio_format(audio_generator):
    """Test audio format conversion."""
    # Create test audio data
    sample_rate = 24000
    duration = 0.5  # 500ms
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * 440 * t) * 0.3
    audio_data = audio_data.astype(np.float32)
    
    # Convert to WAV format
    audio_bytes, format = audio_generator.convert_audio_format(
        audio_data,
        sample_rate,
        AudioFormat.WAV
    )
    
    # Verify result
    assert format == AudioFormat.WAV
    assert audio_bytes is not None
    assert len(audio_bytes) > 0
    
    # Verify unsupported format defaults to WAV
    audio_bytes, format = audio_generator.convert_audio_format(
        audio_data,
        sample_rate,
        AudioFormat.MP3
    )
    assert format == AudioFormat.WAV


def test_normalize_language_code(audio_generator):
    """Test language code normalization."""
    # Test normalization of various language codes
    assert audio_generator._normalize_language_code("en") == "en-us"
    assert audio_generator._normalize_language_code("en-us") == "en-us"
    assert audio_generator._normalize_language_code("EN-US") == "en-us"
    assert audio_generator._normalize_language_code("fr") == "fr"
    assert audio_generator._normalize_language_code("fr-fr") == "fr-fr"
