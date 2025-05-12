# Test TTS router
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import io

from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.tts_service.api.routers.tts import router, get_tts_validator
from src.tts_service.models import TTSRequest, AudioFormat, AudioResult
from src.tts_service.infrastructure import ValidationError


# Setup test app
from fastapi import FastAPI, Depends

app = FastAPI()
app.include_router(router)


# Mock dependencies
@pytest.fixture
def mock_tts_service():
    """Mock TTS service."""
    service_mock = MagicMock()
    service_mock.generate_speech = AsyncMock()
    service_mock.get_provider_info = AsyncMock()
    return service_mock


@pytest.fixture
def mock_validator():
    """Mock TTS validator."""
    validator_mock = MagicMock()
    validator_mock.validate = MagicMock()
    return validator_mock


@pytest.fixture
def client(mock_tts_service, mock_validator):
    """Test client with mocked dependencies."""
    # Import the dependency resolver function that's being mocked
    from src.tts_service.api.dependencies import get_tts_service as original_get_tts_service

    app.dependency_overrides = {
        # Override the service dependency with the correct function reference
        original_get_tts_service: lambda: mock_tts_service,
        # Override the validator dependency
        get_tts_validator: lambda: mock_validator,
    }
    return TestClient(app)


def test_generate_speech_success(client, mock_tts_service, mock_validator):
    """Test successful speech generation."""
    # Arrange
    mock_result = AudioResult(
        audio_data=b"test audio data", duration_ms=1000, sample_rate=24000, format=AudioFormat.WAV, meta={}
    )
    mock_tts_service.generate_speech.return_value = mock_result

    request_data = {"text": "This is a test", "voice": "test_voice", "options": {"speed": 1.0}, "format": "wav"}

    # Act
    response = client.post("/tts", json=request_data)

    # Assert
    assert response.status_code == 200
    assert response.content == b"test audio data"
    assert response.headers["Content-Type"] == "audio/wav"
    assert response.headers["X-Audio-Duration"] == "1000"
    assert response.headers["X-Audio-Sample-Rate"] == "24000"

    # Verify validator was called
    mock_validator.validate.assert_called_once()

    # Verify service was called with correct args
    mock_tts_service.generate_speech.assert_called_once()
    call_args = mock_tts_service.generate_speech.call_args[1]
    assert call_args["text"] == "This is a test"
    assert call_args["voice_id"] == "test_voice"
    assert call_args["options"] == {"speed": 1.0}


def test_generate_speech_validation_error(client, mock_tts_service, mock_validator):
    """Test text length validation error."""
    # Arrange
    error_message = "Text length exceeds maximum allowed length of 1000 characters"
    mock_validator.validate.side_effect = ValidationError(error_message)

    request_data = {"text": "This is a test", "voice": "test_voice", "format": "wav"}

    # Act
    response = client.post("/tts", json=request_data)

    # Assert
    assert response.status_code == 400
    assert error_message in response.json()["detail"]

    # Verify service was not called
    mock_tts_service.generate_speech.assert_not_called()


def test_health_check(client, mock_tts_service):
    """Test health check endpoint."""
    # Arrange
    mock_provider_info = [
        MagicMock(id="provider1", name="Provider 1", is_available=True, voice_count=5),
        MagicMock(id="provider2", name="Provider 2", is_available=False, voice_count=3),
    ]
    mock_tts_service.get_provider_info.return_value = mock_provider_info

    # Act
    response = client.get("/tts/health")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"  # At least one provider is available
    assert len(data["providers"]) == 2

    # Check provider details
    providers = {p["id"]: p for p in data["providers"]}
    assert "provider1" in providers
    assert providers["provider1"]["available"] is True
    assert providers["provider1"]["voice_count"] == 5

    assert "provider2" in providers
    assert providers["provider2"]["available"] is False
    assert providers["provider2"]["voice_count"] == 3
