# Tests for Kokoro model handler
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np
from pathlib import Path

from src.tts_service.providers.kokoro import KokoroModelHandler
from src.tts_service.infrastructure import ModelLoadError


@pytest.fixture
def mock_kokoro():
    """Create a mock Kokoro instance."""
    mock = MagicMock()
    mock.create.return_value = (np.zeros(1000, dtype=np.float32), 24000)
    return mock


@pytest.fixture
def test_model_path(tmp_path):
    """Create a temporary model directory."""
    model_path = tmp_path / "models"
    model_path.mkdir()
    
    # Create model file
    model_file = model_path / "kokoro-v1.0.int8.onnx"
    model_file.touch()
    
    return str(model_path)


@pytest.fixture
def test_voices_dir(tmp_path):
    """Create a temporary voices directory."""
    voices_dir = tmp_path / "voices"
    voices_dir.mkdir()
    
    # Create voices file
    voices_file = voices_dir / "voices-v1.0.bin"
    voices_file.touch()
    
    return str(voices_dir)


@pytest.fixture
def model_handler(test_model_path, test_voices_dir):
    """Create a model handler with test paths."""
    with patch("src.tts_service.providers.kokoro.model_handler.Kokoro", return_value=MagicMock()):
        handler = KokoroModelHandler(
            model_path=test_model_path,
            voices_dir=test_voices_dir,
            use_gpu=False
        )
        yield handler


@pytest.mark.asyncio
async def test_initialization(test_model_path, test_voices_dir, mock_kokoro):
    """Test model handler initialization."""
    with patch("src.tts_service.providers.kokoro.model_handler.Kokoro", return_value=mock_kokoro):
        handler = KokoroModelHandler(
            model_path=test_model_path,
            voices_dir=test_voices_dir,
            use_gpu=False
        )
        
        # Check initial state
        assert handler._model_path == Path(test_model_path)
        assert handler._voices_dir == Path(test_voices_dir)
        assert handler._use_gpu is False
        assert handler._model_file == Path(test_model_path) / "kokoro-v1.0.int8.onnx"
        assert handler._voices_file == Path(test_voices_dir) / "voices-v1.0.bin"
        assert handler._kokoro is None
        assert handler.is_initialized is False


@pytest.mark.asyncio
async def test_initialize_success(model_handler, mock_kokoro):
    """Test successful model initialization."""
    with patch("src.tts_service.providers.kokoro.model_handler.Kokoro", return_value=mock_kokoro):
        # Initialize model
        await model_handler.initialize()
        
        # Check that model is initialized
        assert model_handler.is_initialized is True
        assert model_handler.model == mock_kokoro


@pytest.mark.asyncio
async def test_initialize_error_missing_model(model_handler):
    """Test initialization with missing model file."""
    # Remove model file
    model_handler._model_file.unlink(missing_ok=True)
    
    # Try to initialize model
    with pytest.raises(ModelLoadError):
        await model_handler.initialize()
    
    # Check that model is not initialized
    assert model_handler.is_initialized is False


@pytest.mark.asyncio
async def test_is_available(model_handler):
    """Test is_available method."""
    # Test with KOKORO_AVAILABLE = True
    with patch("src.tts_service.providers.kokoro.model_handler.KOKORO_AVAILABLE", True):
        assert await model_handler.is_available() is True
    
    # Test with KOKORO_AVAILABLE = False
    with patch("src.tts_service.providers.kokoro.model_handler.KOKORO_AVAILABLE", False):
        assert await model_handler.is_available() is False


def test_mock_kokoro_sample_rate():
    """Test that MockKokoro uses sampling rate from settings."""
    # Patch settings to have a custom sampling rate
    with patch("src.tts_service.providers.kokoro.model_handler.settings.KOKORO_SETTINGS", {"sampling_rate": 16000}):
        # Create a MockKokoro instance
        from src.tts_service.providers.kokoro.model_handler import MockKokoro
        mock_kokoro = MockKokoro("path/to/model", "path/to/voices")
        
        # Generate audio and check the sample rate
        audio_data, sample_rate = mock_kokoro.create("Test text")
        
        # Verify the sample rate is from settings, not hardcoded
        assert sample_rate == 16000
