# Tests for Kokoro voice manager
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np

from src.tts_service.providers.kokoro import KokoroVoiceManager
from src.tts_service.infrastructure import VoiceNotFoundError, ModelLoadError


@pytest.fixture
def voice_manager():
    """Create a voice manager."""
    manager = KokoroVoiceManager(
        provider_id="kokoro",
        default_language="en-us"
    )
    return manager


@pytest.mark.asyncio
async def test_initialization(voice_manager):
    """Test voice manager initialization."""
    # Check initial state
    assert voice_manager._provider_id == "kokoro"
    assert voice_manager._default_language == "en-us"
    assert len(voice_manager._voices) == 0
    assert len(voice_manager._languages) == 0
    assert len(voice_manager._voice_metadata) > 0  # Should have some metadata


@pytest.mark.asyncio
async def test_load_voices(voice_manager):
    """Test loading voices."""
    # Load voices
    await voice_manager.load_voices()
    
    # Check that voices were loaded
    assert len(voice_manager.voices) > 0
    
    # Verify a specific voice
    assert any(v.id == "af_heart" for v in voice_manager.voices)
    heart_voice = next(v for v in voice_manager.voices if v.id == "af_heart")
    assert heart_voice.name == "Heart"
    assert heart_voice.language == "en-us"
    assert heart_voice.provider == "kokoro"


@pytest.mark.asyncio
async def test_load_languages(voice_manager):
    """Test loading languages."""
    # Load languages
    await voice_manager.load_languages()
    
    # Check that languages were loaded
    assert len(voice_manager.languages) > 0
    
    # Verify a specific language
    assert any(l.code == "en-us" for l in voice_manager.languages)
    en_us = next(l for l in voice_manager.languages if l.code == "en-us")
    assert en_us.name == "English (US)"


@pytest.mark.asyncio
async def test_get_voice_success(voice_manager):
    """Test getting an existing voice."""
    # Load voices first
    await voice_manager.load_voices()
    
    # Get voice
    voice = await voice_manager.get_voice("af_heart")
    
    # Verify voice
    assert voice.id == "af_heart"
    assert voice.name == "Heart"
    assert voice.language == "en-us"
    assert voice.provider == "kokoro"


@pytest.mark.asyncio
async def test_get_voice_not_found(voice_manager):
    """Test getting a non-existent voice."""
    # Load voices first
    await voice_manager.load_voices()
    
    # Try to get non-existent voice
    with pytest.raises(VoiceNotFoundError):
        await voice_manager.get_voice("non_existent_voice")


def test_load_voice_metadata(voice_manager):
    """Test loading voice metadata."""
    # Metadata should be loaded during initialization
    metadata = voice_manager._voice_metadata
    
    # Verify metadata
    assert "af_heart" in metadata
    assert metadata["af_heart"]["name"] == "Heart"
    assert metadata["af_heart"]["language"] == "en-us"
    assert metadata["af_heart"]["gender"] == "female"
