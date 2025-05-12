# Peri TTS Service Architecture

This document outlines the architecture for the Python-based TTS services in the Peri project, with a specific focus on the Kokoro TTS implementation. This architecture is designed to support multiple TTS service providers with a unified interface.

## High-Level Architecture

The Peri TTS service follows a layered architecture with the following components:

1. **API Layer**: FastAPI endpoints that handle HTTP requests
2. **Service Layer**: Business logic and service orchestration
3. **Provider Layer**: Specific implementations for different TTS engines
4. **Infrastructure Layer**: Cross-cutting concerns like caching, logging, and monitoring

The architecture is designed to be:

- **Modular**: Each component can be replaced or updated independently
- **Extensible**: New TTS engines can be added with minimal changes
- **Testable**: Components are decoupled for easier testing
- **Scalable**: Services can be scaled independently based on demand

## Component Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                        API Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │   Voices API    │  │    TTS API      │  │   Admin API   │  │
│  └─────────────────┘  └─────────────────┘  └───────────────┘  │
└───────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────────────────────────────────────────┐
│                      Service Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │  Voice Service  │  │   TTS Service   │  │ Admin Service │  │
│  └─────────────────┘  └─────────────────┘  └───────────────┘  │
└───────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────────────────────────────────────────┐
│                      Provider Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │   Kokoro TTS    │  │    Azure TTS    │  │ [Future TTS]  │  │
│  └─────────────────┘  └─────────────────┘  └───────────────┘  │
└───────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │  Cache Manager  │  │  Audio Processor│  │    Logger     │  │
│  └─────────────────┘  └─────────────────┘  └───────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

## Service Interfaces

### TTS Provider Interface

All TTS providers implement a common interface:

```python
class TTSProvider(Protocol):
    """Interface for TTS providers."""
    
    async def get_voices(self) -> List[Voice]:
        """Get available voices."""
        ...
    
    async def generate_speech(self, text: str, voice_id: str, options: Dict[str, Any]) -> AudioResult:
        """Generate speech from text."""
        ...
    
    async def get_languages(self) -> List[Language]:
        """Get supported languages."""
        ...
```

### Core Service Interface

The core TTS service coordinates between providers:

```python
class TTSService:
    """Service for coordinating TTS operations."""
    
    def __init__(self, providers: Dict[str, TTSProvider], cache: CacheManager):
        """Initialize with providers and cache."""
        ...
    
    async def get_all_voices(self) -> Dict[str, List[Voice]]:
        """Get all voices from all providers."""
        ...
    
    async def generate_speech(self, text: str, voice_id: str, 
                              provider_id: Optional[str] = None,
                              options: Optional[Dict[str, Any]] = None) -> AudioResult:
        """Generate speech, automatically selecting provider if not specified."""
        ...
```

## Kokoro TTS Provider Implementation

The Kokoro TTS provider implements the TTSProvider interface:

```python
class KokoroTTSProvider:
    """Kokoro TTS implementation of TTSProvider."""
    
    def __init__(self, model_path: str, voices_dir: str, cache_dir: str):
        """Initialize Kokoro TTS provider."""
        ...
    
    async def load_model(self, lang_code: str) -> None:
        """Load a specific language model."""
        ...
    
    async def get_voices(self) -> List[Voice]:
        """Get available voices for the current model."""
        ...
    
    async def generate_speech(self, text: str, voice_id: str, 
                             options: Dict[str, Any]) -> AudioResult:
        """Generate speech using Kokoro TTS."""
        ...
```

## API Endpoints

The FastAPI application exposes the following endpoints:

- `GET /voices` - List all available voices
- `POST /tts` - Generate speech from text
- `GET /languages` - List available languages
- `GET /providers` - List available TTS providers
- `GET /health` - Service health check

## Data Flow

1. Client submits text to the `/tts` endpoint
2. API layer validates the request
3. Service layer selects the appropriate provider
4. Provider layer generates the speech
5. Audio is processed (format conversion, etc.)
6. Audio is returned to the client

## Caching Strategy

The TTS service includes a multi-level caching strategy:

1. **Request-level cache**: Cache results of identical requests
2. **Content-level cache**: Store generated audio by content hash
3. **Model cache**: Keep frequently used models in memory

## Error Handling

The service implements a comprehensive error handling strategy:

1. **Domain-specific exceptions**: `ModelNotFoundError`, `VoiceNotFoundError`, etc.
2. **Graceful degradation**: Fall back to alternative providers when possible
3. **Informative error responses**: Clear error messages with troubleshooting hints

## Deployment Architecture

The service can be deployed in multiple configurations:

1. **Standalone**: Single instance for development and testing
2. **Horizontally scaled**: Multiple instances behind a load balancer
3. **Microservices**: Each provider as a separate microservice

## Future Extensions

The architecture supports future enhancements:

1. **Additional TTS Providers**: Easy integration of new providers
2. **Voice Customization**: Support for voice adaptation and fine-tuning
3. **Advanced Features**: Speech styling, emphasis, and emotion

## Security Considerations

The service includes several security measures:

1. **Rate limiting**: Prevent abuse through request throttling
2. **Input validation**: Sanitize and validate all input
3. **Authentication**: Optional API key authentication for production

This architecture ensures a flexible, maintainable system that can evolve as the Peri project grows and requirements change.
