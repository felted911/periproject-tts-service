# Kokoro TTS provider implementation
# This file now uses the refactored Kokoro TTS provider components
import os
import sys
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

from ..models import Voice, Language, AudioResult
from .kokoro.provider import KokoroTTSProvider

# Export the provider class to maintain backward compatibility
__all__ = ["KokoroTTSProvider"]
