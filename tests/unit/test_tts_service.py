# Tests for TTS service
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.tts_service.models import AudioResult, AudioFormat, Voice
from src.tts_service.infrastructure import VoiceNotFoundError


@pytest.mark.asyncio
async def test_service_initialization(tts_service, mock_kokoro_provider):
    """Test service initialization."""
    # Create mocks for provider methods
    initialize_called = False
    
    async def mock_is_available():
        return True
    
    async def mock_initialize():
        nonlocal initialize_called
        initialize_called = True
        
    # Mock provider methods
    mock_kokoro_provider.initialize = mock_initialize
    mock_kokoro_provider.is_available = mock_is_available
    
    # Initialize service
    await tts_service.initialize()
    
    # Verify provider initialize was called
    assert initialize_called, "initialize should be called during service initialization"


@pytest.mark.asyncio
async def test_get_all_voices(tts_service, mock_kokoro_provider):
    """Test getting all voices."""
    # Mock data
    mock_voices = [
        Voice(
            id="voice1",
            name="Test Voice 1",
            language="en",
            gender="female",
            provider="kokoro",
        ),
        Voice(
            id="voice2",
            name="Test Voice 2",
            language="en",
            gender="male",
            provider="kokoro",
        ),
    ]
    
    # Mock provider methods
    async def mock_get_voices():
        return mock_voices
        
    async def mock_is_available():
        return True
        
    mock_kokoro_provider.get_voices = mock_get_voices
    mock_kokoro_provider.is_available = mock_is_available
    
    # Get voices
    voices = await tts_service.get_all_voices()
    
    # Verify results
    assert "kokoro" in voices
    assert len(voices["kokoro"]) == 2
    assert voices["kokoro"][0].id == "voice1"
    assert voices["kokoro"][1].id == "voice2"


@pytest.mark.asyncio
async def test_generate_speech(tts_service, mock_kokoro_provider, cache_manager):
    """Test speech generation."""
    # Mock data
    voice_id = "test_voice"
    text = "Hello, world!"
    expected_result = AudioResult(
        audio_data=b"mock audio data",
        duration_ms=1000,
        sample_rate=24000,
        format=AudioFormat.WAV,
        meta={},
    )
    
    # Mock provider methods
    mock_voice = Voice(
        id=voice_id,
        name="Test Voice",
        language="en",
        gender="neutral",
        provider="kokoro",
    )
    mock_kokoro_provider.get_voice = AsyncMock(return_value=mock_voice)
    
    # Track calls to generate_speech
    generate_speech_called = False
    generate_speech_args = None
    
    async def mock_generate_speech(*args, **kwargs):
        nonlocal generate_speech_called, generate_speech_args
        generate_speech_called = True
        generate_speech_args = (args, kwargs)
        return expected_result
        
    async def mock_is_available():
        return True
        
    mock_kokoro_provider.generate_speech = mock_generate_speech
    mock_kokoro_provider.is_available = mock_is_available
    
    # Mock cache manager
    cache_manager.get = AsyncMock(return_value=None)  # Cache miss
    cache_manager.set = AsyncMock(return_value=True)
    
    # Generate speech
    result = await tts_service.generate_speech(text, voice_id)
    
    # Verify provider methods were called
    mock_kokoro_provider.get_voice.assert_called_once_with(voice_id)
    assert generate_speech_called, "generate_speech should be called when there's a cache miss"
    assert generate_speech_args[0][0] == text, "generate_speech called with wrong text"
    assert generate_speech_args[0][1] == voice_id, "generate_speech called with wrong voice_id"
    assert generate_speech_args[1] == {}, "generate_speech called with wrong options"
    
    # Verify result
    assert result == expected_result
    
    # Verify cache was set
    cache_manager.set.assert_called_once()


@pytest.mark.asyncio
async def test_generate_speech_with_cache(tts_service, mock_kokoro_provider, cache_manager):
    """Test speech generation with cache hit."""
    # Mock data
    voice_id = "test_voice"
    text = "Hello, world!"
    cached_audio = b"cached audio data"
    
    # Mock cache manager
    cache_manager.get = AsyncMock(return_value=cached_audio)  # Cache hit
    
    # Mock generate_speech on the provider to track if it's called
    original_generate_speech = mock_kokoro_provider.generate_speech
    generate_speech_called = False
    
    async def mock_generate_speech(*args, **kwargs):
        nonlocal generate_speech_called
        generate_speech_called = True
        # This should never be called in this test
        return await original_generate_speech(*args, **kwargs)
        
    async def mock_is_available():
        return True
        
    mock_kokoro_provider.generate_speech = mock_generate_speech
    mock_kokoro_provider.is_available = mock_is_available
    
    # Generate speech
    result = await tts_service.generate_speech(text, voice_id)
    
    # Verify provider methods were not called
    assert not generate_speech_called, "generate_speech should not be called when using cached data"
    
    # Verify result
    assert result.audio_data == cached_audio


@pytest.mark.asyncio
async def test_get_voice_not_found(tts_service, mock_kokoro_provider):
    """Test getting a non-existent voice."""
    # Mock provider methods to throw an exception
    async def mock_get_voice(voice_id):
        raise VoiceNotFoundError(f"Voice '{voice_id}' not found")
        
    async def mock_is_available():
        return True
        
    mock_kokoro_provider.get_voice = mock_get_voice
    mock_kokoro_provider.is_available = mock_is_available
    
    # Try to get voice
    with pytest.raises(VoiceNotFoundError):
        await tts_service.get_voice("non_existent_voice")
