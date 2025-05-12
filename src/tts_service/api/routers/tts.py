# API router for TTS endpoints
import io
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, BackgroundTasks
from fastapi.responses import StreamingResponse

from ...services import TTSService
from ...models import TTSRequest, AudioFormat
from config import settings
from ...infrastructure import (
    VoiceNotFoundError,
    ProviderNotAvailableError,
    ValidationError,
    GenerationFailedError,
    get_logger,
)
from ..dependencies import get_tts_service
from ..validators import TTSRequestValidator

router = APIRouter(prefix="/tts", tags=["tts"])
logger = get_logger(__name__)


def get_tts_validator() -> TTSRequestValidator:
    """Dependency injection for TTSRequestValidator.

    Returns:
        A configured TTSRequestValidator instance
    """
    return TTSRequestValidator()


@router.post("/", response_class=StreamingResponse, summary="Generate speech from text")
async def generate_speech(
    request: TTSRequest,
    background_tasks: BackgroundTasks,
    tts_service: TTSService = Depends(get_tts_service),
    validator: TTSRequestValidator = Depends(get_tts_validator),
) -> StreamingResponse:
    """Generate speech from text.

    Args:
        request: TTS request
        background_tasks: FastAPI background tasks
        tts_service: TTS service
        validator: TTS request validator

    Returns:
        Audio stream

    Raises:
        HTTPException: If generation fails
    """
    # Try to generate speech
    try:
        # Log request
        logger.info(
            f"TTS request received",
            extra={
                "text_length": len(request.text),
                "voice_id": request.voice,
                "format": request.format.value,
            },
        )

        # Validate request - explicitly check for text length
        if len(request.text) > settings.MAX_TEXT_LENGTH:
            raise ValidationError(
                f"Text length exceeds maximum allowed length of {settings.MAX_TEXT_LENGTH} characters"
            )

        validator.validate(request)

        # Generate speech
        result = await tts_service.generate_speech(
            text=request.text,
            voice_id=request.voice,
            provider_id=request.options.get("provider_id"),
            options=request.options,
        )

        logger.info(f"TTS generation successful for voice {request.voice}")

        return create_streaming_response(result)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except VoiceNotFoundError as e:
        logger.error(f"Voice not found for TTS: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ProviderNotAvailableError as e:
        logger.error(f"Provider not available for TTS: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except GenerationFailedError as e:
        logger.error(f"TTS generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate speech")
    except Exception as e:
        logger.exception(f"Unexpected error during TTS generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


def create_streaming_response(result) -> StreamingResponse:
    """Create a streaming response from audio result.

    This function encapsulates the logic for creating a streaming response
    based on an audio result, following the Single Responsibility Principle.

    Args:
        result: Audio generation result

    Returns:
        StreamingResponse with proper headers and content type
    """
    # Determine content type
    content_type = {
        AudioFormat.WAV: "audio/wav",
        AudioFormat.MP3: "audio/mpeg",
        AudioFormat.OGG: "audio/ogg",
    }.get(result.format, "application/octet-stream")

    # Return audio stream
    return StreamingResponse(
        content=io.BytesIO(result.audio_data),
        media_type=content_type,
        headers={
            "X-Audio-Duration": str(result.duration_ms),
            "X-Audio-Sample-Rate": str(result.sample_rate),
            "X-Audio-Format": result.format.value,
        },
    )


@router.get("/health", response_model=Dict[str, Any], summary="Check service health")
async def health_check(
    tts_service: TTSService = Depends(get_tts_service),
) -> Dict[str, Any]:
    """Check service health.

    Returns:
        Health status
    """
    # Get provider info
    providers = await tts_service.get_provider_info()

    # Check if any provider is available
    service_available = any(p.is_available for p in providers)

    return {
        "status": "healthy" if service_available else "degraded",
        "providers": [
            {
                "id": p.id,
                "name": p.name,
                "available": p.is_available,
                "voice_count": p.voice_count,
            }
            for p in providers
        ],
    }
