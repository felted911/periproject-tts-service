# Integration tests for API
import pytest
from unittest.mock import AsyncMock, patch
import json
from fastapi.testclient import TestClient

from src.tts_service.models import Voice, AudioResult, AudioFormat
from src.tts_service.infrastructure import VoiceNotFoundError


def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_docs_endpoint(client):
    """Test API docs endpoint."""
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]


def test_get_voices(client, test_kokoro_provider, monkeypatch):
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

    # Apply the mocks
    monkeypatch.setattr(test_kokoro_provider._voice_manager, "voices", mock_voices)
    monkeypatch.setattr(test_kokoro_provider, "is_available", AsyncMock(return_value=True))

    # Make request with the correct URL
    response = client.get("/api/v1/voices")

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "kokoro" in data
    assert len(data["kokoro"]) == 2
    assert data["kokoro"][0]["id"] == "voice1"
    assert data["kokoro"][1]["id"] == "voice2"


def test_get_voice(client, test_kokoro_provider, monkeypatch):
    """Test getting a specific voice."""
    # Mock data
    voice_id = "test_voice"
    mock_voice = Voice(
        id=voice_id,
        name="Test Voice",
        language="en",
        gender="neutral",
        provider="kokoro",
    )

    # Create a specific mock implementation that handles the right voice ID
    async def mock_get_voice(voice_id_arg):
        if voice_id_arg == voice_id:
            return mock_voice
        raise VoiceNotFoundError(f"Voice '{voice_id_arg}' not found")

    # Setup KokoroTTSProvider.get_voice mock to delegate to the voice manager
    async def mock_provider_get_voice(self, voice_id_arg):
        return await self._voice_manager.get_voice(voice_id_arg)

    # Apply the mocks
    from types import MethodType

    monkeypatch.setattr(test_kokoro_provider._voice_manager, "get_voice", mock_get_voice)
    monkeypatch.setattr(test_kokoro_provider, "get_voice", MethodType(mock_provider_get_voice, test_kokoro_provider))
    monkeypatch.setattr(test_kokoro_provider, "is_available", AsyncMock(return_value=True))

    # Make request
    response = client.get(f"/api/v1/voices/{voice_id}")

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == voice_id
    assert data["name"] == "Test Voice"
    assert data["language"] == "en"
    assert data["gender"] == "neutral"
    assert data["provider"] == "kokoro"


def test_get_voice_not_found(client, test_kokoro_provider, monkeypatch):
    """Test getting a non-existent voice."""

    # Setup voice_manager's get_voice to raise VoiceNotFoundError
    async def mock_get_voice(voice_id_arg):
        raise VoiceNotFoundError(f"Voice '{voice_id_arg}' not found")

    # Setup KokoroTTSProvider.get_voice to delegate to voice_manager
    async def mock_provider_get_voice(self, voice_id_arg):
        return await self._voice_manager.get_voice(voice_id_arg)

    # Apply the mocks
    from types import MethodType

    monkeypatch.setattr(test_kokoro_provider._voice_manager, "get_voice", mock_get_voice)
    monkeypatch.setattr(test_kokoro_provider, "get_voice", MethodType(mock_provider_get_voice, test_kokoro_provider))
    monkeypatch.setattr(test_kokoro_provider, "is_available", AsyncMock(return_value=True))

    # Make request
    response = client.get("/api/v1/voices/non_existent_voice")

    # Check response
    assert response.status_code == 404
    assert "error" in response.json()


def test_get_providers(client, test_kokoro_provider, monkeypatch):
    """Test getting provider information."""
    # Mock voices
    empty_voices = []
    monkeypatch.setattr(test_kokoro_provider._voice_manager, "voices", empty_voices)

    # Mock provider methods
    monkeypatch.setattr(test_kokoro_provider, "is_available", AsyncMock(return_value=True))
    monkeypatch.setattr(test_kokoro_provider, "get_features", lambda: ["feature1", "feature2"])

    # Make request
    response = client.get("/api/v1/providers")

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "kokoro"
    assert data[0]["name"] == "Kokoro TTS"  # This uses the actual property
    assert data[0]["is_available"] is True
    # Check for the mocked features
    assert "feature1" in data[0]["features"]
    assert "feature2" in data[0]["features"]


def test_generate_speech(client, test_kokoro_provider, test_cache_manager, monkeypatch):
    """Test speech generation."""
    # Mock data
    mock_result = AudioResult(
        audio_data=b"mock audio data",
        duration_ms=1000,
        sample_rate=24000,
        format=AudioFormat.WAV,
        meta={},
    )

    # Create a mock voice
    voice_id = "test_voice"
    mock_voice = Voice(
        id=voice_id,
        name="Test Voice",
        language="en",
        gender="neutral",
        provider="kokoro",
    )

    # Mock the voice manager's get_voice method
    async def mock_get_voice(voice_id_arg):
        if voice_id_arg == voice_id:
            return mock_voice
        raise VoiceNotFoundError(f"Voice '{voice_id_arg}' not found")

    # Mock the audio generator's generate_speech method
    async def mock_generate_speech(text, voice_id_arg, options=None):
        return mock_result

    # Setup KokoroTTSProvider.get_voice and generate_speech to delegate properly
    async def mock_provider_get_voice(self, voice_id_arg):
        return await self._voice_manager.get_voice(voice_id_arg)

    async def mock_provider_generate_speech(self, text, voice_id_arg, options=None):
        return await self._audio_generator.generate_speech(text, voice_id_arg, options)

    # Apply the mocks
    from types import MethodType

    monkeypatch.setattr(test_kokoro_provider._voice_manager, "get_voice", mock_get_voice)
    monkeypatch.setattr(test_kokoro_provider._audio_generator, "generate_speech", mock_generate_speech)

    monkeypatch.setattr(test_kokoro_provider, "get_voice", MethodType(mock_provider_get_voice, test_kokoro_provider))
    monkeypatch.setattr(
        test_kokoro_provider, "generate_speech", MethodType(mock_provider_generate_speech, test_kokoro_provider)
    )

    monkeypatch.setattr(test_kokoro_provider, "is_available", AsyncMock(return_value=True))

    # Mock cache manager
    monkeypatch.setattr(test_cache_manager, "get", AsyncMock(return_value=None))
    monkeypatch.setattr(test_cache_manager, "set", AsyncMock(return_value=True))

    # Make request
    request_data = {"text": "Hello, world!", "voice": voice_id, "options": {"speed": 1.0}, "format": "wav"}

    response = client.post("/api/v1/tts", json=request_data)

    # Check response
    assert response.status_code == 200
    assert response.content == b"mock audio data"
    assert response.headers["Content-Type"] == "audio/wav"
    assert response.headers["X-Audio-Duration"] == "1000"
    assert response.headers["X-Audio-Sample-Rate"] == "24000"
    assert response.headers["X-Audio-Format"] == "wav"
