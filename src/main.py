# Main application entry point
import asyncio
import uvicorn
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from tts_service.api import api_router, RequestLoggerMiddleware
from tts_service.infrastructure import get_logger
from tts_service.services import TTSService
from tts_service.api.dependencies import get_tts_service
from config import settings
from utils.download_models import download_kokoro_models

# Configure logger
logger = get_logger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events for the application."""
    # Startup logic
    logger.info("Application starting up")
    
    # Check and download model files if needed
    if not check_model_files():
        logger.info("Downloading model files...")
        model_type = "int8" if not settings.KOKORO_SETTINGS["use_gpu"] else "fp16"
        download_kokoro_models(model_type)
    
    # Initialize TTS service
    # Important: We need to properly resolve dependencies
    from tts_service.api.dependencies import get_providers, get_cache_manager
    providers = get_providers()  # Direct call, not using Depends
    cache_manager = get_cache_manager()  # Direct call, not using Depends
    from tts_service.services import TTSService
    tts_service = TTSService(providers=providers, cache_manager=cache_manager)
    await tts_service.initialize()
    
    # Set the global service for the dependency function
    from tts_service.api.dependencies import _tts_service as tts_service_singleton
    tts_service_singleton = tts_service
    
    logger.info("Application startup complete")
    
    # Application running context
    yield
    
    # Shutdown logic
    logger.info("Application shutting down")


# Create FastAPI application
app = FastAPI(
    title="Peri TTS Service",
    description="Text-to-Speech service for the Peri morning routine assistant",
    version="0.1.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
    # Ensure URLs work with or without trailing slashes
    redirect_slashes=True,
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add request logger middleware
app.add_middleware(RequestLoggerMiddleware)


# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions.
    
    Args:
        request: Request object
        exc: HTTP exception
        
    Returns:
        JSON response
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "request_id": getattr(request.state, "request_id", None),
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions.
    
    This function catches all unhandled exceptions in the application and returns a standardized
    JSON response with a 500 status code. It also logs the exception for further investigation.
    
    Args:
        request: The FastAPI Request object
        exc: The exception that was raised
        
    Returns:
        A JSONResponse with error details
    """
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "request_id": getattr(request.state, "request_id", None),
            }
        }
    )


# Check for model files
def check_model_files() -> bool:
    """Check if model files exist.
    
    Returns:
        True if model files exist, False otherwise
    """
    model_type = "int8" if not settings.KOKORO_SETTINGS["use_gpu"] else "fp16" 
    model_file = Path(settings.MODEL_DIR) / f"kokoro-v1.0{'.fp16' if model_type == 'fp16' else '.int8' if model_type == 'int8' else ''}.onnx"
    voices_file = Path(settings.VOICES_DIR) / "voices-v1.0.bin"
    
    return model_file.exists() and voices_file.exists()


# Startup and shutdown events are now handled by the lifespan context manager


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Run application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
