#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A simple test script for Kokoro TTS.
This script can be run directly without the FastAPI application to test basic functionality.
"""

import os
import sys
from pathlib import Path
import soundfile as sf

# Add the project root to the Python path to find modules
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

try:
    from kokoro_onnx import Kokoro
    KOKORO_AVAILABLE = True
    print("✅ kokoro_onnx module found")
except ImportError:
    KOKORO_AVAILABLE = False
    print("❌ kokoro_onnx module not found")

def main():
    """Run a simple test of Kokoro TTS."""
    if not KOKORO_AVAILABLE:
        print("Kokoro ONNX module not available. Please install with:")
        print("  pip install kokoro-onnx")
        return

    # Paths to model and voices files
    model_dir = project_root / "data" / "models"
    voices_dir = project_root / "data" / "voices"
    
    model_path = model_dir / "kokoro-v1.0.int8.onnx"
    voices_path = voices_dir / "voices-v1.0.bin"
    
    # Check if files exist
    if not model_path.exists():
        print(f"Model file not found: {model_path}")
        print("Please download the model file first.")
        return
    
    if not voices_path.exists():
        print(f"Voices file not found: {voices_path}")
        print("Please download the voices file first.")
        return
    
    print(f"Using model: {model_path}")
    print(f"Using voices: {voices_path}")
    
    # Initialize Kokoro
    try:
        print("Initializing Kokoro...")
        kokoro = Kokoro(str(model_path), str(voices_path))
        print("✅ Kokoro initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Kokoro: {str(e)}")
        return
    
    # Generate speech
    try:
        text = "Hello, this is a test of the Kokoro TTS engine."
        print(f"Generating speech for text: {text}")
        
        samples, sample_rate = kokoro.create(
            text=text,
            voice="af_heart",
            speed=1.0,
            lang="en-us"
        )
        print(f"✅ Speech generated successfully: {len(samples)} samples at {sample_rate} Hz")
    except Exception as e:
        print(f"❌ Failed to generate speech: {str(e)}")
        return
    
    # Save to a WAV file
    try:
        output_path = project_root / "test_output.wav"
        sf.write(str(output_path), samples, sample_rate)
        print(f"✅ Audio saved to {output_path}")
    except Exception as e:
        print(f"❌ Failed to save audio: {str(e)}")
        return
    
    print("Test completed successfully")

if __name__ == "__main__":
    main()
