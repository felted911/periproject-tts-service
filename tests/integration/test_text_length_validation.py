# Integration test for text length validation
import pytest
from fastapi.testclient import TestClient
import traceback
from config import settings


@pytest.mark.parametrize("endpoint_url", [
    f"{settings.API_PREFIX}/tts/",  # With trailing slash
    f"{settings.API_PREFIX}/tts"    # Without trailing slash
])
def test_text_length_validation(client, test_tts_validator, endpoint_url):
    """Test text length validation in the TTS endpoint.
    
    Tests both with and without trailing slash to ensure robustness.
    
    Note: The validation happens at the Pydantic/FastAPI level via @validator,
    which returns a 422 Unprocessable Entity status code, not in our custom validator.
    """
    try:
        # Create a request with text that exceeds MAX_TEXT_LENGTH
        # Use the validator's actual value rather than hardcoding
        max_length = test_tts_validator.max_text_length
        long_text = "a" * (max_length + 1)  # One character more than allowed
        
        request_data = {
            "text": long_text,
            "voice": "test_voice",
            "format": "wav"
        }
        
        # Make request to the endpoint
        print(f"DEBUG: Posting to endpoint: {endpoint_url}")
        response = client.post(endpoint_url, json=request_data)
        
        # Check response
        # We expect 422 (Unprocessable Entity) as the validation is handled by Pydantic
        # not our custom validator which would return 400
        assert response.status_code == 422, f"Expected status 422 but got {response.status_code} - Response: {response.text}"
        response_json = response.json()
        print(f"DEBUG: Response JSON: {response_json}")
        
        # Check that the error is about text length
        assert any("text length exceeds maximum" in error.get("msg", "").lower() 
                  for error in response_json.get("detail", []))
    except Exception as e:
        print(f"DEBUG: Exception details: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise
