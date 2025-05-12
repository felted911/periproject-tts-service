# Test configuration for pytest
import os
import sys
import pytest
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).resolve().parent.parent.parent / "src"
sys.path.insert(0, str(src_path))
project_path = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_path))

from src.tts_service.infrastructure import CacheManager
from src.tts_service.providers import KokoroTTSProvider
from src.tts_service.services import TTSService


@pytest.fixture
def test_cache_dir(tmp_path):
    """Create a temporary cache directory.

    Args:
        tmp_path: Pytest temporary path

    Returns:
        Path to temporary cache directory
    """
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return str(cache_dir)


@pytest.fixture
def cache_manager(test_cache_dir):
    """Create a test cache manager.

    Args:
        test_cache_dir: Temporary cache directory

    Returns:
        Cache manager instance
    """
    cm = CacheManager(
        cache_dir=test_cache_dir,
        enabled=True,
        ttl=3600,
        max_size=1024 * 1024 * 10,  # 10MB
    )
    # For compatibility with existing tests
    cm._cache_dir = test_cache_dir
    return cm


@pytest.fixture
def mock_kokoro_provider():
    """Create a mock Kokoro TTS provider.

    Returns:
        Mock Kokoro TTS provider instance
    """
    provider = KokoroTTSProvider(
        model_path="mock_model_path",
        voices_dir="mock_voices_dir",
        cache_dir="mock_cache_dir",
        default_language="en",
        use_gpu=False,
    )
    return provider


@pytest.fixture
def tts_service(mock_kokoro_provider, cache_manager):
    """Create a test TTS service.

    Args:
        mock_kokoro_provider: Mock Kokoro TTS provider
        cache_manager: Cache manager

    Returns:
        TTS service instance
    """
    providers = {"kokoro": mock_kokoro_provider}
    return TTSService(providers=providers, cache_manager=cache_manager)
