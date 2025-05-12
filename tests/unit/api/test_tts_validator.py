# Test TTS validator
import pytest
from unittest.mock import patch

from src.tts_service.api.validators.tts_validator import TTSRequestValidator
from src.tts_service.models import TTSRequest, AudioFormat
from src.tts_service.infrastructure import ValidationError


def test_validate_valid_request():
    """Test that a valid request passes validation."""
    # Arrange
    validator = TTSRequestValidator(max_text_length=100)
    request = TTSRequest(
        text="This is a test",
        voice="test_voice",
        options={},
        format=AudioFormat.WAV
    )
    
    # Act & Assert
    # Should not raise any exception
    validator.validate(request)


def test_validate_text_too_long():
    """Test that a request with text exceeding max length fails validation."""
    # Arrange
    max_length = 10
    validator = TTSRequestValidator(max_text_length=max_length)
    request = TTSRequest(
        text="This text is too long for validation",
        voice="test_voice",
        options={},
        format=AudioFormat.WAV
    )
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validator.validate(request)
    
    # Check error message
    assert f"maximum allowed length of {max_length}" in str(exc_info.value)


def test_validate_uses_settings_value():
    """Test that validator uses settings.MAX_TEXT_LENGTH by default."""
    # Arrange
    with patch("src.tts_service.api.validators.tts_validator.settings") as mock_settings:
        mock_settings.MAX_TEXT_LENGTH = 15
        validator = TTSRequestValidator()  # No explicit max_text_length
        
        # Valid request
        valid_request = TTSRequest(
            text="Short text",
            voice="test_voice",
            options={},
            format=AudioFormat.WAV
        )
        
        # Invalid request
        invalid_request = TTSRequest(
            text="This text is too long for validation",
            voice="test_voice",
            options={},
            format=AudioFormat.WAV
        )
        
        # Act & Assert
        # Valid request should pass
        validator.validate(valid_request)
        
        # Invalid request should fail
        with pytest.raises(ValidationError):
            validator.validate(invalid_request)
