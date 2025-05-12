# Validator for TTS requests
import sys
import os
from typing import Optional, Dict, Any

# Import settings from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
from config import settings

from ...models import TTSRequest
from ...infrastructure import ValidationError, get_logger

logger = get_logger(__name__)

class TTSRequestValidator:
    """Validator for TTS requests.
    
    This class is responsible for validating TTS requests before processing them.
    It implements the Single Responsibility Principle by focusing solely on
    validation logic, separate from the router's request handling logic.
    """
    
    def __init__(self, max_text_length: Optional[int] = None):
        """Initialize the validator.
        
        Args:
            max_text_length: Maximum allowed text length for TTS requests.
                If None, the value from settings is used.
        """
        self.max_text_length = max_text_length or settings.MAX_TEXT_LENGTH
    
    def validate(self, request: TTSRequest) -> None:
        """Validate a TTS request.
        
        Args:
            request: The TTS request to validate
            
        Raises:
            ValidationError: If the request is invalid
        """
        self._validate_text_length(request.text)
        # Additional validations can be added here
    
    def _validate_text_length(self, text: str) -> None:
        """Validate text length against maximum allowed length.
        
        Args:
            text: The text to validate
            
        Raises:
            ValidationError: If the text exceeds the maximum length
        """
        if len(text) > self.max_text_length:
            logger.warning(
                f"Text length validation failed",
                extra={
                    "text_length": len(text),
                    "max_length": self.max_text_length,
                },
            )
            raise ValidationError(
                f"Text length exceeds maximum allowed length of {self.max_text_length} characters"
            )
