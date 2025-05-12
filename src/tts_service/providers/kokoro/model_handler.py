# Model handler for Kokoro TTS
import os
from pathlib import Path
from typing import Any, Optional

# Module exports
__all__ = ["KokoroModelHandler", "MockKokoro", "KOKORO_AVAILABLE"]

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from ...infrastructure import get_logger, ModelLoadError
from config import settings

# Import for Kokoro ONNX TTS
# Define MockKokoro outside the try/except block to make it importable even if the import fails
class MockKokoro:
    """Mock Kokoro implementation for development."""
    
    def __init__(self, model_path: str, voices_path: str):
        self.model_path = model_path
        self.voices_path = voices_path
        self.loaded = True
        
    def create(
        self, 
        text: str, 
        voice: str = "af_heart",
        speed: float = 1.0,
        lang: str = "en-us"
    ) -> tuple[Any, int]:
        """Generate speech."""
        # Generate some dummy audio data (sine wave)
        import numpy as np
        sample_rate = settings.KOKORO_SETTINGS["sampling_rate"]
        duration = len(text) / 10  # Rough approximation
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = np.sin(2 * np.pi * 440 * t) * 0.3
        return audio.astype(np.float32), sample_rate

try:
    from kokoro_onnx import Kokoro
    KOKORO_AVAILABLE = True
except ImportError:
    # Mock implementation for development and testing
    KOKORO_AVAILABLE = False
    # Mock the module
    Kokoro = MockKokoro

logger = get_logger(__name__)


class KokoroModelHandler:
    """Handler for Kokoro TTS model initialization and management."""
    
    def __init__(
        self,
        model_path: str = settings.KOKORO_SETTINGS["model_path"],
        voices_dir: str = settings.KOKORO_SETTINGS["voices_dir"],
        use_gpu: bool = settings.KOKORO_SETTINGS["use_gpu"],
    ):
        """Initialize the Kokoro model handler.
        
        Args:
            model_path: Path to models directory
            voices_dir: Path to voices directory
            use_gpu: Whether to use GPU
        """
        self._model_path = Path(model_path)
        self._voices_dir = Path(voices_dir)
        self._use_gpu = use_gpu and KOKORO_AVAILABLE
        
        # Ensure directories exist
        self._model_path.mkdir(exist_ok=True, parents=True)
        self._voices_dir.mkdir(exist_ok=True, parents=True)
        
        # Model and voices file paths
        if use_gpu:
            # Use FP16 model for GPU
            self._model_file = self._model_path / "kokoro-v1.0.fp16.onnx"
        else:
            # Use INT8 model for CPU (smaller and faster)
            self._model_file = self._model_path / "kokoro-v1.0.int8.onnx"
            
        self._voices_file = self._voices_dir / "voices-v1.0.bin"
        
        # Initialize Kokoro instance
        self._kokoro: Optional[Any] = None
        
        logger.info(
            f"Kokoro model handler initialized",
            extra={
                "model_path": str(self._model_file),
                "voices_path": str(self._voices_file),
                "use_gpu": self._use_gpu,
                "available": KOKORO_AVAILABLE,
            },
        )
    
    @property
    def model(self) -> Any:
        """Get the Kokoro model instance.
        
        Returns:
            Kokoro model instance
        """
        return self._kokoro
    
    @property
    def is_initialized(self) -> bool:
        """Check if model is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self._kokoro is not None
    
    async def initialize(self) -> None:
        """Initialize Kokoro model.
        
        Raises:
            ModelLoadError: If model cannot be initialized
        """
        if self.is_initialized:
            return
            
        try:
            logger.info(f"Initializing Kokoro with model '{self._model_file}' and voices '{self._voices_file}'")
            
            # Download model and voices files if they don't exist
            # In a real implementation, this would handle downloading
            if not self._model_file.exists():
                raise FileNotFoundError(f"Model file not found: {self._model_file}")
            
            if not self._voices_file.exists():
                raise FileNotFoundError(f"Voices file not found: {self._voices_file}")
            
            # Create Kokoro instance
            self._kokoro = Kokoro(
                str(self._model_file),
                str(self._voices_file)
            )
            
            logger.info(f"Kokoro initialized successfully")
        except Exception as e:
            logger.exception(f"Failed to initialize Kokoro: {str(e)}")
            raise ModelLoadError(f"Failed to initialize Kokoro: {str(e)}")
    
    async def is_available(self) -> bool:
        """Check if Kokoro is available.
        
        Returns:
            True if available, False otherwise
        """
        return KOKORO_AVAILABLE
