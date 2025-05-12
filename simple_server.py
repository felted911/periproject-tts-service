#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A simplified FastAPI server for Kokoro TTS.
This is a minimalist version that can be used for testing with fewer dependencies.
"""

import os
import io
import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any
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

# Create FastAPI application
app = FastAPI(
    title="Simple Kokoro TTS API",
    description="A simplified API for Kokoro TTS",
    version="0.1.0",
)

# Model and voices paths
MODEL_PATH = project_root / "data" / "models" / "kokoro-v1.0.int8.onnx"
VOICES_PATH = project_root / "data" / "voices" / "voices-v1.0.bin"

# Global Kokoro instance
kokoro = None


class TTSRequest(BaseModel):
    """Request model for TTS endpoint."""
    
    text: str
    voice: str = "af_heart"
    speed: float = 1.0
    lang: str = "en-us"


@app.on_event("startup")
async def startup_event():
    """Initialize Kokoro on startup."""
    global kokoro
    
    if not KOKORO_AVAILABLE:
        print("Kokoro ONNX module not available. Please install with:")
        print("  pip install kokoro-onnx")
        return
    
    # Check if files exist
    if not MODEL_PATH.exists():
        print(f"Model file not found: {MODEL_PATH}")
        return
    
    if not VOICES_PATH.exists():
        print(f"Voices file not found: {VOICES_PATH}")
        return
    
    try:
        kokoro = Kokoro(str(MODEL_PATH), str(VOICES_PATH))
        print("✅ Kokoro initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Kokoro: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the Simple Kokoro TTS API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "kokoro_available": kokoro is not None}


@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Generate speech from text."""
    if kokoro is None:
        raise HTTPException(status_code=503, detail="TTS service not available")
    
    try:
        # Generate speech
        samples, sample_rate = kokoro.create(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            lang=request.lang
        )
        
        # Convert to WAV
        with io.BytesIO() as wav_buffer:
            sf.write(wav_buffer, samples, sample_rate, format='WAV')
            wav_buffer.seek(0)
            audio_data = wav_buffer.read()
        
        # Return WAV audio
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f'attachment; filename="speech.wav"',
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate speech: {str(e)}")


def main():
    """Run the FastAPI server."""
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
