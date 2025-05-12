# Configuration settings for the TTS service
import os
from pathlib import Path
from typing import Dict, Any

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VOICES_DIR = DATA_DIR / "voices"
CACHE_DIR = DATA_DIR / "cache"
MODEL_DIR = DATA_DIR / "models"

# Ensure directories exist
VOICES_DIR.mkdir(exist_ok=True, parents=True)
CACHE_DIR.mkdir(exist_ok=True, parents=True)
MODEL_DIR.mkdir(exist_ok=True, parents=True)

# Environment settings
ENV = os.getenv("ENVIRONMENT", "development")
DEBUG = ENV == "development"

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_PREFIX = "/api/v1"

# Kokoro TTS settings
KOKORO_SETTINGS: Dict[str, Any] = {
    "model_path": os.getenv("KOKORO_MODEL_PATH", str(MODEL_DIR)),
    "voices_dir": str(VOICES_DIR),
    "cache_dir": str(CACHE_DIR),
    "default_language": os.getenv("KOKORO_DEFAULT_LANGUAGE", "en-us"),
    "sampling_rate": int(os.getenv("KOKORO_SAMPLING_RATE", 24000)),
    "use_gpu": os.getenv("KOKORO_USE_GPU", "false").lower() == "true",
}

# Audio settings
AUDIO_FORMAT = os.getenv("AUDIO_FORMAT", "wav")
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", 1000))

# Cache settings
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", 86400))  # 24 hours in seconds
MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", 1024 * 1024 * 1024))  # 1GB

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json" if ENV == "production" else "console")

# Security settings
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 100))  # requests per minute
RATE_LIMIT_TIMEFRAME = int(os.getenv("RATE_LIMIT_TIMEFRAME", 60))  # seconds

# Model download URLs
KOKORO_MODEL_URLS = {
    "model": {
        "fp32": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
        "fp16": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.fp16.onnx",
        "int8": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx",
    },
    "voices": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}
