# Error Handling and Logging Standards

This document defines the standards for error handling and logging in the Peri TTS Python services. Following these standards ensures a consistent approach to dealing with errors and producing useful logs for debugging and monitoring.

## Error Handling Principles

### Core Principles

1. **Be explicit about errors**: Define custom exceptions that clearly communicate what went wrong
2. **Fail early**: Validate inputs at the boundary and fail before performing operations
3. **Provide context**: Include relevant information in exceptions
4. **Handle errors at the appropriate level**: Catch exceptions where they can be meaningfully handled
5. **Never silently swallow exceptions**: Always log or rethrow exceptions

### Error Categories

Errors in the Peri TTS services fall into these categories:

1. **Validation Errors**: Invalid input or request format
2. **Resource Errors**: Missing or unavailable resources (models, voices)
3. **Service Errors**: Failures in external services or dependencies
4. **Internal Errors**: Unexpected failures in the application logic
5. **Configuration Errors**: Invalid or missing configuration

## Exception Hierarchy

The Peri TTS services use a structured exception hierarchy:

```python
# Base exception for all TTS service errors
class TTSError(Exception):
    """Base exception for all TTS service errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


# Validation errors
class ValidationError(TTSError):
    """Raised when input validation fails."""
    pass


class InvalidTextError(ValidationError):
    """Raised when the input text is invalid."""
    pass


class InvalidOptionsError(ValidationError):
    """Raised when TTS options are invalid."""
    pass


# Resource errors
class ResourceError(TTSError):
    """Raised when a required resource is unavailable."""
    pass


class ModelNotFoundError(ResourceError):
    """Raised when a TTS model cannot be found."""
    pass


class VoiceNotFoundError(ResourceError):
    """Raised when a voice cannot be found."""
    pass


# Service errors
class ServiceError(TTSError):
    """Raised when a service dependency fails."""
    pass


class ModelLoadError(ServiceError):
    """Raised when loading a model fails."""
    pass


class GenerationFailedError(ServiceError):
    """Raised when speech generation fails."""
    pass


# Internal errors
class InternalError(TTSError):
    """Raised when an unexpected internal error occurs."""
    pass


# Configuration errors
class ConfigurationError(TTSError):
    """Raised when there is an issue with configuration."""
    pass
```

## Error Handling Patterns

### Function-Level Error Handling

Functions should document the exceptions they can raise and handle errors appropriately:

```python
async def get_voice(self, voice_id: str) -> Voice:
    """
    Get a voice by its ID.
    
    Args:
        voice_id: The ID of the voice to retrieve
        
    Returns:
        The voice with the specified ID
        
    Raises:
        VoiceNotFoundError: If no voice with the specified ID is found
    """
    try:
        voice = next((v for v in self._voices if v.id == voice_id), None)
        if not voice:
            raise VoiceNotFoundError(f"Voice '{voice_id}' not found")
        return voice
    except Exception as e:
        # Unexpected error, wrap in InternalError for consistent handling
        if not isinstance(e, TTSError):
            self._logger.exception(f"Unexpected error retrieving voice {voice_id}")
            raise InternalError(f"Unexpected error retrieving voice: {str(e)}") from e
        raise
```

### API Endpoint Error Handling

API endpoints should convert exceptions to appropriate HTTP responses:

```python
@router.post("/tts", response_class=StreamingResponse)
async def generate_speech(
    request: TTSRequest,
    background_tasks: BackgroundTasks,
    tts_service: TTSService = Depends(get_tts_service),
) -> StreamingResponse:
    """Generate speech from text."""
    try:
        # Validate request
        if not request.text:
            raise ValidationError("Text cannot be empty")
            
        # Generate speech
        result = await tts_service.generate_speech(
            text=request.text,
            voice_id=request.voice,
            options=request.options
        )
        
        # Return audio
        return StreamingResponse(
            content=io.BytesIO(result.audio_data),
            media_type="audio/wav",
            headers={"X-Audio-Duration": str(result.duration_ms)}
        )
        
    except ValidationError as e:
        # 400 Bad Request
        raise HTTPException(status_code=400, detail=e.message)
        
    except VoiceNotFoundError as e:
        # 404 Not Found
        raise HTTPException(status_code=404, detail=e.message)
        
    except (ModelNotFoundError, ResourceError) as e:
        # 503 Service Unavailable
        raise HTTPException(status_code=503, detail=e.message)
        
    except ServiceError as e:
        # 500 Internal Server Error
        logger.error(f"Service error: {e.message}", extra=e.details)
        raise HTTPException(status_code=500, detail="Speech generation failed")
        
    except Exception as e:
        # Unexpected error
        logger.exception(f"Unexpected error during speech generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Global Exception Handler

Use a global exception handler for consistent error handling:

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "request_id": request.state.request_id
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "request_id": request.state.request_id
            }
        }
    )
```

## Logging Standards

### Logging Levels

The Peri TTS services use the following logging levels:

| Level | Usage |
|-------|-------|
| CRITICAL | Application failure requiring immediate attention |
| ERROR | Error that prevents a request from being completed |
| WARNING | Potentially problematic situation that doesn't fail a request |
| INFO | Normal operational messages for tracking application flow |
| DEBUG | Detailed information for debugging |

### Structured Logging

All logs should be structured as JSON for easier parsing and analysis:

```python
# Configure structured logging
import logging
import json
from typing import Dict, Any

class JsonFormatter(logging.Formatter):
    """Format logs as JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
            
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
            
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            for key, value in record.extra.items():
                log_data[key] = value
                
        return json.dumps(log_data)
```

### Request Context Logging

Include request context in logs for traceability:

```python
@app.middleware("http")
async def request_middleware(request: Request, call_next) -> Response:
    """Add request ID and logging context for each request."""
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Set up context for structured logging
    context_logger = logging.LoggerAdapter(
        logger,
        {"request_id": request_id, "method": request.method, "path": request.url.path}
    )
    
    context_logger.info(f"Request started: {request.method} {request.url.path}")
    start_time = time.time()
    
    try:
        # Process request
        response = await call_next(request)
        
        # Log completion
        duration_ms = round((time.time() - start_time) * 1000)
        context_logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={"duration_ms": duration_ms, "status_code": response.status_code}
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        # Log exception
        duration_ms = round((time.time() - start_time) * 1000)
        context_logger.exception(
            f"Request failed: {request.method} {request.url.path}",
            extra={"duration_ms": duration_ms, "error": str(e)}
        )
        raise
```

### Log Message Standards

Follow these guidelines for log messages:

1. **Be specific**: Include relevant details about what happened
2. **Be concise**: Keep messages clear and to the point
3. **Use appropriate level**: Match the log level to the significance of the event
4. **Include context**: Add relevant data as extra fields
5. **Be consistent**: Use a consistent message format
6. **Avoid sensitive data**: Never log sensitive information

Example log messages:

```python
# Good log messages
logger.info("Model loaded successfully", extra={"model_id": model_id, "duration_ms": load_time})
logger.error("Failed to generate speech", extra={"voice_id": voice_id, "text_length": len(text)})
logger.debug("Processing text chunk", extra={"chunk_index": i, "chunk_length": len(chunk)})

# Bad log messages (avoid these)
logger.info("Success")  # Too vague
logger.error(f"Error: {str(e)}")  # Just repeats exception without context
logger.debug(f"Text: {text}")  # May contain sensitive user data
```

## Logging Configuration

### Application-Level Configuration

Configure logging at the application level:

```python
import logging
import logging.config
import yaml
import os

def configure_logging() -> None:
    """Configure logging for the application."""
    log_config_path = os.environ.get("LOG_CONFIG_PATH", "config/logging.yaml")
    
    if os.path.exists(log_config_path):
        # Load configuration from file
        with open(log_config_path, "r") as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        # Default configuration
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
    # Create logger for this module
    logger = logging.getLogger("tts_service")
    logger.info("Logging configured")
    
    return logger
```

### Environment-Specific Configuration

Use different logging configurations for different environments:

```yaml
# config/logging.development.yaml
version: 1
formatters:
  standard:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  json:
    class: app.logging.JsonFormatter
handlers:
  console:
    class: logging.StreamHandler
    level: DEBUG
    formatter: standard
    stream: ext://sys.stdout
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: json
    filename: logs/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
loggers:
  tts_service:
    level: DEBUG
    handlers: [console, file]
    propagate: no
root:
  level: INFO
  handlers: [console]
  propagate: no
```

```yaml
# config/logging.production.yaml
version: 1
formatters:
  json:
    class: app.logging.JsonFormatter
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: json
    stream: ext://sys.stdout
loggers:
  tts_service:
    level: INFO
    handlers: [console]
    propagate: no
root:
  level: WARNING
  handlers: [console]
  propagate: no
```

## Error Monitoring and Alerting

### Error Tracking

Integrate with error tracking services:

```python
# Example integration with Sentry
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    environment=os.environ.get("ENVIRONMENT", "development"),
    traces_sample_rate=0.1
)

# Add middleware to FastAPI app
app = FastAPI(...)
app = SentryAsgiMiddleware(app)
```

### Log Aggregation

Configure log shipping to a centralized logging system:

```python
# Example log shipper configuration for logstash
import logging
from logging_handlers import LogstashHandler

logstash_handler = LogstashHandler(
    host=os.environ.get("LOGSTASH_HOST", "localhost"),
    port=int(os.environ.get("LOGSTASH_PORT", 5000)),
    tags=["tts_service", os.environ.get("ENVIRONMENT", "development")]
)

logger = logging.getLogger("tts_service")
logger.addHandler(logstash_handler)
```

## Troubleshooting Best Practices

### Debugging Techniques

1. **Enable debug logging**: Temporarily increase log level to DEBUG
2. **Use correlation IDs**: Trace requests through the system
3. **Inspect log patterns**: Look for patterns preceding errors
4. **Check resource usage**: Monitor CPU, memory, and disk usage
5. **Test in isolation**: Isolate components to identify issues

### Common Error Resolution Steps

1. **API Errors**:
   - Check request payload against schema
   - Verify API key and permissions
   - Check rate limiting status

2. **TTS Generation Errors**:
   - Verify model and voice files exist
   - Check text for unsupported characters
   - Monitor resource usage during generation

3. **Performance Issues**:
   - Check cache hit rates
   - Monitor model loading/unloading
   - Look for memory leaks or excessive allocations

### Debugging Endpoints

Include debugging endpoints in development environments:

```python
@router.get("/debug/status", tags=["Debug"])
async def debug_status() -> Dict[str, Any]:
    """Get detailed service status for debugging."""
    if os.environ.get("ENVIRONMENT", "development") == "production":
        raise HTTPException(status_code=404)
        
    return {
        "service": "tts_service",
        "version": __version__,
        "uptime_seconds": time.time() - START_TIME,
        "python_version": sys.version,
        "loaded_models": [m.name for m in service.get_loaded_models()],
        "available_voices": len(service.get_all_voices()),
        "cache_stats": service.get_cache_stats(),
        "memory_usage_mb": psutil.Process().memory_info().rss / (1024 * 1024)
    }
```

## Log Analysis

### Key Metrics to Track

1. **Error rates**: Track by endpoint, error type, and client
2. **Response times**: Monitor for performance degradation
3. **Resource usage**: Track memory and CPU usage over time
4. **Cache performance**: Monitor hit rates and eviction patterns
5. **Voice/model popularity**: Track which voices and models are used most

### Log Queries

Use these example queries to analyze logs:

```
# Find errors for a specific request
request_id="12345-abcd-67890" AND level="ERROR"

# Find slow requests
level="INFO" AND message=~"Request completed.*" AND duration_ms>1000

# Track model loading performance
message="Model loaded successfully" | stats avg(duration_ms), max(duration_ms) by model_id

# Find top errors
level="ERROR" | stats count() by message | sort -count

# Track voice usage
message="Generating speech" | stats count() by voice_id | sort -count
```

## Error Recovery

### Automatic Recovery Strategies

1. **Circuit Breakers**: Prevent cascading failures
2. **Retry with Backoff**: Automatically retry transient errors
3. **Fallback Mechanisms**: Provide alternative behavior when services fail
4. **Resource Cleanup**: Ensure resources are released properly

Example circuit breaker implementation:

```python
class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        timeout: float = 10.0
    ):
        """Initialize circuit breaker."""
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._timeout = timeout
        self._last_failure_time = 0.0
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = asyncio.Lock()
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection."""
        async with self._lock:
            if self._state == "OPEN":
                # Check if recovery timeout has elapsed
                if time.time() - self._last_failure_time > self._recovery_timeout:
                    logger.info("Circuit half-open, allowing test request")
                    self._state = "HALF_OPEN"
                else:
                    logger.warning("Circuit open, failing fast")
                    raise CircuitOpenError("Circuit breaker is open")
        
        try:
            # Set timeout for the function call
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=self._timeout)
            
            # If successful and in HALF_OPEN, reset circuit
            if self._state == "HALF_OPEN":
                async with self._lock:
                    logger.info("Test request successful, closing circuit")
                    self._state = "CLOSED"
                    self._failure_count = 0
                    
            return result
            
        except Exception as e:
            # Handle failure
            async with self._lock:
                self._last_failure_time = time.time()
                
                if self._state == "CLOSED":
                    self._failure_count += 1
                    logger.warning(
                        f"Circuit breaker failure ({self._failure_count}/{self._failure_threshold})",
                        extra={"error": str(e)}
                    )
                    
                    if self._failure_count >= self._failure_threshold:
                        logger.error("Circuit breaker threshold reached, opening circuit")
                        self._state = "OPEN"
                        
                elif self._state == "HALF_OPEN":
                    logger.error("Test request failed, reopening circuit")
                    self._state = "OPEN"
                    
            raise
```

## Appendix: Error Code Reference

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| 1000 | Generic error | 500 |
| 1100 | Validation error | 400 |
| 1101 | Invalid text | 400 |
| 1102 | Invalid voice | 404 |
| 1103 | Invalid options | 400 |
| 1200 | Resource error | 503 |
| 1201 | Model not found | 503 |
| 1202 | Voice not found | 404 |
| 1300 | Service error | 500 |
| 1301 | Model load error | 500 |
| 1302 | Generation failed | 500 |
| 1400 | Configuration error | 500 |

This comprehensive error handling and logging strategy ensures that the Peri TTS services are robust, maintainable, and easy to troubleshoot.
