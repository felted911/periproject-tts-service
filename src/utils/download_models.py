# Utility script to download Kokoro TTS models and voice files
import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm
import argparse

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config import settings

def download_file(url: str, destination: Path, chunk_size: int = 8192) -> None:
    """Download a file with progress bar.
    
    Args:
        url: URL to download
        destination: Destination path
        chunk_size: Chunk size in bytes
        
    Returns:
        None
    """
    # Create parent directory if it doesn't exist
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    # Don't download if file already exists
    if destination.exists():
        print(f"File already exists: {destination}")
        return
    
    # Download file
    print(f"Downloading {url} to {destination}")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    
    # Show progress bar
    with tqdm(total=total_size, unit="B", unit_scale=True) as progress_bar:
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    progress_bar.update(len(chunk))
    
    print(f"Downloaded {destination}")

def download_kokoro_models(model_type: str = "int8") -> None:
    """Download Kokoro TTS models and voice files.
    
    Args:
        model_type: Model type (fp32, fp16, or int8)
        
    Returns:
        None
        
    Raises:
        ValueError: If an invalid model type is provided
    """
    # Validate model type
    valid_types = ["fp32", "fp16", "int8"]
    if model_type not in valid_types:
        raise ValueError(f"Invalid model type: {model_type}. Must be one of {valid_types}")
    
    # Download model
    model_url = settings.KOKORO_MODEL_URLS["model"][model_type]
    model_path = Path(settings.MODEL_DIR) / f"kokoro-v1.0{'.fp16' if model_type == 'fp16' else '.int8' if model_type == 'int8' else ''}.onnx"
    download_file(model_url, model_path)
    
    # Download voices
    voices_url = settings.KOKORO_MODEL_URLS["voices"]
    voices_path = Path(settings.VOICES_DIR) / "voices-v1.0.bin"
    download_file(voices_url, voices_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Kokoro TTS models and voice files")
    parser.add_argument(
        "--model-type", 
        choices=["fp32", "fp16", "int8"], 
        default="int8",
        help="Model type to download (fp32, fp16, or int8)"
    )
    args = parser.parse_args()
    
    download_kokoro_models(args.model_type)
